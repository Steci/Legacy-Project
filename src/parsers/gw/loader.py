"""High-level helpers for loading GeneWeb databases.

These wrap :class:`GWParser` to keep the parsing step pure while ensuring the
post-import refresh (consanguinity computation, loop diagnostics, etc.) runs by
default for callers that just need a ready-to-use database.
"""

from __future__ import annotations

from typing import Optional

from .models import GWDatabase
from .parser import GWParser
from .refresh import refresh_consanguinity


def load_geneweb_text(
    text: str,
    *,
    compute_consanguinity: bool = True,
    debug: bool = False,
    parser: Optional[GWParser] = None,
) -> GWDatabase:
    """Parse *text* into a :class:`GWDatabase` and optionally compute consanguinity.

    Args:
        text: GeneWeb textual content.
        compute_consanguinity: Whether to trigger the refresh pass that computes
            consanguinity coefficients and collects loop diagnostics.
        debug: Passed to :class:`GWParser` if no explicit *parser* is provided.
        parser: Reuse an existing :class:`GWParser` instance when provided.
    """

    gw_parser = parser or GWParser(debug=debug)
    database = gw_parser.parse_text(text)
    if compute_consanguinity:
        refresh_consanguinity(database)
    return database


def load_geneweb_file(
    path: str,
    *,
    compute_consanguinity: bool = True,
    debug: bool = False,
    parser: Optional[GWParser] = None,
) -> GWDatabase:
    """Open and parse the GeneWeb file located at *path*.

    This mirrors :meth:`GWParser.parse_file` but runs the post-import refresh by
    default so downstream code immediately receives populated consanguinity
    coefficients.
    """

    gw_parser = parser or GWParser(debug=debug)
    database = gw_parser.parse_file(path)
    if compute_consanguinity:
        refresh_consanguinity(database)
    return database
