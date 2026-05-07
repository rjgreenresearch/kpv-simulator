from pathlib import Path
from kpv.domains.leadership_osint.pipelines.update_country import update_country


import os
print("CWD:", os.getcwd())


def main():
    data_root = Path(__file__).resolve().parent / "kvp_data"
    print("Using data_root:", data_root)
    result = update_country("cn", str(data_root))

    print("\n=== UPDATED DATASET ===")
    print(result["updated_dataset"])

    print("\n=== DIFF ===")
    print(result["diff"])

    print("\nSnapshot written to:", result["snapshot_path"])
    print("Diff written to:", result["diff_path"])

if __name__ == "__main__":
    main()
