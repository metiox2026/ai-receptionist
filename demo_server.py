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
import re
import struct
import wave
from pathlib import Path
from typing import Any

import yaml
from cartesia import AsyncCartesia
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from openai import AsyncOpenAI

from agent.config import get_settings
from agent.prompts.builder import build_system_prompt
from agent.tools import all_tools_for_business
from eval.run_eval import (
    INTER_SCENARIO_PAUSE_SEC,
    TOOL_STUBS,
    _anthropic_to_openai_tools,
    _check_expectation,
    _expect_to_kv,
)


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
# EVAL TAB — streaming scenario runner + HTTP routes
# ===========================================================================

async def stream_scenario(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    openai_tools: list[dict],
    scenario_path: Path,
):
    """Yield SSE events as a scenario plays out."""
    scenario = yaml.safe_load(scenario_path.read_text())
    name = scenario.get("name", scenario_path.stem)
    description = scenario.get("description", "").strip()

    yield {"type": "scenario_meta", "name": name, "description": description}

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    cumulative_tool_calls: list[str] = []
    all_failures: list[str] = []
    last_agent_text = ""

    for turn_idx, turn in enumerate(scenario.get("turns", [])):
        if turn.get("role") != "caller":
            continue
        text = (turn.get("text") or "").strip()
        if not text:
            yield {
                "type": "silence",
                "duration_ms": turn.get("silence_ms", 0),
            }
            continue

        yield {"type": "caller_text", "text": text, "turn": turn_idx}
        messages.append({"role": "user", "content": text})

        safety = 0
        while safety < 8:
            resp = await client.chat.completions.create(
                model=model,
                max_tokens=300,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            tool_calls = list(msg.tool_calls or [])
            assistant_content = msg.content or ""

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
            }
            if tool_calls:
                assistant_msg["tool_calls"] = [
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
            messages.append(assistant_msg)

            if not tool_calls:
                last_agent_text = assistant_content.strip()
                yield {
                    "type": "agent_text",
                    "text": last_agent_text,
                    "turn": turn_idx,
                }
                break

            for tc in tool_calls:
                name_t = tc.function.name
                args: dict = {}
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    pass
                cumulative_tool_calls.append(name_t)
                result = TOOL_STUBS.get(name_t, {"ok": False, "error": "unknown tool"})
                yield {
                    "type": "tool_call",
                    "name": name_t,
                    "args": args,
                    "result": result,
                    "turn": turn_idx,
                }
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            safety += 1

        for expect in turn.get("expect", []):
            key, value = _expect_to_kv(expect)
            passed = _check_expectation(key, value, last_agent_text, cumulative_tool_calls)
            if not passed:
                all_failures.append(
                    f"{key}={value!r} not satisfied "
                    f"(reply: {last_agent_text[:80]!r}, tools: {cumulative_tool_calls})"
                )
            yield {
                "type": "expectation",
                "key": key,
                "value": value,
                "passed": passed,
                "turn": turn_idx,
            }

    yield {
        "type": "scenario_done",
        "name": name,
        "passed": not all_failures,
        "failures": all_failures,
        "tool_calls": cumulative_tool_calls,
    }


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


@app.get("/api/scenarios")
async def list_scenarios() -> dict:
    paths = sorted(Path("eval/scenarios").glob("*.yaml"))
    out = []
    for p in paths:
        s = yaml.safe_load(p.read_text())
        out.append(
            {
                "name": s.get("name", p.stem),
                "description": (s.get("description") or "").strip(),
                "turn_count": sum(
                    1 for t in s.get("turns", []) if t.get("role") == "caller"
                ),
            }
        )
    return {"scenarios": out}


@app.get("/api/run")
async def run_all_stream() -> StreamingResponse:
    return StreamingResponse(
        _run_stream(scenario_filter=None),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/run/{scenario_name}")
async def run_one_stream(scenario_name: str) -> StreamingResponse:
    return StreamingResponse(
        _run_stream(scenario_filter=scenario_name),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _run_stream(scenario_filter: str | None):
    settings = get_settings()
    if not settings.openai_api_key:
        yield f"data: {json.dumps({'type':'error','message':'OPENAI_API_KEY not set'})}\n\n"
        return

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/receptionist-demo",
            "X-Title": "receptionist-demo",
        },
    )

    system_prompt = await build_system_prompt(business_id="eval", caller={})
    anthropic_tools = await all_tools_for_business("eval")
    openai_tools = _anthropic_to_openai_tools(anthropic_tools)

    paths = sorted(Path("eval/scenarios").glob("*.yaml"))
    if scenario_filter:
        paths = [p for p in paths if p.stem == scenario_filter]
        if not paths:
            yield f"data: {json.dumps({'type':'error','message':f'unknown scenario {scenario_filter!r}'})}\n\n"
            return

    yield f"data: {json.dumps({'type':'start','model':settings.openai_model,'total':len(paths)})}\n\n"

    passed = 0
    failed = 0
    for idx, path in enumerate(paths):
        yield f"data: {json.dumps({'type':'scenario_start','name':path.stem})}\n\n"
        scenario_passed = False
        try:
            async for event in stream_scenario(
                client, settings.openai_model, system_prompt, openai_tools, path
            ):
                if event.get("type") == "scenario_done":
                    scenario_passed = event.get("passed", False)
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            err_text = str(exc)
            m = re.search(r"retry in (\d+(?:\.\d+)?)s", err_text, re.IGNORECASE)
            wait_s = int(float(m.group(1))) + 2 if m else 30
            yield f"data: {json.dumps({'type':'scenario_error','name':path.stem,'error':err_text[:200],'retry_in':wait_s})}\n\n"
            if wait_s <= 120:
                await asyncio.sleep(wait_s)
                try:
                    async for event in stream_scenario(
                        client, settings.openai_model, system_prompt, openai_tools, path
                    ):
                        yield f"data: {json.dumps(event)}\n\n"
                        if event.get("type") == "scenario_done":
                            scenario_passed = event.get("passed", False)
                except Exception as exc2:
                    yield f"data: {json.dumps({'type':'scenario_error','name':path.stem,'error':str(exc2)[:200]})}\n\n"

        if scenario_passed:
            passed += 1
        else:
            failed += 1
        if idx < len(paths) - 1 and not scenario_filter:
            await asyncio.sleep(INTER_SCENARIO_PAUSE_SEC)

    yield f"data: {json.dumps({'type':'done','passed':passed,'failed':failed})}\n\n"


# ===========================================================================
# CONVERSATION TAB — WebSocket voice chat
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
# HTML page — tabs for Conversation + Eval
# ===========================================================================

HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Receptionist — Live Demo</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #0b0b10;
    --bg-elev: #1a1a22;
    --bg-elev2: #25252f;
    --fg: #e8e8ee;
    --fg-dim: #9b9ba8;
    --border: #2a2a35;
    --accent: #8b5cf6;
    --accent-dim: #5d3a9e;
    --ok: #22c55e;
    --warn: #f59e0b;
    --err: #ef4444;
    --neutral: #6b7280;
    --mono: ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg);
               font-family: var(--sans); min-height: 100vh; }
  header { padding: 16px 32px; border-bottom: 1px solid var(--border);
           display: flex; align-items: center; justify-content: space-between;
           flex-wrap: wrap; gap: 12px; }
  header h1 { margin: 0; font-size: 20px; font-weight: 600; }
  header .sub { color: var(--fg-dim); font-size: 13px; margin-top: 4px; }
  .controls { display: flex; gap: 12px; align-items: center; }
  button { background: var(--accent); color: white; border: 0; padding: 8px 16px;
           border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;
           transition: opacity .15s, background .15s; }
  button:hover { background: var(--accent-dim); }
  button:disabled { opacity: .5; cursor: not-allowed; }
  button.secondary { background: var(--bg-elev); color: var(--fg);
                     border: 1px solid var(--border); }
  button.secondary:hover { background: var(--border); }
  button.danger { background: var(--err); }
  button.danger:hover { background: #c93a3a; }
  button.mic { background: var(--err); width: 60px; height: 60px; border-radius: 50%;
               font-size: 22px; display: flex; align-items: center; justify-content: center;
               padding: 0; }
  button.mic.listening { animation: pulse 1.5s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
                     50% { box-shadow: 0 0 0 16px rgba(239,68,68,0); } }
  .status { padding: 6px 12px; border-radius: 999px; font-size: 12px;
            background: var(--bg-elev); color: var(--fg-dim); border: 1px solid var(--border); }
  .status.live { background: var(--accent-dim); color: white; border-color: var(--accent); }
  .tabs { display: flex; gap: 4px; padding: 0 32px; border-bottom: 1px solid var(--border);
          background: var(--bg-elev); }
  .tab { padding: 12px 20px; color: var(--fg-dim); cursor: pointer; font-weight: 500;
          border-bottom: 2px solid transparent; transition: all .15s; }
  .tab:hover { color: var(--fg); }
  .tab.active { color: var(--fg); border-bottom-color: var(--accent); }
  main { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* Conversation tab */
  .chat-wrap { display: grid; grid-template-columns: 1fr 320px; gap: 16px;
               height: calc(100vh - 200px); min-height: 500px; }
  @media (max-width: 900px) { .chat-wrap { grid-template-columns: 1fr; } }
  .chat-main { background: var(--bg-elev); border: 1px solid var(--border);
                 border-radius: 8px; display: flex; flex-direction: column; }
  .chat-log { flex: 1; overflow-y: auto; padding: 20px; display: flex;
              flex-direction: column; gap: 12px; }
  .bubble { max-width: 75%; padding: 10px 14px; border-radius: 14px;
            font-size: 14px; line-height: 1.4; word-wrap: break-word;
            animation: slidein .2s ease-out; }
  @keyframes slidein { from { opacity: 0; transform: translateY(4px); }
                       to { opacity: 1; transform: translateY(0); } }
  .bubble.user { background: var(--accent); color: white; align-self: flex-end;
                 border-bottom-right-radius: 4px; }
  .bubble.user.interim { background: var(--accent-dim); opacity: 0.6; }
  .bubble.agent { background: var(--bg-elev2); align-self: flex-start;
                  border-bottom-left-radius: 4px; border: 1px solid var(--border); }
  .bubble.tool { background: #2a2419; align-self: stretch; max-width: 100%;
                 border-left: 3px solid var(--warn); font-family: var(--mono);
                 font-size: 12px; }
  .bubble.tool .tool-name { color: var(--warn); font-weight: 600; }
  .bubble.tool .tool-result { color: var(--fg-dim); margin-top: 4px; }
  .bubble.system { background: var(--bg-elev2); color: var(--fg-dim); align-self: center;
                   font-size: 12px; font-style: italic; }
  .chat-input { display: flex; gap: 8px; padding: 16px; border-top: 1px solid var(--border); }
  .chat-input input { flex: 1; background: var(--bg); color: var(--fg); border: 1px solid var(--border);
                      padding: 10px 14px; border-radius: 6px; font-size: 14px;
                      font-family: var(--sans); }
  .chat-input input:focus { outline: none; border-color: var(--accent); }

  .chat-side { display: flex; flex-direction: column; gap: 16px; }
  .panel { background: var(--bg-elev); border: 1px solid var(--border);
           border-radius: 8px; padding: 16px; }
  .panel h3 { margin: 0 0 12px; font-size: 12px; color: var(--fg-dim);
              text-transform: uppercase; letter-spacing: .05em; }
  .mic-zone { display: flex; flex-direction: column; align-items: center;
              gap: 12px; padding: 16px; }
  .mic-status { font-size: 12px; color: var(--fg-dim); text-align: center; min-height: 18px; }
  .voice-controls { display: flex; gap: 8px; align-items: center; justify-content: center;
                    margin-top: 8px; }
  .voice-controls label { display: flex; align-items: center; gap: 6px;
                          font-size: 12px; color: var(--fg-dim); cursor: pointer; }
  .voice-controls input { cursor: pointer; }
  .voice-controls select { background: var(--bg); color: var(--fg);
                            border: 1px solid var(--border); padding: 4px;
                            border-radius: 4px; font-size: 11px; max-width: 200px; }
  .voice-info { font-size: 11px; color: var(--fg-dim); line-height: 1.5; margin-top: 12px;
                  padding: 10px; background: var(--bg); border-radius: 4px;
                  border: 1px dashed var(--border); }
  .voice-info b { color: var(--accent); }

  /* Eval tab */
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
           margin-bottom: 24px; }
  .stat { background: var(--bg-elev); border: 1px solid var(--border);
          border-radius: 8px; padding: 16px; }
  .stat .label { font-size: 11px; color: var(--fg-dim); text-transform: uppercase;
                 letter-spacing: .05em; margin-bottom: 6px; }
  .stat .value { font-size: 24px; font-weight: 600; font-family: var(--mono); }
  .stat.passed .value { color: var(--ok); }
  .stat.failed .value { color: var(--err); }
  .stat.duration .value { color: var(--accent); }
  .grid { display: grid; gap: 16px; }
  .card { background: var(--bg-elev); border: 1px solid var(--border);
          border-radius: 8px; padding: 16px 20px; transition: border-color .2s; }
  .card.running { border-color: var(--accent); }
  .card.passed { border-color: var(--ok); }
  .card.failed { border-color: var(--err); }
  .card-head { display: flex; align-items: center; justify-content: space-between;
               margin-bottom: 12px; }
  .card-name { font-family: var(--mono); font-size: 14px; font-weight: 600; }
  .badge { padding: 3px 10px; border-radius: 999px; font-size: 11px;
           font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }
  .badge.pending { background: var(--border); color: var(--fg-dim); }
  .badge.running { background: var(--accent-dim); color: white; }
  .badge.passed  { background: var(--ok); color: black; }
  .badge.failed  { background: var(--err); color: white; }
  .description { color: var(--fg-dim); font-size: 13px; margin-bottom: 12px;
                 line-height: 1.4; }
  .transcript { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
  .turn { padding: 8px 12px; border-radius: 6px; font-size: 13px;
          line-height: 1.4; animation: slidein .2s ease-out; }
  .turn.caller { background: #1e1e2e; border-left: 3px solid var(--accent); }
  .turn.caller::before { content: "CALLER"; display: block; font-size: 10px;
                          font-weight: 700; color: var(--accent); margin-bottom: 4px; }
  .turn.agent { background: #1a2e1f; border-left: 3px solid var(--ok); }
  .turn.agent::before { content: "AGENT"; display: block; font-size: 10px;
                         font-weight: 700; color: var(--ok); margin-bottom: 4px; }
  .turn.tool { background: #2a2419; border-left: 3px solid var(--warn);
               font-family: var(--mono); font-size: 12px; }
  .turn.tool::before { content: "TOOL"; display: block; font-size: 10px;
                       font-weight: 700; color: var(--warn); margin-bottom: 4px; }
  .turn.silence { background: #1a1a1a; border-left: 3px solid var(--neutral);
                  font-style: italic; color: var(--fg-dim); font-size: 12px; }
  .tool-args { color: var(--fg-dim); margin-top: 4px; font-size: 11px; }
  .tool-result { color: var(--warn); margin-top: 4px; font-size: 11px; }
  .expectations { margin-top: 12px; padding-top: 12px;
                  border-top: 1px dashed var(--border); display: flex;
                  flex-direction: column; gap: 4px; }
  .expectation { display: flex; align-items: center; gap: 8px;
                 font-family: var(--mono); font-size: 12px; }
  .expectation .icon { width: 14px; }
  .expectation.pass { color: var(--ok); }
  .expectation.fail { color: var(--err); }
  .failures-box { margin-top: 12px; padding: 10px 12px; background: #2a1219;
                  border-left: 3px solid var(--err); border-radius: 4px;
                  font-size: 12px; color: var(--err); }
  .failures-box ul { margin: 4px 0 0; padding-left: 18px; }
  .card-actions { display: flex; gap: 8px; margin-top: 8px; }
  .card-actions button { padding: 4px 10px; font-size: 11px; }
</style>
</head>
<body>
<header>
  <div>
    <h1>AI Phone Receptionist — Live Demo</h1>
    <div class="sub">Pipecat architecture · Deepgram STT · Cartesia TTS · OpenRouter Gemini Flash</div>
  </div>
  <div class="controls">
    <span id="status" class="status">Idle</span>
  </div>
</header>

<div class="tabs">
  <div class="tab active" data-tab="chat">Conversation</div>
  <div class="tab" data-tab="eval">Eval</div>
</div>

<!-- =================== CONVERSATION TAB =================== -->
<main>
<div class="tab-panel active" data-panel="chat">
  <div class="chat-wrap">
    <div class="chat-main">
      <div class="chat-log" id="chat-log"></div>
      <div class="chat-input">
        <input id="text-input" type="text" placeholder="Type a message (or click the mic)..." autocomplete="off">
        <button onclick="sendText()">Send</button>
      </div>
    </div>
    <div class="chat-side">
      <div class="panel">
        <h3>Voice</h3>
        <div class="mic-zone">
          <button id="mic-btn" class="mic" title="Hold to talk">🎤</button>
          <div class="mic-status" id="mic-status">Tap to speak</div>
          <div class="voice-controls">
            <label>Voice:&nbsp;
              <select id="voice-select"></select>
            </label>
          </div>
        </div>
        <div class="voice-info">
          <b>How voice works:</b><br>
          • Browser captures raw PCM via AudioWorklet<br>
          • WebSocket streams audio → <b>Deepgram</b> STT<br>
          • Transcript → <b>Gemini Flash</b> agent<br>
          • Reply → <b>Cartesia</b> TTS → audio plays on your phone<br>
          • Try: "What time do you close?" — "I want to book" — "Speak to a human"
        </div>
      </div>
      <div class="panel">
        <h3>Status</h3>
        <div id="chat-status" style="font-size:12px;color:var(--fg-dim);">Disconnected</div>
        <div style="margin-top:8px;font-size:11px;color:var(--fg-dim);">
          Model: <span id="chat-model" style="font-family:var(--mono);">—</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- =================== EVAL TAB =================== -->
<div class="tab-panel" data-panel="eval">
  <div class="stats">
    <div class="stat passed"><div class="label">Passed</div>
      <div class="value" id="stat-passed">—</div></div>
    <div class="stat failed"><div class="label">Failed</div>
      <div class="value" id="stat-failed">—</div></div>
    <div class="stat duration"><div class="label">Elapsed</div>
      <div class="value" id="stat-elapsed">—</div></div>
    <div class="stat"><div class="label">Model</div>
      <div class="value" id="stat-model" style="font-size:14px;">—</div></div>
  </div>
  <div style="margin-bottom:16px;display:flex;gap:8px;">
    <button onclick="runAll()">▶ Run All</button>
    <button class="secondary" onclick="resetAll()">Reset</button>
  </div>
  <div class="grid" id="scenarios"></div>
</div>
</main>

<script>
const PCM_SAMPLE_RATE_OUT = 44100;

// =================== TAB SWITCHING ===================
document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    document.querySelector(`[data-panel="${t.dataset.tab}"]`).classList.add('active');
    if (t.dataset.tab === 'eval') initEval();
  });
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// =================== CONVERSATION TAB ===================
let ws = null;
let audioCtx = null;
let mediaStream = null;
let workletNode = null;
let isListening = false;
const chatLog = document.getElementById('chat-log');
const textInput = document.getElementById('text-input');
const chatStatus = document.getElementById('chat-status');
const chatModel = document.getElementById('chat-model');
const micBtn = document.getElementById('mic-btn');
const micStatus = document.getElementById('mic-status');
const voiceSelect = document.getElementById('voice-select');

let currentInterimBubble = null;
let lastUserTextBubble = null;
let pendingTtsSource = null;

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/chat`);
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => { chatStatus.textContent = 'Connected'; chatStatus.style.color = 'var(--ok)'; };
  ws.onclose = () => {
    chatStatus.textContent = 'Disconnected'; chatStatus.style.color = 'var(--fg-dim)';
    setTimeout(connectWS, 1500);
  };
  ws.onerror = () => {};
  ws.onmessage = (e) => {
    if (typeof e.data === 'string') {
      handleJSON(JSON.parse(e.data));
    } else {
      // Binary = PCM audio from TTS
      playPCMChunk(e.data);
    }
  };
}

function handleJSON(msg) {
  if (msg.type === 'ready') {
    chatModel.textContent = msg.model;
    appendBubble('system', `Connected · ${msg.model} · Cartesia TTS ready`);
    voiceSelect.innerHTML = (msg.voices || [])
      .map(v => `<option value="${v.id}">${escapeHtml(v.name)}</option>`).join('');
    if (msg.default_voice) voiceSelect.value = msg.default_voice;
    if (!voiceSelect.options.length && msg.default_voice) {
      voiceSelect.innerHTML = `<option value="${msg.default_voice}">Default voice</option>`;
      voiceSelect.value = msg.default_voice;
    }
  } else if (msg.type === 'interim') {
    // Replace previous interim bubble in place
    if (currentInterimBubble) currentInterimBubble.remove();
    if (!msg.text) return;
    currentInterimBubble = appendBubble('user interim', escapeHtml(msg.text));
  } else if (msg.type === 'user_text') {
    if (currentInterimBubble) { currentInterimBubble.remove(); currentInterimBubble = null; }
    lastUserTextBubble = appendBubble('user', escapeHtml(msg.text));
  } else if (msg.type === 'agent_text') {
    appendBubble('agent', escapeHtml(msg.text));
  } else if (msg.type === 'tool_call') {
    appendBubble('tool',
      `<span class="tool-name">${escapeHtml(msg.name)}()</span>` +
      `<div>${escapeHtml(JSON.stringify(msg.args))}</div>` +
      `<div class="tool-result">→ ${escapeHtml(JSON.stringify(msg.result))}</div>`
    );
  } else if (msg.type === 'tts_start') {
    pendingTtsSource = null;  // new playback session
  } else if (msg.type === 'tts_end') {
    pendingTtsSource = null;
  } else if (msg.type === 'turn_done') {
    // noop
  } else if (msg.type === 'voice_set') {
    appendBubble('system', `Voice: ${msg.voice_id}`);
  } else if (msg.type === 'error') {
    appendBubble('system', '⚠ ' + msg.message);
    micStatus.textContent = msg.message;
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

// ----- Audio playback (Cartesia returns raw PCM s16le 22050 Hz) -----
async function ensureAudioCtx() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') await audioCtx.resume();
  return audioCtx;
}

// We queue PCM chunks per utterance, then play as one buffer.
let pcmChunks = [];
let pcmSampleRate = 22050;
function playPCMChunk(chunk) {
  pcmChunks.push(chunk);
  // TTS chunks stream in via tts_start/.../tts_end markers — actual scheduling
  // happens when tts_end arrives.
}

// Playback triggered on tts_end: decode queued chunks and play.
async function playQueuedTTS() {
  if (!pcmChunks.length) return;
  const ctx = await ensureAudioCtx();
  // Concatenate chunks
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
  pendingTtsSource = src;
  pcmChunks = [];
}

// Patch handleJSON to call playQueuedTTS on tts_end.
const _handleJSON = handleJSON;
// Override: wrap tts_end
const origHandle = handleJSON;
function handleJSONWrapped(msg) {
  if (msg.type === 'tts_end') playQueuedTTS();
  origHandle(msg);
}
handleJSON = handleJSONWrapped;

// ----- Mic capture (AudioWorklet → PCM int16 48kHz → ws binary) -----
let workletLoaded = false;
let framesSent = 0;
let lastFrameAt = 0;

async function startListening() {
  if (isListening) return;
  const ctx = await ensureAudioCtx();
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        channelCount: 1,
      }
    });
  } catch (err) {
    micStatus.textContent = 'Mic denied: ' + err.message;
    return;
  }

  // Inline AudioWorklet that converts Float32 → Int16 PCM and posts buffers.
  // Register once per AudioContext — repeated addModule() throws in some browsers.
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
  // Don't connect workletNode to destination — we don't want to hear ourselves.

  isListening = true;
  micBtn.classList.add('listening');
  micStatus.textContent = 'Listening…';
}

function stopListening() {
  if (!isListening) return;
  isListening = false;
  micBtn.classList.remove('listening');
  micStatus.textContent = 'Tap to speak';
  if (workletNode) { try { workletNode.disconnect(); } catch(e){} workletNode = null; }
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
    mediaStream = null;
  }
}

micBtn.addEventListener('click', async () => {
  if (isListening) {
    stopListening();
  } else {
    await startListening();
  }
});

// Self-heal: resume if tab returns to foreground, restart capture if frames stall.
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible' && isListening) {
    const ctx = await ensureAudioCtx();
    if (ctx.state === 'suspended') await ctx.resume();
  }
});

setInterval(() => {
  if (isListening && audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  const ctxEl = document.getElementById('chat-status');
  if (!ctxEl) return;
  const wsState = ws ? ws.readyState : 0;  // 0=CONNECTING 1=OPEN 2=CLOSING 3=CLOSED
  if (isListening) {
    ctxEl.textContent =
      `WS:${wsState===1?'live':'dead'} · Ctx:${audioCtx?.state||'—'} · ` +
      `Frames:${framesSent}${lastFrameAt ? ` · last:${((Date.now()-lastFrameAt)/1000).toFixed(1)}s ago` : ''}`;
    ctxEl.style.color = wsState === 1 ? 'var(--ok)' : 'var(--err)';
  } else {
    ctxEl.textContent = wsState === 1 ? 'Connected' : 'Disconnected';
    ctxEl.style.color = wsState === 1 ? 'var(--ok)' : 'var(--fg-dim)';
  }
}, 1000);

connectWS();

// =================== EVAL TAB ===================
let evalInited = false;
let evalState = {};

async function initEval() {
  if (evalInited) return;
  evalInited = true;
  const resp = await fetch('/api/scenarios');
  const data = await resp.json();
  const container = document.getElementById('scenarios');
  container.innerHTML = '';
  data.scenarios.forEach(s => {
    evalState[s.name] = { status:'pending', turns:[], expectations:[], failures:[], description: s.description };
    const card = document.createElement('div');
    card.className = 'card';
    card.id = `card-${s.name}`;
    card.innerHTML = `
      <div class="card-head">
        <div class="card-name">${s.name}</div>
        <div style="display:flex;gap:8px;align-items:center">
          <button class="secondary" onclick="runOne('${s.name}')">Run</button>
          <span class="badge pending" id="badge-${s.name}">Pending</span>
        </div>
      </div>
      <div class="description">${s.description}</div>
      <div class="transcript" id="transcript-${s.name}"></div>
      <div class="expectations" id="expectations-${s.name}"></div>
      <div id="failures-${s.name}"></div>`;
    container.appendChild(card);
  });
}

function evalAppendTurn(name, html, cls) {
  const t = document.getElementById(`transcript-${name}`);
  const div = document.createElement('div');
  div.className = `turn ${cls}`;
  div.innerHTML = html;
  t.appendChild(div); t.scrollTop = t.scrollHeight;
}

function evalSetBadge(name, status) {
  evalState[name].status = status;
  const badge = document.getElementById(`badge-${name}`);
  badge.className = `badge ${status}`;
  badge.textContent = status;
  const card = document.getElementById(`card-${name}`);
  card.classList.remove('running','passed','failed');
  if (status === 'running') card.classList.add('running');
  if (status === 'passed')  card.classList.add('passed');
  if (status === 'failed')  card.classList.add('failed');
}

function evalRenderExpectation(name, key, value, passed) {
  const container = document.getElementById(`expectations-${name}`);
  const div = document.createElement('div');
  div.className = `expectation ${passed ? 'pass' : 'fail'}`;
  div.innerHTML = `<span class="icon">${passed ? '✓' : '✗'}</span><span>${key}</span><span style="color:var(--fg-dim)">${typeof value === 'object' ? JSON.stringify(value) : value}</span>`;
  container.appendChild(div);
}

function evalRenderFailures(name, failures) {
  if (!failures.length) return;
  const box = document.getElementById(`failures-${name}`);
  box.innerHTML = `<div class="failures-box"><strong>Failures</strong><ul>${failures.map(f => `<li>${escapeHtml(f)}</li>`).join('')}</ul></div>`;
}

let evalActiveSource = null;
let evalStartedAt = null;
let evalElapsedTimer = null;

function evalTickElapsed() {
  if (!evalStartedAt) return;
  const secs = Math.floor((Date.now() - evalStartedAt) / 1000);
  const m = Math.floor(secs / 60).toString().padStart(2,'0');
  const s = (secs % 60).toString().padStart(2,'0');
  document.getElementById('stat-elapsed').textContent = `${m}:${s}`;
}

function evalConsumeStream(url) {
  if (evalActiveSource) { evalActiveSource.close(); evalActiveSource = null; }
  document.getElementById('status').textContent = 'Running';
  document.getElementById('status').classList.add('live');
  evalStartedAt = Date.now();
  evalElapsedTimer = setInterval(evalTickElapsed, 250);
  let passedCount = 0, failedCount = 0;
  evalActiveSource = new EventSource(url);
  evalActiveSource.onmessage = (e) => {
    const evt = JSON.parse(e.data);
    if (evt.type === 'start') {
      document.getElementById('stat-model').textContent = evt.model || '';
    } else if (evt.type === 'scenario_start') {
      evalSetBadge(evt.name, 'running');
    } else if (evt.type === 'caller_text') {
      evalAppendTurn(evt.name, escapeHtml(evt.text), 'caller');
    } else if (evt.type === 'agent_text') {
      evalAppendTurn(evt.name, escapeHtml(evt.text), 'agent');
    } else if (evt.type === 'tool_call') {
      const argsHtml = Object.keys(evt.args).length
        ? `<div class="tool-args">${escapeHtml(JSON.stringify(evt.args))}</div>` : '';
      const resHtml = `<div class="tool-result">→ ${escapeHtml(JSON.stringify(evt.result))}</div>`;
      evalAppendTurn(evt.name, `<strong>${escapeHtml(evt.name)}()</strong>${argsHtml}${resHtml}`, 'tool');
    } else if (evt.type === 'silence') {
      evalAppendTurn(evt.name, `silence ${evt.duration_ms}ms`, 'silence');
    } else if (evt.type === 'expectation') {
      evalRenderExpectation(evt.name, evt.key, evt.value, evt.passed);
    } else if (evt.type === 'scenario_done') {
      evalSetBadge(evt.name, evt.passed ? 'passed' : 'failed');
      evalRenderFailures(evt.name, evt.failures);
      if (evt.passed) passedCount++; else failedCount++;
      document.getElementById('stat-passed').textContent = passedCount;
      document.getElementById('stat-failed').textContent = failedCount;
    } else if (evt.type === 'scenario_error') {
      evalSetBadge(evt.name, 'failed');
      evalRenderFailures(evt.name, [evt.error]);
      failedCount++;
      document.getElementById('stat-failed').textContent = failedCount;
    } else if (evt.type === 'done') {
      document.getElementById('stat-passed').textContent = evt.passed;
      document.getElementById('stat-failed').textContent = evt.failed;
      evalFinishRun();
    } else if (evt.type === 'error') {
      alert(evt.message); evalFinishRun();
    }
  };
  evalActiveSource.onerror = () => evalFinishRun();
}

function evalFinishRun() {
  if (evalActiveSource) { evalActiveSource.close(); evalActiveSource = null; }
  document.getElementById('status').textContent = 'Idle';
  document.getElementById('status').classList.remove('live');
  if (evalElapsedTimer) { clearInterval(evalElapsedTimer); evalElapsedTimer = null; }
}

function runAll() {
  document.getElementById('stat-passed').textContent = '—';
  document.getElementById('stat-failed').textContent = '—';
  document.getElementById('stat-elapsed').textContent = '00:00';
  Object.keys(evalState).forEach(n => {
    evalSetBadge(n, 'pending');
    document.getElementById(`transcript-${n}`).innerHTML = '';
    document.getElementById(`expectations-${n}`).innerHTML = '';
    document.getElementById(`failures-${n}`).innerHTML = '';
  });
  evalConsumeStream('/api/run');
}

function runOne(name) {
  evalSetBadge(name, 'pending');
  document.getElementById(`transcript-${name}`).innerHTML = '';
  document.getElementById(`expectations-${name}`).innerHTML = '';
  document.getElementById(`failures-${name}`).innerHTML = '';
  evalConsumeStream(`/api/run/${name}`);
}

function resetAll() {
  Object.keys(evalState).forEach(n => {
    evalSetBadge(n, 'pending');
    document.getElementById(`transcript-${n}`).innerHTML = '';
    document.getElementById(`expectations-${n}`).innerHTML = '';
    document.getElementById(`failures-${n}`).innerHTML = '';
  });
  document.getElementById('stat-passed').textContent = '—';
  document.getElementById('stat-failed').textContent = '—';
  document.getElementById('stat-elapsed').textContent = '—';
  if (evalActiveSource) { evalActiveSource.close(); evalActiveSource = null; }
  document.getElementById('status').textContent = 'Idle';
  document.getElementById('status').classList.remove('live');
}
</script>
</body>
</html>"""


def main() -> None:
    import uvicorn
    print(f"\n  Receptionist demo → http://localhost:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()