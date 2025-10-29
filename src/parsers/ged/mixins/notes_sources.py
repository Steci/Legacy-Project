from dataclasses import dataclass, field
from typing import List, Optional, Tuple, TYPE_CHECKING

from models.event import Event

from ..models import GedcomRecord, Note, Source

if TYPE_CHECKING:
	from ..models import GedcomDatabase


@dataclass
class SourceCollection:
	"""Aggregate structure mirroring ged2gwb treat_source results."""

	context: str = ""
	texts: List[str] = field(default_factory=list)
	note_texts: List[str] = field(default_factory=list)
	html_segments: List[str] = field(default_factory=list)
	raw_subrecords: List[List[GedcomRecord]] = field(default_factory=list)

	def combined_text(self) -> str:
		return " ".join(text for text in self.texts if text).strip()

	def combined_notes(self) -> str:
		note_segments = [seg for seg in self.note_texts if seg]
		html_segments = [seg for seg in self.html_segments if seg]

		notes = "<br>\n".join(note_segments)
		html = "".join(html_segments)

		if notes and html:
			return f"{notes}<br>\n{html}"
		return notes or html


class NoteSourceMixin:
	"""Note and source handling helpers extracted from GedcomParser."""

	database: "GedcomDatabase"
	untreated_in_notes: bool
	default_source: str
	_note_records: dict
	_source_records: dict

	def _extract_notes(self, record: GedcomRecord) -> str:
		"""Extract notes from record using ged2gwb rules."""

		rendered_notes: List[str] = []

		for note_record in self._find_all_sub_records(record, "NOTE"):
			text = self._render_note_reference(note_record)
			if text:
				rendered_notes.append(text)

		return "<br>\n".join(rendered_notes)

	def _process_note_record(self, note_record: GedcomRecord) -> str:
		"""Process a single note record."""

		if note_record.value.startswith('@') and note_record.value.endswith('@'):
			referenced = self._note_records.get(note_record.value)
			if referenced:
				return self._compose_note_text(referenced)
			stored = self.database.notes.get(note_record.value)
			return stored.content if stored else Note().content

		return self._compose_note_text(note_record)

	def _render_note_content(self, note_record: GedcomRecord) -> str:
		"""Render a top-level NOTE record to text."""

		return self._compose_note_text(note_record)

	def _compose_note_text(self, note_record: GedcomRecord) -> str:
		"""Combine NOTE, CONC and CONT records into a single string."""

		text = self._strip_spaces(note_record.value)
		trailing_space = note_record.value.endswith(" ") if note_record.value else False
		if trailing_space:
			text += " "

		for sub_rec in note_record.sub_records:
			raw_value = sub_rec.value or ""
			stripped = self._strip_spaces(raw_value)
			end_space = raw_value.endswith(" ")

			if sub_rec.tag == "CONC":
				if not raw_value:
					continue
				text += stripped
				if end_space:
					text += " "
			elif sub_rec.tag == "CONT":
				text += "<br>\n"
				text += stripped
				if end_space:
					text += " "

		return text

	def _render_note_reference(self, note_record: GedcomRecord) -> str:
		"""Render either inline or referenced note using compose helper."""

		if note_record.value.startswith('@') and note_record.value.endswith('@'):
			referenced = self._note_records.get(note_record.value)
			if referenced:
				return self._compose_note_text(referenced)
			stored = self.database.notes.get(note_record.value)
			return stored.content if stored else ""

		return self._compose_note_text(note_record)

	def _render_source_notes(self, sub_records: List[GedcomRecord]) -> str:
		"""Render TITL/TEXT blocks from a source record list."""

		if not sub_records:
			return ""

		title = self._rebuild_text(self._find_in_records(sub_records, "TITL"))
		text = self._rebuild_text(self._find_in_records(sub_records, "TEXT"))

		if title:
			bold_title = f"<b>{title}</b>"
			return f"{bold_title}<br>\n{text}" if text else bold_title

		return text

	def _process_source_reference(
		self,
		sour_record: GedcomRecord,
		context_label: str,
	) -> Tuple[str, str, List[str], List[GedcomRecord], Optional[str]]:
		"""Return structured details for a SOUR reference."""

		value = sour_record.value or ""
		sub_records: List[GedcomRecord] = []

		if value.startswith('@') and value.endswith('@'):
			referenced = self._source_records.get(value)
			if referenced:
				text = self._record_content(referenced)
				sub_records = referenced.sub_records
				note_text = self._render_source_notes(sub_records)
				extras = self._extract_additional_source_notes(sub_records)
				html = self._build_html_from_subrecords(context_label, sub_records)
				return text, note_text, extras, sub_records, html

			stored = self.database.sources.get(value)
			if stored:
				parts = [stored.title, stored.author, stored.publication]
				text = ", ".join(part for part in parts if part)
				return text or value, "", [], [], None

			self.add_warning(f"Source {value} not found", sour_record.line_number)
			return "", "", [], [], None

		text = self._record_content(sour_record)
		sub_records = sour_record.sub_records
		note_text = self._render_source_notes(sub_records)
		extras = self._extract_additional_source_notes(sub_records)
		html = self._build_html_from_subrecords(context_label, sub_records)
		return text, note_text, extras, sub_records, html

	def _extract_source(self, record: GedcomRecord, context_label: Optional[str] = None) -> SourceCollection:
		"""Extract source information and associated note fragments."""

		context = context_label or f"{record.tag} SOUR"
		collection = SourceCollection(context=context)

		for sour_record in self._find_all_sub_records(record, "SOUR"):
			text, note_text, extras, sub_records, html_segment = self._process_source_reference(
				sour_record,
				context,
			)
			if text:
				collection.texts.append(text)
			if note_text:
				collection.note_texts.append(note_text)
			if extras:
				collection.note_texts.extend(extras)
			if html_segment:
				collection.html_segments.append(html_segment)
			if sub_records:
				collection.raw_subrecords.append(list(sub_records))

		return collection

	def _extract_additional_source_notes(self, sub_records: List[GedcomRecord]) -> List[str]:
		"""Pull PAGE/QUAY/NOTE/DATA details into note text like ged2gwb."""

		segments: List[str] = []
		for sub in sub_records:
			if sub.tag == "PAGE":
				sub.used = True
				page_text = self._record_content(sub)
				if page_text:
					segments.append(f"Page: {page_text}")
			elif sub.tag == "QUAY":
				sub.used = True
				certainty = self._strip_spaces(sub.value)
				if certainty:
					segments.append(f"Certainty: {certainty}")
			elif sub.tag == "NOTE":
				sub.used = True
				note_text = self._render_note_reference(sub)
				if note_text:
					segments.append(note_text)
			elif sub.tag == "DATA":
				sub.used = True
				segments.extend(self._render_source_data_segments(sub))
		return segments

	def _render_source_data_segments(self, data_record: GedcomRecord) -> List[str]:
		"""Render DATA sub-records (DATE/TEXT/NOTE) for source notes."""

		segments: List[str] = []

		date_record = self._find_sub_record(data_record, "DATE")
		if date_record:
			date_text = self._record_content(date_record)
			if date_text:
				segments.append(f"Data date: {date_text}")

		for sub in data_record.sub_records:
			if sub.tag == "TEXT":
				sub.used = True
				text_value = self._rebuild_text(sub)
				if text_value:
					segments.append(text_value)
			elif sub.tag == "NOTE":
				sub.used = True
				note_text = self._render_note_reference(sub)
				if note_text:
					segments.append(note_text)

		return segments

	def _build_html_from_subrecords(self, context: str, sub_records: List[GedcomRecord]) -> Optional[str]:
		"""Reproduce ged2gwb html_text_of_tags for untreated source tags."""

		if not self.untreated_in_notes or not sub_records:
			return None

		lines = []

		def walk(records: List[GedcomRecord], level: int) -> List[str]:
			collected: List[str] = []
			for rec in records:
				child_lines = walk(rec.sub_records, level + 1)
				include = not rec.used or child_lines
				if not include:
					continue
				pieces = [str(level), rec.tag]
				value = self._strip_spaces(rec.value)
				if value:
					pieces.append(value)
				collected.append(" ".join(pieces))
				collected.extend(child_lines)
			return collected

		body_lines = walk(sub_records, 1)
		if not body_lines:
			return None

		header = "-- GEDCOM --" if not context else f"-- GEDCOM ({context}) --"
		lines.append(header)
		lines.extend(body_lines)
		return "<pre>\n" + "\n".join(lines) + "\n</pre>"

	def _merge_notes(self, base: str, addition: str) -> str:
		"""Merge two note fragments with GEDCOM line break semantics."""

		if not addition:
			return base
		if not base:
			return addition
		return f"{base}<br>\n{addition}"

	def _collect_source_note_segments(self, *events: Optional[Event]) -> List[str]:
		"""Collect source-derived note fragments from events."""

		segments: List[str] = []
		for event in events:
			if not event:
				continue
			note_fragment = getattr(event, "source_notes", "")
			if note_fragment:
				segments.append(note_fragment)
		return segments

	def _apply_default_source(self, source_text: str) -> str:
		"""Apply default source fallback when configured."""

		text = self._strip_spaces(source_text)
		if not text and self.default_source:
			return self.default_source
		return text

	def _parse_source_record(self, record: GedcomRecord) -> Source:
		"""Parse source record"""
		source = Source(source_id=record.xref_id or "")

		titl_record = self._find_sub_record(record, "TITL")
		if titl_record:
			source.title = self._rebuild_text(titl_record)

		auth_record = self._find_sub_record(record, "AUTH")
		if auth_record:
			source.author = self._rebuild_text(auth_record)

		publ_record = self._find_sub_record(record, "PUBL")
		if publ_record:
			source.publication = self._rebuild_text(publ_record)

		return source
