"""Phone-call handler for Twilio Media Streams.

Protocol: Twilio POSTs the inbound call to our voice webhook, which returns
TwiML with a <Connect><Stream> element pointing at /twilio/media. Twilio
then opens a WebSocket and streams bidirectional audio as JSON events.

Audio format: Twilio streams **PCMU (G.711 mu-law) 8 kHz mono**. We
decode + resample to 16 kHz L16 for Deepgram, and downsample + mulaw-encode
Cartesia's 16 kHz L16 output for Twilio. See `audio_utils.py`.

Event shape (subset):
  in:  {"event": "connected", "protocol": "Call", "version": "1.0.0"}
       {"event": "start", "streamSid": "MZ...", "start": {"callSid": "CA...",
              "mediaFormat": {"encoding": "audio/x-mulaw", "sampleRate": 8000, "channels": 1}}}
       {"event": "media", "media": {"track": "inbound", "payload": "<base64>"}}
       {"event": "stop"}
  out: {"event": "media", "streamSid": "MZ...", "media": {"payload": "<base64>"}}
"""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import numpy as np
from cartesia import AsyncCartesia
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from fastapi import WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from agent.config import get_settings
from agent.prompts.builder import build_system_prompt
from agent.tools import all_tools_for_business
from audio_utils import (
    downsample_16k_to_8k,
    mulaw_to_pcm16,
    pcm16_to_mulaw,
    upsample_8k_to_16k,
)
from eval.run_eval import TOOL_STUBS, _anthropic_to_openai_tools


# Telnyx's voice pipeline uses 16 kHz L16 end-to-end. We re-use that here.
SAMPLE_RATE_DEEPGRAM = 16000
DEFAULT_VOICE_ID = "a0e99841-438c-4a64-b679-ae5017fd3e96"  # Cartesia "Conversational Female"

INITIAL_GREETING = (
    "Hi, thanks for calling Metiox Solutions. This is the AI assistant. "
    "How can I help you today?"
)


