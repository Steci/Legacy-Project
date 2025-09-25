import re
from typing import Optional
from .models import GWDatabase, Family, Person, NoteBlock, RelationBlock
from .utils import parse_name_token, canonical_key_from_tokens

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
            if len(rest) >= 4:
                fam.husband = canonical_key_from_tokens(rest[0:2])
                fam.wife = canonical_key_from_tokens(rest[-2:])
            else:
                fam.husband = " ".join(rest)
        else:
            h_tokens = rest[:plus_idx]
            after_plus = rest[plus_idx+1:]
            if len(after_plus) >= 2:
                fam.husband = canonical_key_from_tokens(h_tokens)
                fam.wife = canonical_key_from_tokens(after_plus[-2:])
                if after_plus and re.match(r"[~\?\<\>\d0]", after_plus[0]):
                    fam.wedding_date = after_plus[0]
                fam.options = [t for t in rest if t.startswith("#") or t in ("-", "#eng")]

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
        if parts and parts[0] in ("h", "f"):
            gender, parts = parts[0], parts[1:]
        last, first, number, remaining = parse_name_token(parts)
        p = Person(f"{last} {first}", last, first, number, remaining)
        self.db.persons.setdefault(p.key(), p)
        return (gender, p, remaining)

    def _parse_notes_block(self, i: int, lines: list, toks: list) -> int:
        person_key = canonical_key_from_tokens(toks[1:])
        i += 1
        if i < len(lines) and lines[i].strip().lower() == "beg":
            i += 1
        note_lines = []
        while i < len(lines):
            line = lines[i].strip()
            if line.lower() == "end":
                self.db.notes.append(
                    NoteBlock(person_key, "\n".join(note_lines).strip())
                )
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
