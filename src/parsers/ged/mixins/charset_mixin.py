from typing import List, Optional

from ..encoding_utils import decode_bytes
from ..models import GedcomRecord


class CharsetMixin:
    """Charset detection and decoding helpers for GedcomParser."""

    charset: str
    charset_override: Optional[str]

    def _initialize_charset(self, records: List[GedcomRecord]) -> None:
        """Determine the charset from BOM or HEAD record."""

        if self.charset_override:
            self.charset = self.charset_override
            return

        head_record = next((rec for rec in records if rec.tag == "HEAD"), None)
        if not head_record:
            return

        for sub_record in head_record.sub_records:
            if sub_record.tag == "CHAR":
                token_bytes = sub_record.raw_value or sub_record.value.encode("latin-1")
                charset_token = token_bytes.decode("latin-1").strip()
                if charset_token:
                    self.charset = self._normalise_charset_name(charset_token)
                return

    def _normalise_charset_name(self, token: str) -> str:
        """Map GEDCOM CHAR token to canonical charset name."""

        upper = token.upper()
        mapping = {
            "ANSEL": "ANSEL",
            "ANSI": "ANSI",
            "ASCII": "ASCII",
            "IBMPC": "ASCII",
            "MACINTOSH": "MACINTOSH",
            "MSDOS": "MSDOS",
            "UTF-8": "UTF-8",
            "UTF8": "UTF-8",
        }
        return mapping.get(upper, "ASCII")

    def _decode_record_values(self, records: List[GedcomRecord]) -> None:
        """Decode raw GEDCOM values according to detected charset."""

        for record in records:
            record.value = decode_bytes(record.raw_value, self.charset) if record.raw_value else ""
            self._fix_genealogos_bug(record)
            if record.sub_records:
                self._decode_record_values(record.sub_records)

    def _fix_genealogos_bug(self, record: GedcomRecord) -> GedcomRecord:
        """Fix genealogos-specific GEDCOM bugs"""
        if record.tag and record.tag.startswith("@"):
            record.tag, record.value = record.value, record.tag
        if record.tag == "NAME" and "~" in record.value:
            record.value = record.value.replace("~", "")

        return record
