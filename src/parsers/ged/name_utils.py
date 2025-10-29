"""GEDCOM name parsing helpers targeting the new domain models."""

from dataclasses import dataclass
import re
from typing import Dict


@dataclass
class ParsedName:
    """Parsed GEDCOM name components."""

    first_name: str = "x"
    surname: str = "?"
    suffix: str = ""
    nickname: str = ""
    title: str = ""


class NameParsingUtils:
    """Utility class for parsing GEDCOM names and handling name formatting."""

    NAME_PATTERN = re.compile(r"^([^/]*?)/?([^/]*?)/?([^/]*)$")

    @staticmethod
    def parse_gedcom_name(name_value: str) -> ParsedName:
        """Parse GEDCOM name format ``First /Surname/`` into structured parts."""

        if not name_value:
            return ParsedName()

        name_value = name_value.strip()
        match = NameParsingUtils.NAME_PATTERN.match(name_value)

        if match:
            given = match.group(1).strip() if match.group(1) else ""
            surname = match.group(2).strip() if match.group(2) else ""
            suffix = match.group(3).strip() if match.group(3) else ""

            if "/" not in name_value:
                given = name_value.strip()
                surname = ""
        else:
            given = name_value.strip()
            surname = ""
            suffix = ""

        first_name = NameParsingUtils._process_first_name(given)
        surname = NameParsingUtils._process_surname(surname)

        return ParsedName(first_name=first_name, surname=surname or "?", suffix=suffix)

    @staticmethod
    def _process_first_name(given: str) -> str:
        given = (given or "").strip()
        return given if given else "x"

    @staticmethod
    def _process_surname(surname: str) -> str:
        return (surname or "").strip()

    @staticmethod
    def capitalize_name(name: str) -> str:
        if not name:
            return name
        return " ".join(word.capitalize() for word in name.split())

    @staticmethod
    def extract_name_components(full_name: str) -> Dict[str, str]:
        components: Dict[str, str] = {"given": "", "surname": "", "suffix": "", "title": "", "nickname": ""}

        if not full_name:
            return components

        title_patterns = [r"^(Mr\.?|Mrs\.?|Dr\.?|Prof\.?)\s+", r"^(Sir|Lady|Lord|Dame)\s+"]
        for pattern in title_patterns:
            match = re.match(pattern, full_name, re.IGNORECASE)
            if match:
                components["title"] = match.group(1)
                full_name = full_name[match.end():].strip()
                break

        nickname_match = re.search(r'"([^"]+)"|\(([^)]+)\)', full_name)
        if nickname_match:
            components["nickname"] = nickname_match.group(1) or nickname_match.group(2)
            full_name = re.sub(r'"([^"]+)"|\(([^)]+)\)', "", full_name).strip()

        parsed = NameParsingUtils.parse_gedcom_name(full_name)
        components["given"] = parsed.first_name
        components["surname"] = parsed.surname
        components["suffix"] = parsed.suffix
        return components

    @staticmethod
    def format_name_for_display(name: ParsedName, format_style: str = "default") -> str:
        if not name:
            return ""

        if format_style == "surname_first":
            if name.surname and name.first_name != "x":
                return f"{name.surname}, {name.first_name}"
            if name.surname:
                return name.surname
            if name.first_name != "x":
                return name.first_name
            return ""

        if format_style == "formal":
            parts = []
            if name.first_name and name.first_name != "x":
                parts.append(name.first_name)
            if name.surname:
                parts.append(name.surname)
            if name.suffix:
                parts.append(name.suffix)
            return " ".join(parts)

        if name.first_name == "x" and name.surname:
            return name.surname
        if name.first_name != "x" and name.surname:
            return f"{name.first_name} {name.surname}"
        if name.first_name != "x":
            return name.first_name
        return name.surname or ""

    @staticmethod
    def validate_name(name: ParsedName) -> bool:
        if not name:
            return False
        return bool((name.first_name and name.first_name != "x") or name.surname or name.suffix)

    @staticmethod
    def normalize_name_for_search(name: ParsedName) -> str:
        if not name:
            return ""
        parts = []
        if name.first_name and name.first_name != "x":
            parts.append(name.first_name.lower().strip())
        if name.surname:
            parts.append(name.surname.lower().strip())
        return " ".join(parts)
