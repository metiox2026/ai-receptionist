"""Single-file web demo for the AI receptionist.

  • Conversation tab — real-time voice chat. Browser captures raw PCM via
    AudioWorklet, sends binary frames over WebSocket. Server streams audio
    to Deepgram for STT, transcripts to Gemini Flash via OpenRouter for the
    reply, text to Cartesia for TTS, audio back to browser for playback.
    Text input fallback included.

  • Eval tab — runs YAML scenarios against Gemini Flash via OpenRouter
    and streams results via Server-Sent Events.

Required API keys (in .env):
  OPENAI_API_KEY    OpenRouter key
  DEEPGRAM_API_KEY  Deepgram STT
  CARTESIA_API_KEY  Cartesia TTS

Open http://localhost:8766 (or your LAN IP) to use.
"""

from __future__ import annotations

import asyncio
import io
import json
import struct
import wave
from typing import Any

from cartesia import AsyncCartesia
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI

from agent.config import get_settings
from agent.prompts.builder import build_system_prompt
from agent.tools import all_tools_for_business
from eval.run_eval import TOOL_STUBS, _anthropic_to_openai_tools
from telnyx import build_texml, handle_telnyx_call


app = FastAPI(title="Receptionist Demo")

PORT = 8766


# ===========================================================================
# Cartesia voice cache — fetched once at module load so first WS isn't slow.
# ===========================================================================

_DEFAULT_VOICE_ID = "a0e99841-438c-4a64-b679-ae5017fd3e96"  # "Conversational Female"
_cartesia_voice_cache: list[dict[str, str]] = []


async def _load_cartesia_voices(api_key: str) -> list[dict[str, str]]:
    if _cartesia_voice_cache:
        return _cartesia_voice_cache
    try:
        client = AsyncCartesia(api_key=api_key)
        voices: list[dict[str, str]] = []
        async for v in await client.voices.list():
            voices.append({"id": v.id, "name": v.name or v.id})
        # Sort alphabetically by name, take first 12 (avoid cluttering UI).
        voices = [v for v in voices if v["name"]][:12]
        _cartesia_voice_cache.extend(voices)
        return voices
    except Exception:
        return []


# ===========================================================================
# Routes — only the chat websocket + landing page. The eval scenarios still
# live in eval/ and can be run from CLI (`python -m eval.run_eval`), but the
# UI is just a single voice chat screen now.
# ===========================================================================

@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


# ===========================================================================
# TELNYX — phone-call webhook + media stream
# ===========================================================================
#
#   1. Telnyx POSTs /telnyx/voice when a call comes in.
#      We return TeXML that <Answer>s the call and opens a <Stream>.
#   2. Telnyx opens a WebSocket to /telnyx/media and streams bidirectional
#      audio (L16 16kHz mono). handle_telnyx_call runs the voice pipeline.
#
# TODO: verify Telnyx's ed25519 signature using TELNYX_PUBLIC_KEY. Skipped for
# now because the URL is HTTPS + URL-token protected, and signature parsing
# varies by Telnyx product. Revisit before exposing the webhook publicly.

@app.post("/telnyx/voice")
async def telnyx_voice_webhook(request: Request) -> Response:
    settings = get_settings()
    # Telnyx sends call info in the body (from, to, call_control_id, ...). We
    # don't need any of it for the simple answer-and-stream flow.
    await request.body()

    # Build the public base URL from the request so it works behind any host
    # (Cloudflare proxy, Dockploy, local ngrok, ...).
    scheme = request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    public_base = f"{scheme}://{host}"

    if not all([settings.openai_api_key, settings.deepgram_api_key, settings.cartesia_api_key]):
        # Misconfigured server — fail loudly so Telnyx retries don't pile up
        # and so the caller hears a proper error instead of silence.
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?>\n'
                    "<Response><Speak>Sorry, the receptionist is unavailable. "
                    "Please try again later.</Speak></Response>\n",
            media_type="application/xml",
        )

    return Response(content=build_texml(public_base), media_type="application/xml")


