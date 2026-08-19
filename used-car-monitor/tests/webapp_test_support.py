"""Shared HTTP-test scaffolding for carmon.webapp.

Every `tests/test_webapp_*.py` module needs the same three things: a real
`CarMonHandler` HTTP server started against a temp sqlite db (and torn down
afterwards), a config pointed at that temp db, and small helpers for making
requests against the running server. This module holds only that plumbing --
it defines no tests itself, so `unittest discover`'s default `test*.py`
pattern skips it and it is only ever reached by being imported.
"""

from __future__ import annotations

import json
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from carmon import webapp
from carmon.config import Config, load_config


def temp_db_config(db_path: Path) -> Config:
    """A real project config.json (search/scoring/... sections) with paths.db pointed at
    an absolute temp path -- Config.db_path resolves relative paths against the project
    root, so a bare filename would not land in the caller's tempdir."""
    config = load_config()
    config.data["paths"] = dict(config.paths)
    config.data["paths"]["db"] = str(db_path)
    return config


def make_listing(vin: str, **overrides: Any) -> Dict[str, Any]:
    listing = {
        "vin": vin,
        "year": 2022,
        "make": "Toyota",
        "model": "Corolla",
        "trim": "LE",
        "mileage": 25000,
        "price_current": 18500,
        "dealer_name": "Test Toyota",
        "dealer_city": "Nashville",
        "dealer_state": "TN",
        "distance_miles": 42.0,
        "cpo": True,
        "listing_url": "https://example.com/listing/" + vin,
        "score": 3.5,
        "score_breakdown": [
            {"label": "preferred_model", "value": 2.0, "detail": "Toyota Corolla is a preferred model"},
            {"label": "cpo", "value": 2.0, "detail": "Certified pre-owned"},
            {"label": "distance", "value": -0.5, "detail": "42.0 miles (50 free)"},
        ],
        "body_type": "Sedan",
        "fuel_type": "Gasoline",
    }
    listing.update(overrides)
    return listing


class LiveServerCase:
    """Mixin (combined with `unittest.TestCase`) that starts a real CarMonHandler HTTP
    server for a test class's lifetime, plus the `_url`/`_get`/`_get_json`/`_post`
    request helpers every webapp test needs.

    Usage: a subclass's `setUp` calls `super().setUp()` first (for `self._tmpdir` /
    `self.tmp_root`), seeds whatever data or config the test class needs, then calls
    `self._start_server(config)`. A subclass that needs extra teardown work (restoring a
    patched module attribute, an env var, ...) should override `tearDown`, do that work,
    then call `self._stop_server()` and `self._tmpdir.cleanup()` itself -- in that order
    -- rather than `super().tearDown()`, matching where the extra step ran when each test
    class owned its own setUp/tearDown outright.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._stop_server()
        self._tmpdir.cleanup()

    def _start_server(self, config: Config) -> None:
        self.config = config
        self.server = webapp.create_server(config, host="127.0.0.1", port=0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _stop_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _url(self, path: str) -> str:
        return f"http://{self.host}:{self.port}{path}"

    def _get(self, path: str, headers: Optional[Dict[str, str]] = None):
        req = Request(self._url(path), headers=headers or {})
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def _get_json(self, path: str, headers: Optional[Dict[str, str]] = None, expect_status: int = 200):
        status, body = self._get(path, headers=headers)
        self.assertEqual(status, expect_status, msg=body)
        return json.loads(body)

    def _post(self, path: str, json_body: Any = None, headers: Optional[Dict[str, str]] = None, form=None):
        headers = dict(headers or {})
        if form is not None:
            data = urlencode(form).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        else:
            data = json.dumps(json_body if json_body is not None else {}).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        req = Request(self._url(path), data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except HTTPError as exc:
            return exc.code, exc.read()
