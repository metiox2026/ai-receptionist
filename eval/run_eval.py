"""Text-mode scenario runner — OpenRouter edition.

Replays each YAML scenario against an OpenAI-compatible model via
OpenRouter. Reports pass / fail per scenario and per metric. With
--save-baseline, writes a JSON file so future runs can compare.

Run: `python -m eval.run_eval --suite eval/scenarios [--baseline <baseline-json>]`

OpenRouter is OpenAI-API-compatible: we use the openai SDK pointed at
https://openrouter.ai/api/v1. The Anthropic-style tool specs in the project
are translated to OpenAI's `{type:"function", function:{...}}` shape, and
we manage the full message history ourselves (the OpenAI chat completions
API is stateless, unlike Gemini's chat sessions).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from openai import AsyncOpenAI


# Stubs — pretend the agent is calling real tools. Always succeed.
TOOL_STUBS: dict[str, Any] = {
    "check_availability": {"ok": True, "slots": ["10:00", "11:00", "14:00"]},
    "book_appointment": {"ok": True, "appointment_id": "stub-123"},
    "take_message": {"ok": True, "message_id": "stub-msg"},
    "transfer_call": {"ok": True, "transferred_to": "main_line"},
    "end_call": {"ok": True},
    "search_knowledge": {"ok": True, "results": []},
    "log_unanswered": {"ok": True},
    "send_sms": {"ok": True},
}


# Pause between scenarios for free-tier politeness.
INTER_SCENARIO_PAUSE_SEC = 5


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool-spec translation: Anthropic format -> OpenAI function shape
# ---------------------------------------------------------------------------

def _anthropic_to_openai_tools(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool specs into OpenAI's function shape."""
    out_tools: list[dict] = []
    for t in anthropic_tools:
        params = dict(t.get("parameters") or {})
        params.pop("$schema", None)
        params.pop("additionalProperties", None)
        if "type" not in params:
            params["type"] = "object"
        out_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": params,
                },
            }
        )
    return out_tools


# ---------------------------------------------------------------------------
# Expectation checker — handles both string and dict formats
# ---------------------------------------------------------------------------

def _parse_value(value: Any) -> list[str] | str:
    if isinstance(value, list):
        return [str(v).strip().strip("\"'") for v in value]
    if isinstance(value, str):
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            return [
                tok.strip().strip("\"'")
                for tok in inner.split(",")
                if tok.strip()
            ]
        return value
    return str(value)


def _check_expectation(
    key: str, value: Any, agent_text: str, tool_calls: list[str]
) -> bool:
    parsed = _parse_value(value)
    text = agent_text.lower()

    if key == "agent_uses_tool":
        return parsed in tool_calls
    if key == "agent_uses_no_tool":
        return not tool_calls
    if key == "agent_eventually_uses_tool":
        return parsed in tool_calls
    if key == "agent_response_includes_one_of":
        opts = [o.lower() for o in (parsed if isinstance(parsed, list) else [parsed])]
        return any(o in text for o in opts)
    if key == "agent_response_includes":
        return parsed.lower() in text
    if key == "agent_response_length_max_words":
        return len(agent_text.split()) <= int(parsed)
    if key == "agent_asks_question_includes":
        return parsed.lower() in text
    if key == "agent_collects":
        items = parsed if isinstance(parsed, list) else [parsed]
        return all(item.lower() in text for item in items)
    if key == "agent_offer_take_message":
        phrases = ["take a message", "leave a message", "have someone call"]
        return any(p in text for p in phrases)
    return True


def _expect_to_kv(expect: Any) -> tuple[str, Any]:
    if isinstance(expect, dict) and expect:
        if len(expect) == 1:
            return next(iter(expect.items()))
        return next(iter(expect.items()))
    if isinstance(expect, str) and ":" in expect:
        key, _, value = expect.partition(":")
        return key.strip(), value.strip()
    return str(expect), ""


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

