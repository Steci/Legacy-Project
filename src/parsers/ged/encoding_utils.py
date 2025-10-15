"""Utilities for handling GEDCOM character set conversions.

This module mirrors the behaviour of geneweb's ged2gwb encoding helpers
so that the Python parser can decode GEDCOM content exactly like the
original OCaml implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CharsetMapping:
    """Descriptor for a GEDCOM charset."""

    name: str
    normalised: str


# Lookup tables adapted from geneweb/bin/ged2gwb/ged2gwb.ml
_MSDOS_MAP: Dict[int, int] = {
    0o200: 0o307,
    0o201: 0o374,
    0o202: 0o351,
    0o203: 0o342,
    0o204: 0o344,
    0o205: 0o340,
    0o206: 0o345,
    0o207: 0o347,
    0o210: 0o352,
    0o211: 0o353,
    0o212: 0o350,
    0o213: 0o357,
    0o214: 0o356,
    0o215: 0o354,
    0o216: 0o304,
    0o217: 0o305,
    0o220: 0o311,
    0o221: 0o346,
    0o222: 0o306,
    0o223: 0o364,
    0o224: 0o366,
    0o225: 0o362,
    0o226: 0o373,
    0o227: 0o371,
    0o230: 0o377,
    0o231: 0o326,
    0o232: 0o334,
    0o233: 0o242,
    0o234: 0o243,
    0o235: 0o245,
    0o240: 0o341,
    0o241: 0o355,
    0o242: 0o363,
    0o243: 0o372,
    0o244: 0o361,
    0o245: 0o321,
    0o246: 0o252,
    0o247: 0o272,
    0o250: 0o277,
    0o252: 0o254,
    0o253: 0o275,
    0o254: 0o274,
    0o255: 0o241,
    0o256: 0o253,
    0o257: 0o273,
    0o346: 0o265,
    0o361: 0o261,
    0o366: 0o367,
    0o370: 0o260,
    0o372: 0o267,
    0o375: 0o262,
}

_MAC_MAP: Dict[int, int] = {
    0o200: 0o304,
    0o201: 0o305,
    0o202: 0o307,
    0o203: 0o311,
    0o204: 0o321,
    0o205: 0o326,
    0o206: 0o334,
    0o207: 0o341,
    0o210: 0o340,
    0o211: 0o342,
    0o212: 0o344,
    0o213: 0o343,
    0o214: 0o345,
    0o215: 0o347,
    0o216: 0o351,
    0o217: 0o350,
    0o220: 0o352,
    0o221: 0o353,
    0o222: 0o355,
    0o223: 0o354,
    0o224: 0o356,
    0o225: 0o357,
    0o226: 0o361,
    0o227: 0o363,
    0o230: 0o362,
    0o231: 0o364,
    0o232: 0o366,
    0o233: 0o365,
    0o234: 0o372,
    0o235: 0o371,
    0o236: 0o373,
    0o237: 0o374,
    0o241: 0o260,
    0o244: 0o247,
    0o245: 0o267,
    0o246: 0o266,
    0o247: 0o337,
    0o250: 0o256,
    0o256: 0o306,
    0o257: 0o330,
    0o264: 0o245,
    0o273: 0o252,
    0o274: 0o272,
    0o276: 0o346,
    0o277: 0o370,
    0o300: 0o277,
    0o301: 0o241,
    0o302: 0o254,
    0o307: 0o253,
    0o310: 0o273,
    0o312: 0o040,
    0o313: 0o300,
    0o314: 0o303,
    0o315: 0o325,
    0o320: 0o255,
    0o326: 0o367,
    0o330: 0o377,
    0o345: 0o302,
    0o346: 0o312,
    0o347: 0o301,
    0o350: 0o313,
    0o351: 0o310,
    0o352: 0o315,
    0o353: 0o316,
    0o354: 0o317,
    0o355: 0o314,
    0o356: 0o323,
    0o357: 0o324,
    0o361: 0o322,
    0o362: 0o332,
    0o363: 0o333,
    0o364: 0o331,
}


def _translate_bytes(data: bytes, table: Dict[int, int]) -> bytes:
    """Translate a byte string according to ``table``."""

    return bytes(table.get(b, b) for b in data)


def ascii_of_msdos(data: bytes) -> bytes:
    """Convert CP437/MS-DOS bytes to Latin-1, mirroring ged2gwb."""

    return _translate_bytes(data, _MSDOS_MAP)


def ascii_of_macintosh(data: bytes) -> bytes:
    """Convert classic Mac encoding bytes to Latin-1."""

    return _translate_bytes(data, _MAC_MAP)


def _grave(ch: int) -> int:
    return {
        ord("a"): 0o340,
        ord("e"): 0o350,
        ord("i"): 0o354,
        ord("o"): 0o362,
        ord("u"): 0o371,
        ord("A"): 0o300,
        ord("E"): 0o310,
        ord("I"): 0o314,
        ord("O"): 0o322,
        ord("U"): 0o331,
        ord(" "): ord("`"),
    }.get(ch, ch)


def _acute(ch: int) -> int:
    return {
        ord("a"): 0o341,
        ord("e"): 0o351,
        ord("i"): 0o355,
        ord("o"): 0o363,
        ord("u"): 0o372,
        ord("y"): 0o375,
        ord("A"): 0o301,
        ord("E"): 0o311,
        ord("I"): 0o315,
        ord("O"): 0o323,
        ord("U"): 0o332,
        ord("Y"): 0o335,
        ord(" "): 0o264,
    }.get(ch, ch)


def _circumflex(ch: int) -> int:
    return {
        ord("a"): 0o342,
        ord("e"): 0o352,
        ord("i"): 0o356,
        ord("o"): 0o364,
        ord("u"): 0o373,
        ord("A"): 0o302,
        ord("E"): 0o312,
        ord("I"): 0o316,
        ord("O"): 0o324,
        ord("U"): 0o333,
        ord(" "): ord("^"),
    }.get(ch, ch)


def _umlaut(ch: int) -> int:
    return {
        ord("a"): 0o344,
        ord("e"): 0o353,
        ord("i"): 0o357,
        ord("o"): 0o366,
        ord("u"): 0o374,
        ord("y"): 0o377,
        ord("A"): 0o304,
        ord("E"): 0o313,
        ord("I"): 0o317,
        ord("O"): 0o325,
        ord("U"): 0o334,
        ord(" "): 0o250,
    }.get(ch, ch)


def _circle(ch: int) -> int:
    return {
        ord("a"): 0o345,
        ord("A"): 0o305,
        ord(" "): 0o260,
    }.get(ch, ch)


def _tilde(ch: int) -> int:
    return {
        ord("a"): 0o343,
        ord("n"): 0o361,
        ord("o"): 0o365,
        ord("A"): 0o303,
        ord("N"): 0o321,
        ord("O"): 0o327,
        ord(" "): ord("~"),
    }.get(ch, ch)


def _cedilla(ch: int) -> int:
    return {
        ord("c"): 0o347,
        ord("C"): 0o307,
        ord(" "): 0o270,
    }.get(ch, ch)


def _slash(ch: int) -> int:
    return {
        ord("C"): 0o242,
        ord("c"): 0o242,
        ord("O"): 0o330,
        ord("o"): 0o370,
        ord(" "): ord("/"),
    }.get(ch, ch)


def _ansel_digraph(code: int, trail: int) -> Tuple[int, int]:
    """Interpret an ANSEL digraph (accent + base)."""

    mapping = {
        224: _acute,
        225: _grave,
        226: _acute,
        227: _circumflex,
        228: _tilde,
        232: _umlaut,
        234: _circle,
        235: _tilde,
        236: _umlaut,
        237: _acute,
        238: _umlaut,
        240: _cedilla,
        247: _cedilla,
        248: _cedilla,
        249: _cedilla,
        252: _slash,
        254: _acute,
    }
    handler = mapping.get(code)
    if handler:
        return handler(trail), 2
    return trail, 1


_ANSEL_DOUBLE_MAP: Dict[int, Tuple[int, int]] = {
    166: (ord("O"), ord("E")),
    172: (ord("O"), 0o264),
    173: (ord("U"), 0o264),
    182: (ord("o"), ord("e")),
    188: (ord("o"), 0o264),
    189: (ord("u"), 0o264),
}


_ANSEL_SINGLE_MAP: Dict[int, int] = {
    161: ord("L"),
    162: 0o330,
    163: 0o320,
    164: 0o336,
    165: 0o306,
    167: 0o264,
    168: 0o267,
    169: ord("b"),
    170: 0o256,
    171: 0o257,
    174: 0o264,
    176: 0o264,
    177: ord("l"),
    178: 0o370,
    179: 0o360,
    180: 0o376,
    181: 0o346,
    183: ord('"'),
    184: ord("i"),
    185: 0o243,
    186: 0o360,
    190: 0o201,
    191: 0o201,
    192: 0o260,
    193: ord("l"),
    194: ord("P"),
    195: 0o251,
    196: ord("#"),
    197: 0o277,
    198: 0o241,
    205: ord("e"),
    206: ord("o"),
    207: 0o337,
}


def ansel_to_iso_8859_1(data: bytes) -> bytes:
    """Convert ANSEL encoded bytes to ISO-8859-1 bytes."""

    result = bytearray()
    i = 0
    limit = len(data)
    while i < limit:
        code = data[i]
        if i == limit - 1:
            result.append(code)
            break
        if code in _ANSEL_DOUBLE_MAP:
            first, second = _ANSEL_DOUBLE_MAP[code]
            result.extend((first, second))
            i += 1
            continue
        if code >= 224:
            if i + 1 < limit:
                trail = data[i + 1]
                mapped, step = _ansel_digraph(code, trail)
                result.append(mapped)
                i += step
                continue
            result.append(code)
            i += 1
            continue
        if code >= 161:
            mapped = _ANSEL_SINGLE_MAP.get(code, 129)
            result.append(mapped)
            i += 1
            continue
        result.append(code)
        i += 1
    return bytes(result)


def decode_bytes(data: bytes, charset: str) -> str:
    """Decode ``data`` according to GEDCOM charset rules."""

    normalized = charset.upper() if charset else "ASCII"
    if normalized == "ANSEL":
        return ansel_to_iso_8859_1(data).decode("latin-1")
    if normalized in {"ANSI", "ASCII", "IBMPC"}:
        return data.decode("latin-1")
    if normalized == "MSDOS":
        return ascii_of_msdos(data).decode("latin-1")
    if normalized == "MACINTOSH":
        return ascii_of_macintosh(data).decode("latin-1")
    if normalized in {"UTF-8", "UTF8"}:
        return data.decode("utf-8")
    # Geneweb defaults to ISO-8859-1 when charset is unknown.
    return data.decode("latin-1")
