"""Create procurement.db with schema, master data and demo requests.

Usage: .venv/bin/python scripts/init_db.py [--reset]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.application.use_cases import ApproveRequest, SendOrder, SubmitRequest  # noqa: E402
from app.infrastructure.db import (  # noqa: E402
    Database,
    SqlCatalogRepository,
    SqlCostCenterRepository,
    SqlRequestRepository,
)
from app.infrastructure.parsers import RuleBasedParser  # noqa: E402

DB_FILE = ROOT / "procurement.db"
DEMO_PROMPTS = [
    ("I need 5 new Lenovo Laptop", "CC-100", "Anna Keller", "send"),
    ("2 Logitech Mouse", "CC-200", "Marco Rossi", "send"),
    ("Please order three monitors for the team", "CC-100", "Lea Meier", None),
    ("I need 3 Commodore 64", "CC-300", "Jonas Weber", None),
    ("I need 5 new Lenovo Laptop", "CC-100", "Anna Keller", None),
]


def main() -> None:
    if "--reset" in sys.argv:
        DB_FILE.unlink(missing_ok=True)
    elif DB_FILE.exists():
        sys.exit(f"{DB_FILE.name} already exists (use --reset to recreate it)")

    database = Database(f"sqlite:///{DB_FILE}")
    database.create_schema()
    database.seed()

    catalog = SqlCatalogRepository(database)
    centers = SqlCostCenterRepository(database)
    requests = SqlRequestRepository(database)
    parser = RuleBasedParser(sorted({item.category for item in catalog.list_items()}))
    submit = SubmitRequest(parser, catalog, centers, requests)

    for prompt, cost_center, requester, action in DEMO_PROMPTS:
        request = submit.execute(prompt, cost_center, requester)
        if action == "send":
            if request.requires_approval:
                ApproveRequest(requests).execute(request.id)
            request = SendOrder(requests, catalog, centers).execute(request.id)
        print(f"{request.id}  {request.status.value:17} {requester:12} {prompt}")
    print(f"Created {DB_FILE}")


if __name__ == "__main__":
    main()
