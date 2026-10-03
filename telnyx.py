"""Phone-call handler for Telnyx media streaming.

When Telnyx receives a call on a number assigned to our TeXML Application, it:

  1. POSTs to /telnyx/voice, which returns TeXML with a <Stream> element.
  2. Opens a WebSocket to /telnyx/media and streams bidirectional audio.

`handle_telnyx_call` runs the same Deepgram -> LLM -> Cartesia pipeline as the
browser demo, but speaks to a phone instead. Barge-in (caller interrupts the
agent) is handled by setting `stop_tts` whenever a new inbound audio frame
arrives while the agent is still talking.

Audio format throughout: L16 (linear PCM, signed 16-bit), 16 kHz, mono.
That's what Telnyx streams when `mediaFormat="L16" sampleRate="16000"`,
what Deepgram takes directly with `encoding="linear16" sample_rate=16000`,
and what Cartesia can output via `output_format.sample_rate=16000` — so we
never resample.

Telnyx protocol: control events are JSON over the same WebSocket. Audio
chunks are base64-encoded inside the JSON `chunk` field. The first event
we receive is `{"event": "connected", "version": "1.0.0"}` followed by
`{"event": "start", "stream_url": "...", "call_control_id": "..."}`.
"""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

from cartesia import AsyncCartesia
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from fastapi import WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from agent.config import get_settings
from agent.prompts.builder import build_system_prompt
from agent.tools import all_tools_for_business
from eval.run_eval import TOOL_STUBS, _anthropic_to_openai_tools


# --- Audio format: L16 16kHz mono ---
SAMPLE_RATE = 16000
DEFAULT_VOICE_ID = "a0e99841-438c-4a64-b679-ae5017fd3e96"  # Cartesia "Conversational Female"

# Spoken the moment the call connects, before any inbound audio.
INITIAL_GREETING = (
    "Hi, thanks for calling Metiox Solutions. This is the AI assistant. "
    "How can I help you today?"
)


async def handle_telnyx_call(call_control_id: str, websocket: WebSocket) -> None:
    """Run one phone call to completion. Returns when the call ends."""
    settings = get_settings()

    missing = [
        k for k in ("openai_api_key", "deepgram_api_key", "cartesia_api_key")
        if not getattr(settings, k)
    ]
    if missing:
        # The webhook already validated this, but be defensive in case the
        # call is in-flight when the container restarts with bad config.
        return

    # --- Build prompt + tools (same as the browser path) ---
    system_prompt = await build_system_prompt(business_id="metiox", caller={})
    anthropic_tools = await all_tools_for_business("metiox")
    openai_tools = _anthropic_to_openai_tools(anthropic_tools)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # --- Clients ---
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

    # --- Deepgram callback ---
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

    # --- LLM turn (mirrors demo_server.run_agent_turn) ---
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
                args: dict = {}
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    pass
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
        # Safety net: if the model returned no text after a tool call, ask
        # once more for a spoken reply so the caller never hears silence.
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

    # --- Orchestrator: collect segments, fire agent turns on speech_final ---
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

    # --- TTS: stream Cartesia chunks back to Telnyx as base64 PCM ---
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
                    "sample_rate": SAMPLE_RATE,
                },
            ):
                if stop_tts.is_set():
                    break
                if not chunk:
                    continue
                try:
                    await websocket.send_json(
                        {
                            "event": "media",
                            "track": "outbound",
                            "chunk": base64.b64encode(chunk).decode("ascii"),
                        }
                    )
                except Exception:
                    return
        finally:
            is_speaking.clear()

    # --- Open Deepgram live + main receive loop ---
    try:
        async with dg_client.listen.v1.connect(
            model="nova-3",
            language="en",
            encoding="linear16",
            sample_rate=SAMPLE_RATE,
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
                        if event == "media" and data.get("track") == "inbound":
                            chunk_b64 = data.get("chunk", "")
                            if not chunk_b64:
                                continue
                            try:
                                pcm = base64.b64decode(chunk_b64)
                            except Exception:
                                continue
                            # Barge-in: caller started talking — stop our TTS
                            # so the next user turn isn't fought over.
                            if is_speaking.is_set():
                                stop_tts.set()
                            try:
                                await dg_connection.send_media(pcm)
                            except Exception:
                                break
            except WebSocketDisconnect:
                pass
            finally:
                call_active.clear()
                for t in (listen_task, orchestrator_task):
                    t.cancel()
    except Exception as exc:
        # Don't crash the process on a single bad call.
        print(f"[telnyx] call {call_control_id} error: {exc}")


# ---------------------------------------------------------------------------
# TeXML — returned from the /telnyx/voice webhook to answer the call and
# open the media stream. Telnyx parses this and starts the call flow.
# ---------------------------------------------------------------------------

def build_texml(public_base_url: str) -> str:
    """Return TeXML that answers the call and opens a bidirectional media stream.

    `public_base_url` should be the scheme://host (no path) the call is
    reaching us on, e.g. `https://assistant.metiox.com`.
    """
    ws_scheme = "wss" if public_base_url.startswith("https://") else "ws"
    host = public_base_url.split("://", 1)[1].rstrip("/")
    stream_url = f"{ws_scheme}://{host}/telnyx/media"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        "  <Answer>\n"
        '    <Stream bidirectional="true" mediaFormat="L16" '
        f'sampleRate="16000" url="{stream_url}" />\n'
        "  </Answer>\n"
        "</Response>\n"
    )
