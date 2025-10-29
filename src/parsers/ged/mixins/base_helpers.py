from typing import List, Optional

from ..models import GedcomRecord


class RecordTraversalMixin:
    """Helpers for navigating GEDCOM record trees."""

    def _find_sub_record(self, record: GedcomRecord, tag: str) -> Optional[GedcomRecord]:
        """Find first sub-record with given tag"""
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                return sub_record
        return None

    def _find_all_sub_records(self, record: GedcomRecord, tag: str) -> List[GedcomRecord]:
        """Find all sub-records with given tag"""
        found = []
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                found.append(sub_record)
        return found

    def _strip_spaces(self, value: Optional[str]) -> str:
        """Utility mirroring ged2gwb strip_spaces."""
        return value.strip() if value else ""

    def _rebuild_text(self, record: Optional[GedcomRecord]) -> str:
        """Rebuild text with CONT/CONC semantics like ged2gwb."""
        if not record:
            return ""

        text = self._strip_spaces(record.value)
        trailing_space = record.value.endswith(" ") if record.value else False
        if trailing_space:
            text += " "

        for sub_rec in record.sub_records:
            value = sub_rec.value
            if not value:
                continue
            stripped = self._strip_spaces(value)
            end_space = value.endswith(" ")

            if sub_rec.tag == "CONC":
                text += stripped
                if end_space:
                    text += " "
            elif sub_rec.tag == "CONT":
                text += "<br>\n" + stripped
                if end_space:
                    text += " "

        return text

    def _find_in_records(self, records: List[GedcomRecord], tag: str) -> Optional[GedcomRecord]:
        """Find first record with tag within a record list."""
        for record in records:
            if record.tag == tag:
                record.used = True
                return record
        return None

    def _record_content(self, record: Optional[GedcomRecord]) -> str:
        """Return record content with CONC/CONT applied."""
        if not record:
            return ""
        return self._strip_spaces(self._rebuild_text(record))
