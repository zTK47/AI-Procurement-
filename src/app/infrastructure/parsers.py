"""Adapters that turn a natural-language prompt into a ParsedRequest."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from pydantic import BaseModel, Field

from app.application.ports import RequestParser
from app.domain.entities import ParsedRequest
from app.domain.rules import normalize_tokens

logger = logging.getLogger(__name__)

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "dozen": 12,
}
FILLER_WORDS = {
    "i", "we", "need", "needs", "want", "would", "like", "to", "please", "order", "buy",
    "get", "new", "some", "me", "us", "x", "pcs", "pieces", "units", "of", "the",
}


def _match_category(text: str, categories: list[str]) -> str | None:
    tokens = normalize_tokens(text)
    for category in categories:
        if normalize_tokens(category) <= tokens:
            return category
    return None


class RuleBasedParser:
    """Deterministic fallback parser for simple prompts."""

    def __init__(self, categories: list[str]):
        self.categories = categories

    def parse(self, text: str) -> ParsedRequest:
        words = text.split()
        quantity, quantity_index = None, None
        for index, word in enumerate(words):
            match = re.fullmatch(r"(\d+)x?", word.lower())
            if match:
                quantity, quantity_index = int(match.group(1)), index
                break
        if quantity is None:
            for index, word in enumerate(words):
                if word.lower() in NUMBER_WORDS:
                    quantity, quantity_index = NUMBER_WORDS[word.lower()], index
                    break

        product_words = []
        for index, word in enumerate(words):
            clean = word.strip(".,;:!?")
            if clean.lower() == "for":
                break
            if index == quantity_index or clean.lower() in FILLER_WORDS or not clean:
                continue
            product_words.append(clean)
        product = " ".join(product_words)

        complete = bool(quantity and product)
        return ParsedRequest(
            quantity=quantity,
            product_name=product,
            category=_match_category(text, self.categories),
            confidence=0.7 if complete else 0.3,
        )


class _LlmAnswer(BaseModel):
    quantity: int | None = Field(default=None, ge=1)
    productName: str = ""
    category: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)


SYSTEM_PROMPT = """You extract purchase requests for a procurement system.
Return ONLY a JSON object with the keys:
  "quantity" (integer or null), "productName" (short product name without quantity),
  "category" (one of: {categories}, or null), "confidence" (0..1).
The prompt may be in any language: write productName in English, singular,
with brand and product type (e.g. "Logitech Mouse", "Office Chair").
Do not invent products. Example:
Input: "I need 5 new Lenovo Laptop"
Output: {{"quantity": 5, "productName": "Lenovo Laptop", "category": "Laptop", "confidence": 0.95}}"""


def _content(response: Any) -> str:
    try:
        return response.choices[0].message.content
    except AttributeError:
        return response["choices"][0]["message"]["content"]


class LiteLLMParser:
    """Parses prompts with an LLM behind the LiteLLM gateway."""

    def __init__(self, categories: list[str], complete: Callable[..., Any] | None = None):
        self.categories = categories
        if complete is None:
            from app.infrastructure.llm_client import complete
        self.complete = complete

    def parse(self, text: str) -> ParsedRequest:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(categories=", ".join(self.categories))},
            {"role": "user", "content": text},
        ]
        content = _content(self.complete(messages)) or ""
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("LLM answer contains no JSON object")
        answer = _LlmAnswer.model_validate(json.loads(match.group(0)))
        return ParsedRequest(answer.quantity, answer.productName.strip(), answer.category, answer.confidence)


class FallbackParser:
    """Uses the primary parser and falls back when it fails."""

    def __init__(self, primary: RequestParser, fallback: RequestParser):
        self.primary = primary
        self.fallback = fallback

    def parse(self, text: str) -> ParsedRequest:
        try:
            return self.primary.parse(text)
        except Exception as error:
            logger.warning("Primary parser failed, using fallback: %s", error)
            return self.fallback.parse(text)
