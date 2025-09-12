# family/params.py

from enum import Enum

class RelationKind(Enum):
    MARRIED = "married"
    NOT_MARRIED = "not_married"
    PACS = "pacs"
    ENGAGED = "engaged"
    SEPARATED = "separated"
    DIVORCED = "divorced"
    UNKNOWN = "unknown"
