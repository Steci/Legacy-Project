from typing import List, Optional, Tuple

from ..models import GedcomRecord


class RecordReaderMixin:
    """Helpers for constructing the GedcomRecord tree."""

    def _parse_records(self, lines: List[bytes]) -> List[GedcomRecord]:
        """Parse GEDCOM lines into records."""

        records: List[GedcomRecord] = []
        stack: List[GedcomRecord] = []

        for line_num, line in enumerate(lines, 1):
            clean_line = line.rstrip(b"\r\n")
            record = self._parse_line(clean_line, line_num)
            if not record:
                continue

            while stack and stack[-1].level >= record.level:
                stack.pop()

            if stack:
                stack[-1].sub_records.append(record)
            else:
                records.append(record)

            stack.append(record)

        return records

    def _parse_line(self, line: bytes, line_num: int) -> Optional[GedcomRecord]:
        """Parse a single GEDCOM line with simplified validation."""

        if not self._is_valid_line(line):
            return None

        level, xref_id, tag, value, raw_value = self._extract_line_components(line)

        record = GedcomRecord(
            level=level,
            tag=tag,
            value=value,
            xref_id=xref_id,
            line_number=line_num,
            raw_value=raw_value,
        )

        return record

    def _is_valid_line(self, line: bytes) -> bool:
        """Validate GEDCOM line format."""
        if not line or line.startswith(b"//"):
            return False
        parts = line.split(b" ", 1)
        return bool(parts and parts[0].isdigit())

    def _extract_line_components(self, line: bytes) -> Tuple[int, Optional[str], str, str, bytes]:
        """Extract level, xref, tag and value bytes from line."""

        parts = line.split(b" ", 2)
        level = int(parts[0])

        xref_id: Optional[str] = None
        tag_bytes = b""
        value_bytes = b""

        if len(parts) >= 2:
            second = parts[1]
            if second.startswith(b"@") and second.endswith(b"@"):
                xref_id = second.decode("latin-1")
                if len(parts) == 3:
                    tag_and_value = parts[2]
                    tag_parts = tag_and_value.split(b" ", 1)
                    tag_bytes = tag_parts[0]
                    if len(tag_parts) > 1:
                        value_bytes = tag_parts[1]
            else:
                tag_bytes = second
                if len(parts) == 3:
                    value_bytes = parts[2]

        tag = tag_bytes.decode("latin-1") if tag_bytes else ""
        value = value_bytes.decode("latin-1") if value_bytes else ""

        return level, xref_id, tag, value, value_bytes
