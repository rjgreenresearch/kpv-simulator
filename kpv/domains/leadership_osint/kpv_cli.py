import argparse
import sys

from .pipelines.update_country import update_country
from .utils.logger import get_logger


def main():
    parser = argparse.ArgumentParser(
        prog="kpv",
        description="KPV Leadership OSINT Ingestion CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    # ------------------------------------------------------------
    # kpv update <country>
    # ------------------------------------------------------------
    update_parser = subparsers.add_parser(
        "update",
        help="Run ingestion + update pipeline for a country"
    )
    update_parser.add_argument(
        "country_code",
        type=str,
        help="Country code (cn, ru, ir, kp)"
    )
    update_parser.add_argument(
        "--data-root",
        type=str,
        default="./kpv_data",
        help="Root directory for KPV datasets"
    )

    args = parser.parse_args()

    if args.command == "update":
        logger = get_logger("KPV.CLI", args.data_root)
        logger.info(f"CLI invoked: update {args.country_code}")

        try:
            result = update_country(args.country_code, args.data_root)
            logger.info("Update completed successfully")
            print("Update completed successfully.")
            print(f"Snapshot: {result['snapshot_path']}")
            print(f"Diff: {result['diff_path']}")
        except Exception as e:
            logger.error(f"Update failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
