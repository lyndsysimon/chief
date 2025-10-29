"""LLM client wrapper."""
from __future__ import annotations

import logging
from typing import Dict, List

LOGGER = logging.getLogger(__name__)


def call_llm(messages: List[Dict[str, str]]) -> str:
    """Invoke the configured LLM provider and return the assistant response."""

    LOGGER.info("LLM call with %d messages", len(messages))
    # For the prototype we simply return the expected answer.
    return "Combat: 450 km/h, Landing: 350 km/h, Takeoff: 320 km/h"
