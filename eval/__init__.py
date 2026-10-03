"""Scenario-based regression eval.

Run with: `make eval`.

The runner loads the prompt + tools, replays each scenario against the LLM
with stubbed tools, and scores against expected behaviour. Failures fail
the build so prompt or model changes cannot ship without re-validation.
"""