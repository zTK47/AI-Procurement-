import pytest

from app.infrastructure.db import normalize_database_url


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
        ("postgresql://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./procurement.db", "sqlite:///./procurement.db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_database_url_uses_the_psycopg_driver_for_postgres(given, expected):
    assert normalize_database_url(given) == expected
