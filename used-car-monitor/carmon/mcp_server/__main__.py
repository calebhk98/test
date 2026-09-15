"""Keeps `python3 -m carmon.mcp_server` working now that mcp_server is a
package rather than a single module."""

import sys

from .server import main

if __name__ == "__main__":
    sys.exit(main())
