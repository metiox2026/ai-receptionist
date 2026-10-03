"""Pipecat voice agent for the AI receptionist.

The agent receives a media stream from the telephony provider, runs the loop
STT -> LLM -> TTS -> tools, and persists every turn to the database through
the api service.

See docs/architecture.md for the call lifecycle.
"""