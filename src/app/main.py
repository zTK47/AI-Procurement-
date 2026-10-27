"""Composition root: wires infrastructure adapters into the use cases."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.application.ports import RequestParser
from app.application.use_cases import ApproveRequest, RejectRequest, SendOrder, SubmitRequest
from app.infrastructure.db import Database, SqlCatalogRepository, SqlCostCenterRepository, SqlRequestRepository
from app.infrastructure.parsers import FallbackParser, LiteLLMParser, RuleBasedParser
from app.interfaces.api import Services, install


def _default_parser(categories: list[str]) -> tuple[RequestParser, str]:
    rules = RuleBasedParser(categories)
    if os.getenv("PARSER", "llm").lower() == "rules":
        return rules, "rules"
    return FallbackParser(LiteLLMParser(categories), rules), f"llm:{os.getenv('LITELLM_MODEL', 'default')}"


def create_app(parser: RequestParser | None = None, database_url: str | None = None) -> FastAPI:
    load_dotenv()
    database = Database(database_url or os.getenv("DATABASE_URL", "sqlite:///./procurement.db"))
    database.create_schema()
    database.seed()

    catalog = SqlCatalogRepository(database)
    cost_centers = SqlCostCenterRepository(database)
    requests = SqlRequestRepository(database)

    parser_name = type(parser).__name__ if parser else ""
    if parser is None:
        categories = sorted({item.category for item in catalog.list_items()})
        parser, parser_name = _default_parser(categories)

    app = FastAPI(title="AI Procurement", version="0.1.0")
    install(app, Services(
        submit=SubmitRequest(parser, catalog, cost_centers, requests),
        approve=ApproveRequest(requests),
        reject=RejectRequest(requests),
        send=SendOrder(requests, catalog, cost_centers),
        catalog=catalog,
        cost_centers=cost_centers,
        requests=requests,
        parser_name=parser_name,
    ))
    return app
