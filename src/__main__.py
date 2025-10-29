from .db.driver import DatabaseDriver
from .parsers.gw.parser import GWParser
from .parsers.gw.summary import db_summary
from .models.family.family import Family, RelationKind
from .models.person.person import Person

def main():
    gw_path = "examples_files/galichet_ref.gw"
    db_path = "data/legacy.db"

    # Initialise la DB
    driver = DatabaseDriver(db_path)
    driver.open()

    # Parse le fichier GW
    parser = GWParser()
    db_data = parser.parse_file(gw_path)

    print("=== RAW PARSED DATA ===")
    print("Families:", db_data.families)
    print("Persons:", db_data.persons)
    print("Notes:", getattr(db_data, "notes", []))
    print("Relations:", getattr(db_data, "relations", []))

    driver.close()

    driver.open()
    print("")
    print("=== Database Summary ===")
    print(db_summary(db_data))
    driver.close()


if __name__ == "__main__":
    main()
