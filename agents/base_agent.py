"""
Base Agent
==========
All agents inherit from this. Handles Claude API calls, retries, and JSON parsing.
"""

import json
import os
import re
import time
from typing import Optional
import anthropic


class BaseAgent:
    MODEL = "claude-opus-4-5"
    MAX_TOKENS = 4096

    def __init__(self, name: str):
        self.name = name
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def call(self, system: str, user: str, max_tokens: Optional[int] = None) -> str:
        """Make a Claude API call and return the text response."""
        print(f"  🤖  [{self.name}] thinking...")
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.MODEL,
                    max_tokens=max_tokens or self.MAX_TOKENS,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return response.content[0].text
            except anthropic.RateLimitError:
                wait = 2 ** attempt * 5
                print(f"  ⏳  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            except Exception as e:
                print(f"  ❌  [{self.name}] API error: {e}")
                raise
        raise RuntimeError(f"[{self.name}] Failed after 3 attempts")

    def call_json(self, system: str, user: str, max_tokens: Optional[int] = None) -> dict | list:
        """Make a Claude API call expecting a JSON response."""
        system_with_json = system + "\n\nRespond ONLY with valid JSON. No markdown fences, no preamble."
        raw = self.call(system_with_json, user, max_tokens)
        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict | list:
        """Parse JSON, stripping any markdown fences if present."""
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"  ⚠️  [{self.name}] JSON parse error: {e}")
            print(f"  Raw response: {raw[:500]}")
            raise
