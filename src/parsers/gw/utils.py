import re
from typing import List, Optional, Tuple


NAME_NUM_RE = re.compile(r"^(.+?)\.(\d+)$")


def parse_name_token(token_list: List[str]) -> Tuple[str, str, Optional[int], List[str]]:
    """Split a GeneWeb token list into name components and remaining tokens."""

    if not token_list:
        raise ValueError("Empty person token list")

    sequences: List[Tuple[int, List[str]]] = []
    current: List[str] = []
    current_start = 0

    for idx, token in enumerate(token_list):
        if _is_name_token(token):
            if not current:
                current_start = idx
            current.append(token)
        else:
            if current:
                sequences.append((current_start, current.copy()))
                current = []
    if current:
        sequences.append((current_start, current.copy()))

    chosen_start: Optional[int] = None
    chosen_tokens: List[str] = []

    if sequences:
        chosen_start, chosen_tokens = max(sequences, key=lambda item: (len(item[1]), -item[0]))
    else:
        # Fallback to the first non-option token.
        for idx, token in enumerate(token_list):
            if token and not token.startswith("#") and not token.isdigit():
                chosen_start = idx
                chosen_tokens = [token]
                break
        if not chosen_tokens:
            chosen_start = 0
            chosen_tokens = [token_list[0]]

    chosen_start = chosen_start or 0
    chosen_end = chosen_start + len(chosen_tokens)
    remainder = token_list[:chosen_start] + token_list[chosen_end:]

    last = chosen_tokens[0]
    given_tokens = chosen_tokens[1:]
    number: Optional[int] = None

    if given_tokens:
        # Inspect the last given token for numbering (e.g. Jean.1)
        given_tokens[-1], number = _split_number(given_tokens[-1])
    else:
        # No explicit given name provided, so treat the lone token as the given name placeholder.
        last, number = _split_number(last)

    first = " ".join(given_tokens) if given_tokens else "0"
    return last, first, number, remainder


def canonical_key_from_tokens(tokens: List[str]) -> str:
    last, first, number, _ = parse_name_token(tokens)
    if number is not None:
        return f"{last} {first}.{number}".strip()
    return f"{last} {first}".strip()


def _is_name_token(token: str) -> bool:
    if not token:
        return False
    if token.startswith("#"):
        return False
    if token.lower() in {"beg", "end"}:
        return False
    stripped = token.strip('"')
    stripped = stripped.lstrip('_')
    if not stripped:
        return False
    if stripped.isdigit():
        return False
    if "," in stripped:
        return False
    lead = stripped[0]
    return lead.isalpha() or lead in {'"', "'"}


def _split_number(token: str) -> Tuple[str, Optional[int]]:
    match = NAME_NUM_RE.match(token)
    if match:
        return match.group(1), int(match.group(2))
    return token, None
