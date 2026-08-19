"""Self-contained JSON API + HTML dashboard for browsing the listings DB.

Stdlib only (http.server / socketserver / sqlite3 / json / urllib). No Flask/FastAPI,
no external CSS/JS/CDN assets -- every page embeds its own CSS/JS inline.

Each request opens its own sqlite connection (sqlite3.Connection objects are not
thread-safe) and closes it in a `finally` block. The server runs on a
socketserver.ThreadingTCPServer so slow clients don't block each other.

Auth: if CARMON_API_TOKEN is configured (see carmon.config.get_secret), every
/api/* route except /api/health requires `Authorization: Bearer <token>`. If it
is unset, the API is open -- this is meant to run on localhost / a trusted LAN.

This package is a thin façade: the implementation lives in `carmon.web` (routing in
`routes`, JSON handlers in `api`, HTML pages in `pages`, shared markup in `render`,
request parsing in `forms`). Everything importable from here (`CarMonHandler`,
`create_server`, `serve`) is re-exported unchanged so `from carmon.webapp import serve`
keeps working.
"""

from __future__ import annotations

from ..web.routes import CarMonHandler, create_server, serve

__all__ = ["CarMonHandler", "create_server", "serve"]
