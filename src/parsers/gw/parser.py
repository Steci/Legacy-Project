import re
from typing import Optional
from .models import GWDatabase, Family, Person, NoteBlock, RelationBlock, EventLine
from .utils import parse_name_token, canonical_key_from_tokens


def _strip_option_values(tokens: list) -> list:
    filtered = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token.startswith("#"):
            skip_next = True
            continue
        if token.startswith("+"):
            continue
        filtered.append(token)
    return filtered


class GWParser:
    def __init__(self, debug: bool = False):
        self.db = GWDatabase()
        self.debug = debug

    def parse_file(self, path: str) -> GWDatabase:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return self.parse_text(f.read())

    def parse_text(self, text: str) -> GWDatabase:
        lines = text.splitlines()
        i = 0
        current_family: Optional[Family] = None

        while i < len(lines):
            raw = lines[i].strip()
            if not raw or raw.startswith("//") or raw.startswith("#!"):
                i += 1
                continue

            toks = raw.split()
            first = toks[0].lower()

            # --- FAMILIES ---
            if first == "fam":
                current_family = self._parse_family_line(raw, toks)
                self.db.families.append(current_family)
                i += 1
                continue

            if first == "fevt" and current_family:
                current_family.raw.append(raw)
                i = self._parse_family_events_block(i, lines, current_family)
                continue

            if first == "src" and current_family:
                current_family.src = raw[len("src"):].strip()
                current_family.raw.append(raw)
                i += 1
                continue

            if first == "comm" and current_family:
                current_family.comm = raw[len("comm"):].strip()
                current_family.raw.append(raw)
                i += 1
                continue

            if raw.startswith("wit:") and current_family:
                current_family.witnesses.append(raw[len("wit:"):].strip())
                current_family.raw.append(raw)
                i += 1
                continue

            # --- CHILDREN ---
            if first == "beg":
                i = self._parse_children_block(i, lines, current_family)
                continue

            # --- NOTES ---
            if first == "notes":
                i = self._parse_notes_block(i, lines, toks)
                continue

            # --- RELATIONS ---
            if first == "rel":
                i = self._parse_relations_block(i, lines, toks)
                continue

            if first == "pevt":
                i = self._parse_person_events_block(i, lines, toks)
                continue

            # --- PERSONS (inline) ---
            self._maybe_add_person(raw)
            i += 1

        return self.db

    # -------------------------
    # Helpers for parsing blocks
    # -------------------------
    def _parse_family_line(self, raw: str, toks: list) -> Family:
        fam = Family()
        fam.raw.append(raw)
        rest = toks[1:]

        try:
            plus_idx = rest.index("+")
        except ValueError:
            plus_idx = None
            for idx, t in enumerate(rest):
                if t.startswith("+"):
                    plus_idx = idx
                    break

        if plus_idx is None:
            if len(rest) >= 2:
                fam.husband = canonical_key_from_tokens(_strip_option_values(rest[:2]))
                fam.wife = canonical_key_from_tokens(_strip_option_values(rest[-2:]))
            else:
                fam.husband = " ".join(rest)
        else:
            h_tokens = rest[:plus_idx]
            after_plus = rest[plus_idx + 1:]
            if h_tokens:
                filtered_h = _strip_option_values(h_tokens)
                fam.husband = canonical_key_from_tokens(filtered_h) if filtered_h else " ".join(h_tokens)
            if after_plus:
                filtered_w = _strip_option_values(after_plus)
                fam.wife = canonical_key_from_tokens(filtered_w) if filtered_w else "0"
                if after_plus and re.match(r"[~\?<\>\d0]", after_plus[0]):
                    fam.wedding_date = after_plus[0]

        return fam

    def _parse_children_block(self, i: int, lines: list, current_family: Family) -> int:
        i += 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.lower() == "end":
                return i + 1
            if line.startswith("-"):
                gender, p, remaining = self._parse_child_line(line, current_family)
                current_family.children.append((gender, p, remaining))
                current_family.raw.append(line)
            else:
                current_family.raw.append(line)
            i += 1
        return i


    def _parse_child_line(self, line: str, family: Family):
        parts = line[1:].strip().split()
        gender = None
        if parts and parts[0] in ("h", "f", "u"):
            gender, parts = parts[0], parts[1:]

        filtered = _strip_option_values(parts)
        last, first, number, remaining = parse_name_token(filtered)
        surname_hint = self._family_surname_hint(family)

        if first == "0" and surname_hint:
            # Assume the lone token represents a given name and borrow the family surname.
            first = last
            last = surname_hint

        person = Person(f"{last} {first}".strip(), last, first, number, remaining)
        existing = self.db.persons.setdefault(person.key(), person)
        return (gender, existing, remaining)

    def _parse_notes_block(self, i: int, lines: list, toks: list) -> int:
        person_key = canonical_key_from_tokens(toks[1:])
        i += 1
        if i < len(lines) and lines[i].strip().lower() == "beg":
            i += 1
        note_lines = []
        while i < len(lines):
            line = lines[i].strip()
            if line.lower().startswith("end"):
                text = "\n".join(note_lines).strip()
                self.db.notes.append(NoteBlock(person_key, text))
                return i + 1
            note_lines.append(line)
            i += 1
        return i

    def _parse_relations_block(self, i: int, lines: list, toks: list) -> int:
        person_key = canonical_key_from_tokens(toks[1:])
        i += 1
        if i < len(lines) and lines[i].strip().lower() == "beg":
            i += 1
        rel_lines = []
        while i < len(lines):
            if lines[i].strip().lower() == "end":
                self.db.relations.append(RelationBlock(person_key, rel_lines))
                return i + 1
            rel_lines.append(lines[i])
            i += 1
        return i

    def _parse_family_events_block(self, i: int, lines: list, family: Family) -> int:
        i += 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.lower() == "end fevt":
                family.raw.append(line)
                return i + 1
            family.raw.append(line)
            event_line = self._parse_event_line(line)
            if event_line:
                family.events.append(event_line)
            i += 1
        return i

    def _parse_event_line(self, raw: str) -> Optional[EventLine]:
        tokens = raw.split()
        if not tokens:
            return None
        tag_token = tokens[0]
        tag = tag_token.lstrip('#').lower()
        return EventLine(raw=raw, tag=tag, tokens=tokens[1:])

    def _parse_person_events_block(self, i: int, lines: list, toks: list) -> int:
        person_tokens = toks[1:]
        if not person_tokens:
            return i + 1
        last, first, number, remaining = parse_name_token(person_tokens)
        key = canonical_key_from_tokens(person_tokens)
        person = self.db.persons.get(key)
        if not person:
            raw_name = f"{last} {first}".strip()
            person = Person(raw_name, last, first, number, remaining)
            self.db.persons[key] = person
        i += 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.lower() == "end pevt":
                return i + 1
            event_line = self._parse_event_line(line)
            if event_line:
                person.events.append(event_line)
            i += 1
        return i

    def _family_surname_hint(self, family: Optional[Family]) -> Optional[str]:
        if not family:
            return None
        for candidate in (family.husband, family.wife):
            if not candidate:
                continue
            parts = candidate.split()
            if parts:
                return parts[0]
        return None

    def _maybe_add_person(self, raw: str):
        toks = raw.split()
        if len(toks) < 2:
            return
        if any(re.match(r"^[~\?\<\>\d0].*", t) for t in toks[2:]):
            try:
                last, first, number, remaining = parse_name_token(toks)
                p = Person(f"{last} {first}", last, first, number, remaining)
                self.db.persons[p.key()] = p
            except Exception:
                pass