async def run_scenario(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    openai_tools: list[dict],
    scenario_path: Path,
) -> ScenarioResult:
    scenario = yaml.safe_load(scenario_path.read_text())
    failures: list[str] = []
    cumulative_tool_calls: list[str] = []

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    for turn in scenario.get("turns", []):
        if turn.get("role") != "caller":
            continue
        text = (turn.get("text") or "").strip()
        # Skip empty caller turns — silence markers in YAML.
        if not text:
            continue

        messages.append({"role": "user", "content": text})

        # Loop: respond to chained tool calls until the model produces a final
        # text reply (i.e., a turn without tool_calls).
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

            # Append the assistant turn to history (preserve tool_calls if any).
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": assistant_content}
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
                break  # Final text reply.

            # Send tool results back.
            for tc in tool_calls:
                name = tc.function.name
                cumulative_tool_calls.append(name)
                result = TOOL_STUBS.get(name, {"ok": False, "error": "unknown tool"})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            safety += 1

        agent_text = assistant_content.strip()

        for expect in turn.get("expect", []):
            key, value = _expect_to_kv(expect)
            if not _check_expectation(key, value, agent_text, cumulative_tool_calls):
                failures.append(
                    f"{key}={value!r} not satisfied (reply: {agent_text[:120]!r}, "
                    f"tools: {cumulative_tool_calls})"
                )

    return ScenarioResult(
        name=scenario["name"],
        passed=not failures,
        failures=failures,
        tool_calls=cumulative_tool_calls,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(suite: Path, baseline: Path | None, save_baseline: bool) -> int:
    from agent.config import get_settings

    settings = get_settings()
    api_key = settings.openai_api_key
    base_url = settings.openai_base_url
    model = settings.openai_model
    if not api_key:
        print("OPENAI_API_KEY not set; cannot run.", file=sys.stderr)
        return 2

    # OpenRouter recommends identifying yourself so the request is allowed
    # even on free-tier rate-limited routes.
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/receptionist-demo",
            "X-Title": "receptionist-demo",
        },
    )

    from agent.prompts.builder import build_system_prompt
    from agent.tools import all_tools_for_business

    system_prompt = await build_system_prompt(business_id="eval", caller={})
    anthropic_tools = await all_tools_for_business("eval")
    openai_tools = _anthropic_to_openai_tools(anthropic_tools)

    results: list[ScenarioResult] = []
    scenario_paths = sorted(suite.glob("*.yaml"))
    for idx, path in enumerate(scenario_paths):
        print(f"running {path.name} ...", end=" ", flush=True)
        try:
            result = await run_scenario(
                client, model, system_prompt, openai_tools, path
            )
        except Exception as exc:
            err_text = str(exc)
            if (
                "429" in err_text
                or "RESOURCE_EXHAUSTED" in err_text
                or "503" in err_text
                or "UNAVAILABLE" in err_text
            ):
                m = re.search(r"retry in (\d+(?:\.\d+)?)s", err_text, re.IGNORECASE)
                wait_s = int(float(m.group(1))) + 2 if m else 30
                if wait_s > 120:
                    print(f"QUOTA_EXHAUSTED (retry in {wait_s}s) ...", end=" ", flush=True)
                    result = ScenarioResult(
                        name=path.stem,
                        passed=False,
                        failures=[f"quota exhausted (retry in {wait_s}s)"],
                    )
                else:
                    print(f"RETRY in {wait_s}s ...", end=" ", flush=True)
                    await asyncio.sleep(wait_s)
                    try:
                        result = await run_scenario(
                            client, model, system_prompt, openai_tools, path
                        )
                    except Exception as exc2:
                        print(f"ERROR ({exc2.__class__.__name__}: {exc2})")
                        result = ScenarioResult(
                            name=path.stem,
                            passed=False,
                            failures=[f"runner error: {exc2}"],
                        )
            else:
                print(f"ERROR ({exc.__class__.__name__}: {exc})")
                result = ScenarioResult(
                    name=path.stem,
                    passed=False,
                    failures=[f"runner error: {exc}"],
                )
        results.append(result)
        print("PASS" if result.passed else f"FAIL ({len(result.failures)} issues)")
        for fail in result.failures:
            print(f"  - {fail}")
        if idx < len(scenario_paths) - 1:
            await asyncio.sleep(INTER_SCENARIO_PAUSE_SEC)

    summary = {
        "total": len(results),
        "passed": sum(r.passed for r in results),
        "failed": sum(not r.passed for r in results),
        "scenarios": [r.__dict__ for r in results],
    }
    print(json.dumps(summary, indent=2))

    if save_baseline and baseline is not None:
        baseline.write_text(json.dumps(summary, indent=2))
        print(f"baseline saved to {baseline}")

    return 0 if summary["failed"] == 0 else 1


def cli_entry() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=Path("eval/scenarios"))
    parser.add_argument("--baseline", type=Path, default=Path("eval/baseline.json"))
    parser.add_argument("--save-baseline", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.suite, args.baseline, args.save_baseline)))


if __name__ == "__main__":
    cli_entry()