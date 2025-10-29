from .loader import load_geneweb_file
from .summary import db_summary

def main():
    gw_path = "examples_files/example.gw"
    db = load_geneweb_file(gw_path)
    print(db_summary(db))

    if db.consanguinity_errors:
        print("Consanguinity errors:")
        for entry in db.consanguinity_errors:
            print(f"  - {entry}")

    if db.consanguinity_warnings:
        print("Consanguinity warnings:")
        for entry in db.consanguinity_warnings:
            print(f"  - {entry}")

    for f in db.families:
        print(f)
        for g in f.children:
            print("  child:", g[1])
    for n in db.notes:
        print("NOTE for", n.person_key, ":", n.text[:40])
    for r in db.relations:
        print("REL for", r.person_key, "lines:", r.lines)

if __name__ == "__main__":
    main()