@app.websocket("/telnyx/media")
async def telnyx_media_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    call_control_id = "unknown"
    try:
        # Telnyx sends {"event": "connected"} first, then {"event": "start",
        # "call_control_id": "..."}. We tolerate either order by reading up
        # to two control messages before kicking off the call handler.
        first = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
        first_event = first.get("event")
        if first_event == "start":
            call_control_id = first.get("call_control_id", call_control_id)
        elif first_event == "connected":
            second = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            if second.get("event") == "start":
                call_control_id = second.get("call_control_id", call_control_id)
        # If we never got a start event, still try — Telnyx sometimes
        # sends media frames directly in test environments.
        await handle_telnyx_call(call_control_id, websocket)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        pass
    except Exception as exc:
        print(f"[telnyx] media ws error: {exc}")


# ===========================================================================
# CONVERSATION — WebSocket voice chat
# ===========================================================================
#
#   Audio path:
#     browser AudioWorklet (PCM int16 48kHz mono)
#       → ws binary frame
#       → Deepgram live (encoding=linear16 sample_rate=48000)
#       → interim / final transcripts
#       → Gemini Flash via OpenRouter (with tool loop)
#       → Cartesia TTS (raw PCM s16le 22kHz)
#       → ws binary frame
#       → browser AudioContext decode + play
#
#   Text path (always available as fallback):
#     browser text input → ws JSON {"type":"text","text":"..."} → LLM directly.

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = get_settings()

    missing = []
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not settings.deepgram_api_key:
        missing.append("DEEPGRAM_API_KEY")
    if not settings.cartesia_api_key:
        missing.append("CARTESIA_API_KEY")
    if missing:
        await websocket.send_json(
            {"type": "error", "message": f"Missing keys: {', '.join(missing)}"}
        )
        await websocket.close()
        return

    # Cartesia voice catalog
    voices = await _load_cartesia_voices(settings.cartesia_api_key)
    default_voice_id = (
        voices[0]["id"] if voices else _DEFAULT_VOICE_ID
    )

    await websocket.send_json(
        {
            "type": "ready",
            "model": settings.openai_model,
            "voices": voices,
            "default_voice": default_voice_id,
        }
    )

    # ----- Gemini / OpenRouter -----
    llm = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/receptionist-demo",
            "X-Title": "receptionist-demo",
        },
    )
    system_prompt = await build_system_prompt(business_id="metiox", caller={})
    anthropic_tools = await all_tools_for_business("metiox")
    openai_tools = _anthropic_to_openai_tools(anthropic_tools)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # ----- Deepgram live connection -----
    # Concurrent queue for transcripts produced from inside the callback.
    transcript_q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    utterance_evt = asyncio.Event()  # set when Deepgram says speech_final

    dg_client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

    async def on_dg_message(result):
        # async may receive ListenV1Results / ListenV1UtteranceEnd / SpeechStarted etc.
        # All have a `.type` discriminator added by the SDK.
        try:
            msg_type = getattr(result, "type", None)
            if msg_type in ("Results", "ListenV1Results", None):
                alts = None
                channel = getattr(result, "channel", None)
                if channel is not None:
                    alts = getattr(channel, "alternatives", None)
                if not alts:
                    return
                text = (alts[0].transcript or "").strip()
                is_final = bool(getattr(result, "is_final", False))
                speech_final = bool(getattr(result, "speech_final", False))
                if text:
                    # Show the user their transcript in real time.
                    await websocket.send_json(
                        {
                            "type": "interim" if not is_final else "user_text",
                            "text": text,
                            "final": is_final,
                        }
                    )
                    if is_final:
                        # Accumulate this segment; orchestrator will concatenate.
                        await segment_q.put(("segment", text))
                if speech_final:
                    await segment_q.put(("utterance_end", ""))
            elif msg_type in ("UtteranceEnd", "ListenV1UtteranceEnd"):
                # Fallback in case the SDK splits this from the Results event.
                await segment_q.put(("utterance_end", ""))
        except Exception:
            pass

    async def turn_orchestrator():
        """Wait for Deepgram's utterance_end, then run one agent turn.

        Survives errors — one failed turn does not kill the conversation.
        """
        buffer = ""
        try:
            while True:
                kind, payload = await segment_q.get()
                if kind == "segment":
                    buffer += (" " + payload) if buffer else payload
                elif kind == "utterance_end":
                    user_text = buffer.strip()
                    buffer = ""
                    if not user_text:
                        continue
                    try:
                        reply = await run_agent_turn(user_text)
                        await tts_to_browser(reply)
                    except WebSocketDisconnect:
                        return
                    except Exception as exc:
                        try:
                            await websocket.send_json(
                                {"type": "error", "message": f"Turn failed: {exc}"}
                            )
                        except Exception:
                            return
                    try:
                        await websocket.send_json({"type": "turn_done"})
                    except Exception:
                        return
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    # ----- Cartesia -----
    ct_client = AsyncCartesia(api_key=settings.cartesia_api_key)
    current_voice_id = default_voice_id

    # ----- Segment queue + turn orchestrator -----
    # Deepgram emits many `is_final=True` segments per utterance (one per
    # pause/re-spoke chunk) and ONE with `speech_final=True` at the end. We
    # accumulate the segments and only fire the agent turn when speech_final
    # arrives, so the LLM sees the whole sentence — not just the last word.
    segment_q: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    # ----- Helper: run LLM + tool loop, return agent_text -----
    async def run_agent_turn(user_text: str) -> str:
        messages.append({"role": "user", "content": user_text})
        safety = 0
        agent_text = ""
        tool_call_made = False
        while safety < 8:
            try:
                resp = await llm.chat.completions.create(
                    model=settings.openai_model,
                    max_tokens=300,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": str(exc)[:200]})
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
                await websocket.send_json({"type": "agent_text", "text": agent_text})
                break

            tool_call_made = True
            for tc in tool_calls:
                args: dict = {}
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    pass
                result = TOOL_STUBS.get(
                    tc.function.name, {"ok": False, "error": "unknown tool"}
                )
                await websocket.send_json(
                    {
                        "type": "tool_call",
                        "name": tc.function.name,
                        "args": args,
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            safety += 1

        # Safety net: if the model returned no text after a tool call, ask
        # once more for a spoken confirmation. Prevents the "blank reply"
        # bug where the model thinks the tool result speaks for itself.
        if tool_call_made and not agent_text:
            try:
                followup = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Please reply out loud now. Tell the caller what you "
                            "just did in one or two short sentences."
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
                    await websocket.send_json(
                        {"type": "agent_text", "text": agent_text}
                    )
            except Exception:
                pass

        return agent_text

    # ----- Helper: TTS via Cartesia, stream raw PCM to browser -----
    async def tts_to_browser(text: str):
        if not text:
            return
        try:
            await websocket.send_json({"type": "tts_start"})
            # Cartesia returns an AsyncIterator of bytes chunks.
            async for chunk in await ct_client.tts.bytes(
                model_id="sonic-2",
                transcript=text,
                voice={"mode": "id", "id": current_voice_id},
                output_format={
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 22050,
                },
            ):
                if chunk:
                    await websocket.send_bytes(chunk)
            await websocket.send_json({"type": "tts_end"})
        except Exception as exc:
            await websocket.send_json({"type": "error", "message": f"TTS failed: {exc}"})
            try:
                await websocket.send_json({"type": "tts_end"})
            except Exception:
                pass

    # The Deepgram v1.connect() context manager holds the live WebSocket open
    # for the duration of the `async with` block — so we wrap the whole
    # session in it.
    try:
        async with dg_client.listen.v1.connect(
            model="nova-3",
            language="en",
            encoding="linear16",
            sample_rate=48000,
            interim_results=True,
            endpointing=300,
            utterance_end_ms=1000,
            vad_events=True,
            smart_format=True,
        ) as dg_connection:
            dg_connection.on(EventType.MESSAGE, on_dg_message)
            # start_listening() blocks until the connection closes; run it as
            # a background task alongside our main receive loop.
            listen_task = asyncio.create_task(dg_connection.start_listening())

            orchestrator_task = asyncio.create_task(turn_orchestrator())

            # ----- Main loop -----
            try:
                while True:
                    msg = await websocket.receive()

                    # -- Text path (typed input) --
                    if msg.get("type") == "websocket.receive" and "text" in msg:
                        try:
                            data = json.loads(msg["text"])
                        except json.JSONDecodeError:
                            continue
                        kind = data.get("type")
                        if kind == "text":
                            user_text = (data.get("text") or "").strip()
                            if not user_text:
                                continue
                            await websocket.send_json(
                                {"type": "user_text", "text": user_text, "final": True}
                            )
                            reply = await run_agent_turn(user_text)
                            await tts_to_browser(reply)
                            await websocket.send_json({"type": "turn_done"})
                        elif kind == "set_voice":
                            current_voice_id = data.get("voice_id") or current_voice_id
                            await websocket.send_json(
                                {"type": "voice_set", "voice_id": current_voice_id}
                            )
                        continue

                    # -- Audio path --
                    if msg.get("type") == "websocket.receive" and "bytes" in msg:
                        pcm = msg["bytes"]
                        if not pcm:
                            continue
                        try:
                            await dg_connection.send_media(pcm)
                        except Exception:
                            break
                        continue

                    # -- Client disconnect --
                    if msg.get("type") == "websocket.disconnect":
                        raise WebSocketDisconnect()

            except WebSocketDisconnect:
                pass
            finally:
                orchestrator_task.cancel()
                listen_task.cancel()
                try:
                    await dg_connection.send_finalize()
                except Exception:
                    pass
    except Exception as exc:
        await websocket.send_json(
            {"type": "error", "message": f"Deepgram connect failed: {exc}"}
        )
        try:
            await websocket.close()
        except Exception:
            pass
        return


# ===========================================================================
# HTML page — single voice-chat screen, mobile-first.
# ===========================================================================

HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Metiox Solutions — Receptionist</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0b10">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<style>
  :root {
    --bg: #0b0b10;
    --bg-elev: #16161e;
    --bg-elev2: #20202a;
    --fg: #f0f0fa;
    --fg-dim: #8e8ea0;
    --border: #2a2a36;
    --accent: #8b5cf6;
    --accent-dim: #6d3fd4;
    --ok: #22c55e;
    --warn: #f59e0b;
    --err: #ef4444;
    --mono: ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --pad-x: 16px;
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bot: env(safe-area-inset-bottom, 0px);
  }
  @media (min-width: 720px) { :root { --pad-x: 24px; } }

  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body {
    margin: 0; padding: 0;
    background: var(--bg); color: var(--fg);
    font-family: var(--sans);
    font-size: 16px;
    line-height: 1.45;
    min-height: 100vh;
    overscroll-behavior: none;
  }
  body {
    display: flex; flex-direction: column;
    min-height: 100vh;
    min-height: 100dvh;
  }

  /* Header — compact, single line on phone */
  header {
    flex: 0 0 auto;
    padding: calc(var(--safe-top) + 12px) var(--pad-x) 12px;
    background: var(--bg-elev);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
  }
  .brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .brand-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--err); flex-shrink: 0;
    transition: background .2s, box-shadow .2s;
  }
  .brand-dot.live { background: var(--ok); box-shadow: 0 0 8px var(--ok); }
  .brand-text { min-width: 0; }
  .brand-text h1 {
    margin: 0; font-size: 16px; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .brand-text .sub {
    color: var(--fg-dim); font-size: 11px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* Chat area — fills middle, scrolls */
  main {
    flex: 1 1 auto;
    display: flex; flex-direction: column;
    min-height: 0;
    padding: 16px var(--pad-x);
  }
  .chat-log {
    flex: 1 1 auto;
    overflow-y: auto;
    display: flex; flex-direction: column; gap: 10px;
    -webkit-overflow-scrolling: touch;
  }
  .bubble {
    max-width: 88%;
    padding: 10px 14px;
    border-radius: 16px;
    font-size: 15px; line-height: 1.4;
    word-wrap: break-word;
    animation: slidein .18s ease-out;
  }
  @keyframes slidein {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .bubble.user {
    background: var(--accent);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
  }
  .bubble.user.interim {
    background: var(--accent-dim);
    opacity: 0.7;
  }
  .bubble.agent {
    background: var(--bg-elev2);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    border: 1px solid var(--border);
  }
  .bubble.tool {
    background: #1f1814;
    align-self: stretch; max-width: 100%;
    border-left: 3px solid var(--warn);
    border-radius: 6px;
    font-family: var(--mono); font-size: 12px;
    padding: 8px 12px;
  }
  .bubble.tool .tool-name { color: var(--warn); font-weight: 600; }
  .bubble.tool .tool-result { color: var(--fg-dim); margin-top: 4px; word-break: break-all; }
  .bubble.system {
    background: var(--bg-elev);
    color: var(--fg-dim);
    align-self: center;
    font-size: 12px;
    font-style: italic;
    padding: 6px 12px;
  }

  /* Bottom dock: voice controls + text input. Sticky to bottom. */
  .dock {
    flex: 0 0 auto;
    background: var(--bg-elev);
    border-top: 1px solid var(--border);
    padding: 10px var(--pad-x) calc(10px + var(--safe-bot));
  }

  /* Voice row: mic (large), status text, voice select (compact) */
  .voice-row {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 10px;
  }
  button.mic {
    flex: 0 0 auto;
    background: var(--err);
    width: 56px; height: 56px;
    border-radius: 50%;
    border: 0;
    color: white;
    font-size: 22px;
    display: flex; align-items: center; justify-content: center;
    padding: 0;
    cursor: pointer;
    transition: transform .12s, background .12s;
    box-shadow: 0 4px 12px rgba(0,0,0,.3);
  }
  button.mic:active { transform: scale(0.94); }
  button.mic.listening {
    background: var(--accent);
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,.6); }
    50%      { box-shadow: 0 0 0 14px rgba(139,92,246,0); }
  }
  .voice-info {
    flex: 1 1 auto; min-width: 0;
    display: flex; flex-direction: column; gap: 4px;
  }
  .mic-status {
    font-size: 13px; font-weight: 500; color: var(--fg);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .voice-select-wrap {
    display: flex; align-items: center; gap: 6px;
  }
  .voice-select-wrap label {
    color: var(--fg-dim); font-size: 11px;
    text-transform: uppercase; letter-spacing: .05em;
  }
  .voice-select-wrap select {
    flex: 1 1 auto; min-width: 0;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 13px;
    font-family: var(--sans);
  }

  /* Text input row */
  .text-row {
    display: flex; gap: 8px;
    align-items: center;
  }
  .text-row input {
    flex: 1 1 auto; min-width: 0;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    padding: 12px 14px;
    border-radius: 999px;
    font-size: 15px;
    font-family: var(--sans);
    /* Avoid iOS zoom-on-focus: 16px font-size is the threshold */
  }
  .text-row input:focus {
    outline: none;
    border-color: var(--accent);
  }
  .text-row button.send {
    flex: 0 0 auto;
    background: var(--accent);
    color: white;
    border: 0;
    padding: 0;
    width: 44px; height: 44px;
    border-radius: 50%;
    font-size: 18px;
    cursor: pointer;
  }
  .text-row button.send:disabled { opacity: 0.4; }

  /* Diagnostics: small mono text under dock for debugging — tap header to toggle */
  .diag {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--fg-dim);
    text-align: center;
    padding: 4px var(--pad-x) calc(4px + var(--safe-bot));
    background: var(--bg);
    display: none;
  }
  .diag.show { display: block; }
</style>
</head>
<body>

<header onclick="toggleDiag()" title="Tap for diagnostics">
  <div class="brand">
    <div id="status-dot" class="brand-dot"></div>
    <div class="brand-text">
      <h1>Metiox Receptionist</h1>
      <div class="sub"><span id="status-text">Connecting…</span> · <span id="chat-model">—</span></div>
    </div>
  </div>
</header>

<main>
  <div class="chat-log" id="chat-log"></div>
</main>

<div class="dock">
  <div class="voice-row">
    <button id="mic-btn" class="mic" aria-label="Toggle microphone">🎤</button>
    <div class="voice-info">
      <div class="mic-status" id="mic-status">Tap to talk</div>
      <div class="voice-select-wrap">
        <label>Voice</label>
        <select id="voice-select"><option>Loading…</option></select>
      </div>
    </div>
  </div>
  <div class="text-row">
    <input id="text-input" type="text" placeholder="Or type here…" autocomplete="off" autocorrect="off" autocapitalize="off" enterkeyhint="send">
    <button id="send-btn" class="send" onclick="sendText()" aria-label="Send">➤</button>
  </div>
</div>

<div id="diag" class="diag"></div>

<script>
// =================== STATE ===================
let ws = null;
let audioCtx = null;
let mediaStream = null;
let workletNode = null;
let isListening = false;
let workletLoaded = false;
let framesSent = 0;
let lastFrameAt = 0;

const chatLog    = document.getElementById('chat-log');
const textInput  = document.getElementById('text-input');
const sendBtn    = document.getElementById('send-btn');
const micBtn     = document.getElementById('mic-btn');
const micStatus  = document.getElementById('mic-status');
const voiceSelect= document.getElementById('voice-select');
const statusDot  = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const chatModel  = document.getElementById('chat-model');
const diagEl     = document.getElementById('diag');

let currentInterimBubble = null;
let pcmChunks = [];
const pcmSampleRate = 22050;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// =================== WS ===================
function setStatus(state, text) {
  statusDot.classList.toggle('live', state === 'live');
  statusText.textContent = text;
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/chat`);
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => setStatus('live', 'Connected');
  ws.onclose = () => {
    setStatus('dead', 'Disconnected · retrying');
    setTimeout(connectWS, 1500);
  };
  ws.onerror = () => {};
  ws.onmessage = (e) => {
    if (typeof e.data === 'string') handleJSON(JSON.parse(e.data));
    else playPCMChunk(e.data);
  };
}

function handleJSON(msg) {
  switch (msg.type) {
    case 'ready':
      chatModel.textContent = msg.model;
      const voices = msg.voices || [];
      voiceSelect.innerHTML = voices.length
        ? voices.map(v => `<option value="${v.id}">${escapeHtml(v.name)}</option>`).join('')
        : `<option value="${msg.default_voice}">Default voice</option>`;
      if (msg.default_voice) voiceSelect.value = msg.default_voice;
      appendBubble('system', `Ready · ${msg.model}`);
      break;
    case 'interim':
      if (currentInterimBubble) currentInterimBubble.remove();
      if (!msg.text) return;
      currentInterimBubble = appendBubble('user interim', escapeHtml(msg.text));
      break;
    case 'user_text':
      if (currentInterimBubble) { currentInterimBubble.remove(); currentInterimBubble = null; }
      appendBubble('user', escapeHtml(msg.text));
      break;
    case 'agent_text':
      appendBubble('agent', escapeHtml(msg.text));
      break;
    case 'tool_call':
      appendBubble('tool',
        `<span class="tool-name">${escapeHtml(msg.name)}()</span>` +
        `<div>${escapeHtml(JSON.stringify(msg.args))}</div>` +
        `<div class="tool-result">→ ${escapeHtml(JSON.stringify(msg.result))}</div>`);
      break;
    case 'tts_end':
      playQueuedTTS();
      break;
    case 'voice_set':
      appendBubble('system', `Voice changed`);
      break;
    case 'error':
      appendBubble('system', '⚠ ' + msg.message);
      micStatus.textContent = msg.message;
      break;
  }
}

function appendBubble(cls, html) {
  const div = document.createElement('div');
  div.className = `bubble ${cls}`;
  div.innerHTML = html;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

// =================== TEXT INPUT ===================
function sendText() {
  const text = textInput.value.trim();
  if (!text || !ws || ws.readyState !== 1) return;
  ws.send(JSON.stringify({type:'text', text}));
  textInput.value = '';
}
textInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendText(); });

voiceSelect.addEventListener('change', () => {
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify({type:'set_voice', voice_id: voiceSelect.value}));
  }
});

// =================== AUDIO PLAYBACK (TTS) ===================
async function ensureAudioCtx() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') await audioCtx.resume();
  return audioCtx;
}

function playPCMChunk(chunk) {
  pcmChunks.push(chunk);
}

async function playQueuedTTS() {
  if (!pcmChunks.length) return;
  const ctx = await ensureAudioCtx();
  let totalLen = 0;
  for (const c of pcmChunks) totalLen += c.byteLength;
  const all = new Int16Array(totalLen / 2);
  let offset = 0;
  for (const c of pcmChunks) {
    const view = new Int16Array(c);
    all.set(view, offset);
    offset += view.length;
  }
  const float32 = new Float32Array(all.length);
  for (let i = 0; i < all.length; i++) float32[i] = all[i] / 32768;
  const buf = ctx.createBuffer(1, float32.length, pcmSampleRate);
  buf.copyToChannel(float32, 0);
  const src = ctx.createBufferSource();
  src.buffer = buf;
  src.connect(ctx.destination);
  src.start();
  pcmChunks = [];
}

// =================== MIC CAPTURE ===================
async function startListening() {
  if (isListening) return;
  const ctx = await ensureAudioCtx();
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 }
    });
  } catch (err) {
    micStatus.textContent = 'Mic denied: ' + err.message;
    return;
  }

  if (!workletLoaded) {
    const workletCode = `
      class PcmProcessor extends AudioWorkletProcessor {
        process(inputs) {
          const input = inputs[0] && inputs[0][0];
          if (input && input.length) {
            const int16 = new Int16Array(input.length);
            for (let i = 0; i < input.length; i++) {
              const v = Math.max(-1, Math.min(1, input[i]));
              int16[i] = v < 0 ? v * 0x8000 : v * 0x7FFF;
            }
            this.port.postMessage(int16.buffer, [int16.buffer]);
          }
          return true;
        }
      }
      registerProcessor('pcm-processor', PcmProcessor);
    `;
    const blob = new Blob([workletCode], {type: 'application/javascript'});
    await ctx.audioWorklet.addModule(URL.createObjectURL(blob));
    workletLoaded = true;
  }

  const source = ctx.createMediaStreamSource(mediaStream);
  workletNode = new AudioWorkletNode(ctx, 'pcm-processor');
  workletNode.port.onmessage = (e) => {
    framesSent += 1;
    lastFrameAt = Date.now();
    if (ws && ws.readyState === 1) ws.send(e.data);
  };
  source.connect(workletNode);

  isListening = true;
  micBtn.classList.add('listening');
  micStatus.textContent = 'Listening…';
}

function stopListening() {
  if (!isListening) return;
  isListening = false;
  micBtn.classList.remove('listening');
  micStatus.textContent = 'Tap to talk';
  if (workletNode) { try { workletNode.disconnect(); } catch(e){} workletNode = null; }
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
    mediaStream = null;
  }
}

micBtn.addEventListener('click', async () => {
  if (isListening) stopListening();
  else await startListening();
});

// Resume audio context when tab returns / mobile wakes
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible' && isListening) {
    const ctx = await ensureAudioCtx();
    if (ctx.state === 'suspended') await ctx.resume();
  }
});

// Diagnostic overlay: tap the header to show audio/WS stats (for debugging only).
let diagVisible = false;
function toggleDiag() {
  diagVisible = !diagVisible;
  diagEl.classList.toggle('show', diagVisible);
}

setInterval(() => {
  if (isListening && audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  if (diagVisible) {
    const wsState = ws ? ws.readyState : 0;
    diagEl.textContent =
      `WS:${wsState===1?'live':'dead'} · Ctx:${audioCtx?.state||'—'} · ` +
      `Frames:${framesSent}${lastFrameAt ? ` · last:${((Date.now()-lastFrameAt)/1000).toFixed(1)}s ago` : ''}`;
  }
}, 1000);

connectWS();
</script>
</body>
</html>"""


def main() -> None:
    import uvicorn
    print(f"\n  Receptionist demo → http://localhost:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()