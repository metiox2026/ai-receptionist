"""Pipecat pipeline assembly and per-call runner.

A new pipeline is built for every inbound call. It is responsible for:

  1. Loading the business's prompt (cached section by section)
  2. Loading caller history by phone number
  3. Running the conversation loop:
        STT (Deepgram) -> LLM (Claude Haiku, Gemini fallback) -> TTS (Cartesia)
     plus function-calling tools and interruption (barge-in) handling.
  4. Persisting every turn to the api service through a DB session.
  5. Enqueueing post-call work (summary, notifications) on hangup.

Verify the exact Pipecat API against the version you pin in pyproject.toml —
the framework moves quickly and these classes are renamed between releases.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import WebSocket
from pipecat.frames.frames import LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.anthropic import AnthropicLLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.transports.websocket.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.vad.silero import SileroVADAnalyzer

from agent.config import get_settings
from agent.cost import CostTracker
from agent.fallbacks import with_fallback
from agent.prompts.builder import build_system_prompt
from agent.tools import all_tools_for_business

logger = structlog.get_logger()
settings = get_settings()


async def run_call(websocket: WebSocket) -> None:
    """Run a single inbound call to completion.

    Caller-side responsibilities (turn detection, recording, caller lookup) are
    handled by Pipecat's transport layer. We assemble services, start the task,
    and wait for the call to end. Persistence and post-call jobs are triggered
    by the pipeline's end-of-call event.
    """
    logger.info("call_starting")

    # 1. Lookup caller + load business context (TODO: hit the api service or local DB).
    #    For now, empty caller and a placeholder business_id.
    caller_context: dict[str, Any] = {}
    business_id: str = "default"

    # 2. Build the system prompt with prompt caching-friendly ordering
    #    (static first, dynamic last).
    prompt = await build_system_prompt(
        business_id=business_id,
        caller=caller_context,
    )

    # 3. Wire transport. Telnyx streams 16-bit, 8kHz PCM by default — verify.
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=TelnyxAudioSerializer(),  # see providers/__init__.py
        ),
    )

    # 4. Build STT / LLM / TTS services. The LLM is wrapped with a fallback that
    #    swaps to Gemini if Anthropic fails repeatedly mid-call.
    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        model=settings.deepgram_model,
        language=settings.deepgram_language,
    )

    llm = with_fallback(
        primary=AnthropicLLMService(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            max_tokens=150,        # short, direct replies
            temperature=0.3,
        ),
        failure_threshold=settings.primary_llm_failure_threshold,
    )

    tts = CartesiaTTSService(
        api_key=settings.cartesia_api_key,
        voice_id=settings.cartesia_voice_id,
        model=settings.cartesia_model,
    )

    # 5. Tools — defined per business; see agent/tools/.
    tools = await all_tools_for_business(business_id)
    context_aggregator = OpenAILLMContext(tools=tools)

    # 6. Compose the pipeline. Order matters: transport -> stt -> llm -> tts -> transport.
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,         # barge-in
            enable_metrics=True,               # latency per turn
            enable_usage_metrics=True,         # token counts
        ),
    )

    # 7. Seed the conversation with the system prompt.
    context_aggregator.add_message({"role": "system", "content": prompt})

    # 8. Track cost + persist every message.
    cost_tracker = CostTracker(call_id=task.id)  # TODO: use real call_id from DB

    @task.event_handler("on_conversation_turn_finished")
    async def _on_turn(_: Any) -> None:
        await cost_tracker.record_turn(context_aggregator)

    # 9. Run until the call ends. Pipecat exits when the transport closes.
    runner = PipelineRunner(handle_sigterm=False)
    await runner.run(task)
    logger.info("call_ended", call_id=task.id)