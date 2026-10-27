import json

import pytest

from app.domain.entities import ParsedRequest
from app.infrastructure.parsers import FallbackParser, LiteLLMParser, RuleBasedParser

CATEGORIES = ["Laptop", "Monitor", "Accessories", "Furniture", "Office Supplies"]


@pytest.mark.parametrize(
    ("text", "quantity", "product", "category"),
    [
        ("I need 5 new Lenovo Laptop", 5, "Lenovo Laptop", "Laptop"),
        ("Please order three monitors for the team", 3, "monitors", "Monitor"),
        ("an ergonomic office chair", 1, "ergonomic office chair", None),
        ("10x Logitech MX Keys", 10, "Logitech MX Keys", None),
    ],
)
def test_rule_based_parser_extracts_quantity_product_and_category(text, quantity, product, category):
    parsed = RuleBasedParser(CATEGORIES).parse(text)

    assert parsed.quantity == quantity
    assert parsed.product_name == product
    assert parsed.category == category


def test_rule_based_parser_without_quantity_has_low_confidence():
    parsed = RuleBasedParser(CATEGORIES).parse("Lenovo laptop")

    assert parsed.quantity is None
    assert parsed.confidence < 0.5


def _completion(content):
    return {"choices": [{"message": {"content": content}}]}


def test_llm_parser_reads_json_from_model_answer():
    calls = []

    def complete(messages, **kwargs):
        calls.append(messages)
        payload = {"quantity": 5, "productName": "Lenovo Laptop", "category": "Laptop", "confidence": 0.95}
        return _completion("Sure:\n```json\n" + json.dumps(payload) + "\n```")

    parsed = LiteLLMParser(CATEGORIES, complete=complete).parse("I need 5 new Lenovo Laptop")

    assert parsed == ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95)
    assert "Laptop" in calls[0][0]["content"]
    assert calls[0][-1] == {"role": "user", "content": "I need 5 new Lenovo Laptop"}


def test_llm_parser_rejects_invalid_json():
    parser = LiteLLMParser(CATEGORIES, complete=lambda messages, **kwargs: _completion("no idea"))

    with pytest.raises(ValueError):
        parser.parse("I need 5 new Lenovo Laptop")


def test_fallback_parser_uses_rules_when_llm_fails():
    class Broken:
        def parse(self, text):
            raise ConnectionError("gateway down")

    parsed = FallbackParser(Broken(), RuleBasedParser(CATEGORIES)).parse("I need 5 new Lenovo Laptop")

    assert parsed.quantity == 5
    assert parsed.product_name == "Lenovo Laptop"