async def handle_twilio_call(call_sid: str, stream_sid: str, websocket: WebSocket) -> None:
    settings = get_settings()

    missing = [
        k for k in ("openai_api_key", "deepgram_api_key", "cartesia_api_key")
        if not getattr(settings, k)
    ]
    if missing:
        return

    system_prompt = await build_system_prompt(business_id="metiox", caller={})
    anthropic_tools = await all_tools_for_business("metiox")
    openai_tools = _anthropic_to_openai_tools(anthropic_tools)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    llm = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        default_headers={
            "HTTP-Referer": "https://assistant.metiox.com",
            "X-Title": "metiox-receptionist",
        },
    )
    dg_client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
    ct_client = AsyncCartesia(api_key=settings.cartesia_api_key)
    voice_id = settings.cartesia_voice_id or DEFAULT_VOICE_ID

    # --- Conversation state ---
    segment_q: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
    is_speaking = asyncio.Event()        # set while TTS audio is being sent
    stop_tts = asyncio.Event()            # set to interrupt current TTS playback
    call_active = asyncio.Event()
    call_active.set()

    async def on_dg_message(result) -> None:
        try:
            channel = getattr(result, "channel", None)
            if not channel:
                return
            alts = getattr(channel, "alternatives", None)
            if not alts:
                return
            text = (alts[0].transcript or "").strip()
            is_final = bool(getattr(result, "is_final", False))
            speech_final = bool(getattr(result, "speech_final", False))
            if text and is_final:
                await segment_q.put(("segment", text))
            if speech_final:
                await segment_q.put(("utterance_end", ""))
        except Exception:
            pass

    async def run_agent_turn(user_text: str) -> str:
        messages.append({"role": "user", "content": user_text})
        agent_text = ""
        tool_made = False
        for _ in range(8):
            try:
                resp = await llm.chat.completions.create(
                    model=settings.openai_model,
                    max_tokens=300,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )
            except Exception:
                return ""
            msg = resp.choices[0].message
            tool_calls = list(msg.tool_calls or [])
            assistant_content = msg.content or ""
            am: dict[str, Any] = {"role": "assistant", "content": assistant_content}
            if tool_calls:
                am["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(am)
            if not tool_calls:
                agent_text = assistant_content.strip()
                break
            tool_made = True
            for tc in tool_calls:
                result = TOOL_STUBS.get(
                    tc.function.name, {"ok": False, "error": "unknown tool"}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
        # Safety net for empty content after a tool call.
        if tool_made and not agent_text:
            try:
                followup = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Please reply out loud now. Tell the caller what "
                            "you just did in one or two short sentences."
                        ),
                    }
                ]
                resp = await llm.chat.completions.create(
                    model=settings.openai_model,
                    max_tokens=200,
                    messages=followup,
                )
                agent_text = (resp.choices[0].message.content or "").strip()
                if agent_text:
                    messages.append({"role": "assistant", "content": agent_text})
            except Exception:
                pass
        return agent_text

    async def turn_orchestrator() -> None:
        buffer = ""
        while call_active.is_set():
            try:
                kind, payload = await asyncio.wait_for(segment_q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if kind == "segment":
                buffer += (" " + payload) if buffer else payload
            elif kind == "utterance_end":
                user_text = buffer.strip()
                buffer = ""
                if not user_text:
                    continue
                try:
                    reply = await run_agent_turn(user_text)
                    if reply:
                        await tts_to_phone(reply)
                except Exception:
                    pass

    async def tts_to_phone(text: str) -> None:
        if not text:
            return
        is_speaking.set()
        stop_tts.clear()
        try:
            async for chunk in await ct_client.tts.bytes(
                model_id="sonic-2",
                transcript=text,
                voice={"mode": "id", "id": voice_id},
                output_format={
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": SAMPLE_RATE_DEEPGRAM,
                },
            ):
                if stop_tts.is_set():
                    break
                if not chunk:
                    continue
                # Cartesia -> 16k L16 -> downsample to 8k -> mulaw -> Twilio
                pcm = np.frombuffer(chunk, dtype=np.int16)
                pcm_8k = downsample_16k_to_8k(pcm)
                mulaw = pcm16_to_mulaw(pcm_8k)
                try:
                    await websocket.send_json(
                        {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": base64.b64encode(mulaw).decode("ascii")},
                        }
                    )
                except Exception:
                    return
        finally:
            is_speaking.clear()

    try:
        async with dg_client.listen.v1.connect(
            model="nova-3",
            language="en",
            encoding="linear16",
            sample_rate=SAMPLE_RATE_DEEPGRAM,
            interim_results=True,
            endpointing=300,
            utterance_end_ms=1000,
            vad_events=True,
            smart_format=True,
        ) as dg_connection:
            dg_connection.on(EventType.MESSAGE, on_dg_message)
            listen_task = asyncio.create_task(dg_connection.start_listening())
            orchestrator_task = asyncio.create_task(turn_orchestrator())

            # Greet the caller as soon as audio is flowing.
            await tts_to_phone(INITIAL_GREETING)

            try:
                while call_active.is_set():
                    msg = await websocket.receive()
                    if msg.get("type") == "websocket.disconnect":
                        break
                    if "text" in msg:
                        try:
                            data = json.loads(msg["text"])
                        except json.JSONDecodeError:
                            continue
                        event = data.get("event")
                        if event == "stop":
                            break
                        if event == "media":
                            media = data.get("media") or {}
                            if media.get("track") not in ("inbound", None):
                                continue
                            payload = media.get("payload") or media.get("chunk") or ""
                            if not payload:
                                continue
                            try:
                                mulaw = base64.b64decode(payload)
                            except Exception:
                                continue
                            # Twilio mulaw 8k -> linear 8k -> upsample to 16k for Deepgram
                            pcm_8k = mulaw_to_pcm16(mulaw)
                            pcm_16k = upsample_8k_to_16k(pcm_8k)
                            # Barge-in: if the caller starts talking while we're talking,
                            # stop TTS so the next user turn isn't fought over.
                            if is_speaking.is_set():
                                stop_tts.set()
                            try:
                                await dg_connection.send_media(pcm_16k.tobytes())
                            except Exception:
                                break
            except WebSocketDisconnect:
                pass
            finally:
                call_active.clear()
                for t in (listen_task, orchestrator_task):
                    t.cancel()
    except Exception as exc:
        print(f"[twilio] call {call_sid} error: {exc}")


# ---------------------------------------------------------------------------
# TwiML — returned from the /twilio/voice webhook to connect the call to our
# media stream.
# ---------------------------------------------------------------------------

def build_twiml(public_base_url: str) -> str:
    """Return TwiML that connects the call to a bidirectional media stream.

    `public_base_url` should be the scheme://host the call is reaching us on,
    e.g. `https://assistant.metiox.com`. We wss:// the host and point Twilio
    at our /twilio/media endpoint.
    """
    ws_scheme = "wss" if public_base_url.startswith("https://") else "ws"
    host = public_base_url.split("://", 1)[1].rstrip("/")
    stream_url = f"{ws_scheme}://{host}/twilio/media"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        "  <Connect>\n"
        f'    <Stream url="{stream_url}" track="both" />\n'
        "  </Connect>\n"
        "</Response>\n"
    )
