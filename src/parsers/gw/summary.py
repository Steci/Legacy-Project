from .models import GWDatabase

def db_summary(db: GWDatabase) -> str:
    return "\n".join([
        f"Families: {len(db.families)}",
        f"Persons (indexed): {len(db.persons)}",
        f"Notes blocks: {len(db.notes)}",
        f"Relations blocks: {len(db.relations)}"
    ])
