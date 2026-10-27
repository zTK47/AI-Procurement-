from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import total_ordering


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int) or self.value < 1:
            raise ValueError("Quantity must be a positive integer")


@dataclass(frozen=True)
class Sku:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("SKU must not be empty")


@total_ordering
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "CHF"

    def __post_init__(self):
        object.__setattr__(self, "amount", Decimal(self.amount))
        if self.amount < 0:
            raise ValueError("Money amount must not be negative")

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Quantity | int) -> Money:
        value = factor.value if isinstance(factor, Quantity) else factor
        return Money(self.amount * value, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount < other.amount
