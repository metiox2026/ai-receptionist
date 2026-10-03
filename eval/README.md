# Eval

Text-mode scenario tests. Run with `make eval`.

Each YAML file is a short conversation script with expectations. The runner
plays the caller's lines, watches the LLM's replies + tool use, and reports
pass / fail per scenario.

## Scenario categories

Cover the full range from the plan's Section 13.1:

| Category | Example |
|---|---|
| FAQ | `faq_hours.yaml` |
| Booking | `booking_basic.yaml` |
| Messages | `message_taking.yaml` |
| Escalation | `escalation_angry.yaml`, `transfer_request.yaml` |
| Edge cases | `edge_silence.yaml` |
| Out of scope | (TODO: prompt-injection scenarios) |
| Language | (TODO: language switch mid-call) |

Add new scenarios whenever a real call surfaces a failure — production
sampling is the best source of new tests.

## Writing a scenario

```yaml
name: <short_id>
description: >
  Plain-English description of what the scenario tests.
turns:
  - role: caller
    text: "..."
    expect:
      - agent_uses_tool: <tool_name>
      - agent_response_includes_one_of: ["yes", "sure"]
      - agent_response_length_max_words: 25
```

Available `expect` prefixes:

- `agent_uses_tool: <name>` — the named tool must be called somewhere.
- `agent_uses_no_tool` — no tool calls are allowed in this turn.
- `agent_eventually_uses_tool: <name>` — must be called by the end of the call.
- `agent_response_includes_one_of: [a, b]` — agent reply must contain one of the strings (case-insensitive).
- `agent_response_length_max_words: <n>` — keep it short.
- `agent_offer_take_message` — caller's last chance — agent should offer to take a message.

## Baseline

Run `make eval-baseline` after the prompt stabilises. Later runs fail if
metrics regress beyond the baseline.