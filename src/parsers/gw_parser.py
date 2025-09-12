"""
GW (GeneWeb) file parser
Author: ChatGPT (example)
Relies on GeneWeb GW format documentation:
  - GeneWeb - The GW format. :contentReference[oaicite:1]{index=1}

This parser focuses on extracting:
 - families (fam lines + children block)
 - persons (inline person data and child lines)
 - notes (notes ... end)
 - relations (rel ... end)

It intentionally keeps many fields as "raw" tokens (tags like #bp, #dp, etc.)
so you can extend parsing rules for any tag you need.

Usage:
  from gw_parser import GWParser
  p = GWParser().parse_file("yourfile.gw")
  print(p.families, p.person_index)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple

@dataclass
class Person:
    raw_name: str
    last: str
    first: str
    number: Optional[int] = None
    tokens: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        """Canonical key to identify person in GW: Last First[.Number]"""
        if self.number is not None:
            return f"{self.last} {self.first}.{self.number}"
        return f"{self.last} {self.first}"

    def __repr__(self):
        return f"Person({self.key()}, tokens={self.tokens})"

@dataclass
class Family:
    husband: Optional[str] = None
    wife: Optional[str] = None
    wedding_date: Optional[str] = None
    options: List[str] = field(default_factory=list)
    src: Optional[str] = None
    comm: Optional[str] = None
    witnesses: List[str] = field(default_factory=list)
    children: List[Tuple[Optional[str], Person, List[str]]] = field(default_factory=list)
    raw: List[str] = field(default_factory=list)

    def __repr__(self):
        return (f"Family(husband={self.husband}, wife={self.wife}, "
                f"children={len(self.children)}, options={self.options})")

@dataclass
class NoteBlock:
    person_key: str
    text: str

@dataclass
class RelationBlock:
    person_key: str
    lines: List[str]

@dataclass
class GWDatabase:
    families: List[Family] = field(default_factory=list)
    persons: Dict[str, Person] = field(default_factory=dict)  # keyed by canonical key
    notes: List[NoteBlock] = field(default_factory=list)
    relations: List[RelationBlock] = field(default_factory=list)

NAME_NUM_RE = re.compile(r"^([^\s]+)\s+([^\s]+?)(?:\.(\d+))?$")
PERSON_LINE_SPLIT = re.compile(r"\s+")

def parse_name_token(token_list: List[str]) -> Tuple[str, str, Optional[int], List[str]]:
    """
    Given tokens starting with LastName FirstName[.Number] ... -> returns
    last, first, number, remaining tokens
    """
    if not token_list:
        raise ValueError("Empty person token list")
    last = token_list[0]
    first_raw = token_list[1] if len(token_list) > 1 else "0"
    number = None
    m = re.match(r"^(.+?)\.(\d+)$", first_raw)
    if m:
        first = m.group(1)
        number = int(m.group(2))
    else:
        first = first_raw
    remaining = token_list[2:] if len(token_list) > 2 else []
    return last, first, number, remaining

def canonical_key_from_tokens(tokens: List[str]) -> str:
    last, first, number, _ = parse_name_token(tokens)
    if number is not None:
        return f"{last} {first}.{number}"
    return f"{last} {first}"

class GWParser:
    def __init__(self, debug: bool = False):
        self.db = GWDatabase()
        self.debug = debug

    def parse_file(self, path: str) -> GWDatabase:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return self.parse_text(text)

    def parse_text(self, text: str) -> GWDatabase:
        lines = text.splitlines()
        i = 0
        current_family: Optional[Family] = None

        while i < len(lines):
            raw = lines[i].strip()
            if not raw or raw.startswith("//") or raw.startswith("#!"):  # skip blank/comments
                i += 1
                continue

            toks = raw.split()
            first = toks[0].lower()

            if first == "fam":
                current_family = Family()
                current_family.raw.append(raw)
                rest = toks[1:]
                try:
                    plus_idx = rest.index("+")
                except ValueError:
                    plus_idx = None
                    for idx, t in enumerate(rest):
                        if t == "+" or t.startswith("+"):
                            plus_idx = idx
                            break
                if plus_idx is None:
                    if len(rest) >= 4:
                        h_tokens = rest[0:2]
                        w_tokens = rest[-2:]
                        current_family.husband = canonical_key_from_tokens(h_tokens)
                        current_family.wife = canonical_key_from_tokens(w_tokens)
                    else:
                        current_family.husband = " ".join(rest)
                else:
                    h_tokens = rest[:plus_idx]
                    after_plus = rest[plus_idx+1:]
                    if len(after_plus) >= 2:
                        w_tokens = after_plus[-2:]
                        current_family.husband = canonical_key_from_tokens(h_tokens)
                        current_family.wife = canonical_key_from_tokens(w_tokens)
                        if after_plus and re.match(r"[~\?\<\>\d0]", after_plus[0]):
                            current_family.wedding_date = after_plus[0]
                        current_family.options = [t for t in rest if t.startswith("#") or t == "-" or t == "#eng"]
                self.db.families.append(current_family)
                i += 1
                continue

            if first == "src" and current_family is not None:
                current_family.src = raw[len("src"):].strip()
                current_family.raw.append(raw)
                i += 1
                continue

            if first == "comm" and current_family is not None:
                current_family.comm = raw[len("comm"):].strip()
                current_family.raw.append(raw)
                i += 1
                continue

            if raw.startswith("wit:") and current_family is not None:
                rest = raw[len("wit:"):].strip()
                current_family.witnesses.append(rest)
                current_family.raw.append(raw)
                i += 1
                continue

            if first == "beg":
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    if line.lower() == "end":
                        i += 1
                        break
                    if line.startswith("-"):
                        sub = line[1:].strip()
                        parts = sub.split()
                        gender = None
                        if parts and parts[0] in ("h", "f"):
                            gender = parts[0]
                            parts = parts[1:]
                        try:
                            last, first, number, remaining = parse_name_token(parts)
                        except Exception:
                            last = parts[0] if parts else ""
                            first = parts[1] if len(parts) > 1 else "0"
                            number = None
                            remaining = parts[2:] if len(parts) > 2 else []
                        p = Person(raw_name=f"{last} {first}", last=last, first=first, number=number, tokens=remaining)
                        key = p.key()
                        if key not in self.db.persons:
                            self.db.persons[key] = p
                        if current_family is not None:
                            current_family.children.append((gender, p, remaining))
                            current_family.raw.append(line)
                        i += 1
                        continue
                    else:
                        if current_family:
                            current_family.raw.append(line)
                        i += 1
                continue

            if first == "notes":
                note_tokens = toks[1:]
                person_key = canonical_key_from_tokens(note_tokens)
                i += 1
                note_lines = []
                if i < len(lines) and lines[i].strip().lower() == "beg":
                    i += 1
                while i < len(lines):
                    line = lines[i]
                    if line.strip().lower() == "end":
                        i += 1
                        break
                    note_lines.append(line)
                    i += 1
                note_text = "\n".join(note_lines).strip()
                self.db.notes.append(NoteBlock(person_key=person_key, text=note_text))
                continue

            if first == "rel":
                rel_tokens = toks[1:]
                person_key = canonical_key_from_tokens(rel_tokens)
                i += 1
                if i < len(lines) and lines[i].strip().lower() == "beg":
                    i += 1
                rel_lines = []
                while i < len(lines):
                    if lines[i].strip().lower() == "end":
                        i += 1
                        break
                    rel_lines.append(lines[i])
                    i += 1
                self.db.relations.append(RelationBlock(person_key=person_key, lines=rel_lines))
                continue

            maybe_person_tokens = raw.split()
            if len(maybe_person_tokens) >= 2:
                if any(re.match(r"^[~\?\<\>\d0].*", t) for t in maybe_person_tokens[2:]):
                    try:
                        last, first, number, remaining = parse_name_token(maybe_person_tokens)
                        p = Person(raw_name=f"{last} {first}", last=last, first=first, number=number, tokens=remaining)
                        self.db.persons[p.key()] = p
                    except Exception:
                        pass
            i += 1

        return self.db

def db_summary(db: GWDatabase) -> str:
    lines = []
    lines.append(f"Families: {len(db.families)}")
    lines.append(f"Persons (indexed): {len(db.persons)}")
    lines.append(f"Notes blocks: {len(db.notes)}")
    lines.append(f"Relations blocks: {len(db.relations)}")
    return "\n".join(lines)


if __name__ == "__main__":
    gw_path = "examples_files/example.gw"

    parser = GWParser()
    db = parser.parse_file(gw_path)
    print(db_summary(db))
    for f in db.families:
        print(f)
        for g in f.children:
            print("  child:", g[1])
    for n in db.notes:
        print("NOTE for", n.person_key, ":", n.text[:40])
    for r in db.relations:
        print("REL for", r.person_key, "lines:", r.lines)
