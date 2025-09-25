import re
from typing import List, Optional, Tuple

NAME_NUM_RE = re.compile(r"^([^\s]+)\s+([^\s]+?)(?:\.(\d+))?$")

def parse_name_token(token_list: List[str]) -> Tuple[str, str, Optional[int], List[str]]:
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
    return f"{last} {first}.{number}" if number is not None else f"{last} {first}"
