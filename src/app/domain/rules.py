"""Deterministic procurement rules: catalog matching, sourcing and approval."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable

from app.domain.value_objects import Money

if TYPE_CHECKING:
    from app.domain.entities import CatalogItem, ParsedRequest

AUTO_APPROVAL_LIMIT = Money(Decimal("1000"))
MANAGER_APPROVAL_LIMIT = Money(Decimal("25000"))

STOPWORDS = {"a", "an", "the", "new", "of", "for", "and", "with", "pcs", "pieces", "units"}


def normalize_tokens(text: str) -> set[str]:
    tokens = set()
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        tokens.add(word)
    return tokens


def find_matching_items(items: Iterable[CatalogItem], parsed: ParsedRequest) -> list[CatalogItem]:
    wanted = normalize_tokens(parsed.product_name or "")
    if not wanted:
        return []
    return [item for item in items if wanted <= normalize_tokens(f"{item.name} {item.category}")]


def select_cheapest(items: list[CatalogItem]) -> CatalogItem:
    return min(items, key=lambda item: item.unit_price)


def approval_level(total: Money, stock_ok: bool) -> str | None:
    if total <= AUTO_APPROVAL_LIMIT and stock_ok:
        return None
    if total <= MANAGER_APPROVAL_LIMIT:
        return "MANAGER"
    return "DIRECTOR"
