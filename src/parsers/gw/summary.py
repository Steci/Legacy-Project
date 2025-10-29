from .models import GWDatabase


def db_summary(db: GWDatabase) -> str:
    lines = [
        f"Families: {len(db.families)}",
        f"Persons (indexed): {len(db.persons)}",
        f"Notes blocks: {len(db.notes)}",
        f"Relations blocks: {len(db.relations)}",
    ]

    if getattr(db, "consanguinity_errors", None):
        lines.append(f"Consanguinity errors: {len(db.consanguinity_errors)}")
    if getattr(db, "consanguinity_warnings", None):
        lines.append(f"Consanguinity warnings: {len(db.consanguinity_warnings)}")

    return "\n".join(lines)
