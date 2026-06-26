"""
LLM Helper Utilities — Shared functions for cleaning and parsing LLM outputs.
"""

import json
import logging

logger = logging.getLogger(__name__)


def parse_llm_json(response: str, default_factory=dict) -> dict | list:
    """
    Parse a JSON string from LLM responses robustly.
    Handles raw JSON, markdown-wrapped JSON blocks, and extra leading/trailing text.
    """
    if not response:
        return default_factory()

    cleaned = response.strip()

    # 1. Clean markdown code block wraps (e.g., ```json ... ```)
    if cleaned.startswith("```"):
        try:
            parts = cleaned.split("```")
            if len(parts) >= 3:
                block = parts[1]
                if block.startswith("json"):
                    block = block[4:]
                cleaned = block.strip()
        except Exception as e:
            logger.warning(f"Error parsing markdown JSON wrapper: {e}")

    # 2. Try parsing direct block
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Find bounding brackets/braces for embedded JSON
    start_bracket = cleaned.find("[")
    start_brace = cleaned.find("{")

    start_idx = -1
    end_idx = -1

    if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
        # Array bounds
        start_idx = start_bracket
        end_idx = cleaned.rfind("]") + 1
    elif start_brace != -1:
        # Object bounds
        start_idx = start_brace
        end_idx = cleaned.rfind("}") + 1

    if start_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(cleaned[start_idx:end_idx])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bounded JSON block: {e}. Raw response snippet: {response[:200]}")

    return default_factory()
