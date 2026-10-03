"""Prompt assembly. Static sections are loaded once and cached on the LLM
provider; the dynamic block is rebuilt per call.

The split keeps prompt caching effective and lets the dashboard edit one
section without invalidating the others.
"""