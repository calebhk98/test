"""Shared test scaffolding for carmon.mcp_server.

Every `tests/test_mcp_*.py` module needs the same seeded MCPServer base class and the
same "unwrap a tools/call JSON result" helper -- this module holds only that plumbing
(plus the two reliability fixtures the base class seeds), not because it holds tests
itself: `unittest discover`'s default `test*.py` pattern skips it, and it is only ever
reached by being imported.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from carmon import db
from carmon.config import load_config
from carmon.mcp_server import MCPServer

RELIABLE_FACTS = {
    "complaint_count": 5,
    "recall_count": 1,
    "crash_complaints": 0,
    "fire_complaints": 0,
    "injuries": 0,
    "deaths": 0,
    "top_components": [["STEERING", 3], ["BRAKES", 2]],
    "recalls": [
        {
            "campaign": "24V001000",
            "component": "STEERING",
            "summary": "steering column may loosen",
            "consequence": "loss of control",
            "remedy": "inspect and replace",
            "report_date": "01/02/2024",
            "park_it": False,
            "park_outside": False,
        }
    ],
    "source": "nhtsa",
}

LOUD_FACTS = {
    "complaint_count": 500,
    "recall_count": 4,
    "crash_complaints": 10,
    "fire_complaints": 2,
    "injuries": 3,
    "deaths": 0,
    "top_components": [["ENGINE", 200], ["FUEL SYSTEM", 100]],
    "recalls": [],
    "source": "nhtsa",
}


def make_listing(vin="VIN0001", **overrides):
    listing = {
        "vin": vin,
        "year": 2022,
        "make": "Honda",
        "model": "Civic",
        "trim": "LX",
        "body_type": "Sedan",
        "fuel_type": "Gasoline",
        "mileage": 30000,
        "price_current": 18000,
        "price_first_seen": 19000,
        "dealer_name": "Example Honda",
        "dealer_city": "Springfield",
        "dealer_state": "TN",
        "distance_miles": 25.0,
        "cpo": True,
        "listing_url": "https://example.com/listing/vin0001",
        "score": 3.5,
        "score_breakdown": [{"label": "test", "value": 1.0, "detail": "detail"}],
        "source": "marketcheck",
    }
    listing.update(overrides)
    return listing


class MCPServerTestCase(unittest.TestCase):
    """Base class that builds a real MCPServer against a temp, seeded DB."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "carmon.db"

        conn = db.init_db(self.db_path)
        db.upsert_listing(conn, make_listing(vin="VIN0001", score=5.0), seen_date="2026-08-10")
        # Give VIN0001 a price drop on a later date.
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0001", score=5.0, price_current=17000),
            seen_date="2026-08-17",
        )
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0002", make="Toyota", model="Corolla", score=1.0, cpo=False),
            seen_date="2026-08-17",
        )
        # A third listing whose model/year has no cached NHTSA data at all, to prove
        # "unknown" is never treated as "bad" by the search filters.
        db.upsert_listing(
            conn,
            make_listing(vin="VIN0003", make="Kia", model="Forte", score=2.0, cpo=False),
            seen_date="2026-08-17",
        )
        # Seed cached NHTSA reliability: VIN0001 (Honda Civic 2022) is quiet, VIN0002
        # (Toyota Corolla 2022) is loud. VIN0003's model/year (Kia Forte 2022) is left
        # unseeded on purpose.
        db.save_reliability(conn, "Honda", "Civic", 2022, RELIABLE_FACTS)
        db.save_reliability(conn, "Toyota", "Corolla", 2022, LOUD_FACTS)
        db.save_mpg(conn, "Honda", "Civic", 2022, {"city_mpg": 33, "highway_mpg": 42, "combined_mpg": 36.5, "source": "fueleconomy.gov"})
        conn.close()

        config = load_config()  # real project config.json for search/scoring sections
        # Point paths.db at our temp DB using an ABSOLUTE path (relative paths
        # resolve against the project root, not the temp dir).
        config.data["paths"]["db"] = str(self.db_path.resolve())
        self.config = config
        self.server = MCPServer(config)

    def tearDown(self):
        self.server.close()
        self.tmpdir.cleanup()

    def call(self, method, params=None, request_id=1):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if request_id is not None:
            message["id"] = request_id
        return self.server.handle_request(message)

    def call_tool(self, name, arguments=None):
        return self.call("tools/call", {"name": name, "arguments": arguments or {}})

    def _tool_json(self, resp):
        """Unwrap a successful tools/call result's single text content block as JSON --
        shared by every test class that calls a tool and expects a JSON payload back."""
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertFalse(result.get("isError"))
        text = result["content"][0]["text"]
        return json.loads(text)
