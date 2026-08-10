"""
Main Orchestrator script for the Real-Time Dynamic Price Optimization Engine dataset pipeline.
Usage: python generate_dataset.py
"""
import sys
import time
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    SQLITE_CACHE_PATH,
    CHECKPOINT_PATH,
    PARQUET_OUTPUT_PATH,
    CSV_OUTPUT_PATH,
    METADATA_PATH,
    VALIDATION_REPORT_PATH,
    REJECTED_ROWS_PATH,
    DATA_QUALITY_REPORT_PATH,
    DATA_DICTIONARY_PATH,
    README_PATH
)
from src.batch_generator import generate_full_dataset, load_checkpoint
from src.validator import run_data_validation
from src.report_generator import (
    generate_metadata_json,
    generate_data_dictionary,
    generate_quality_report_md,
    generate_readme_md
)

def cleanup_temporary_files():
    """
    Cleans up intermediate cache and checkpoint files to preserve disk space on laptop.
    Leaves only the 8 final deliverable files.
    """
    import gc
    gc.collect()
    print("\n[Cleanup] Auto-cleaning intermediate temporary files...")
    temp_files = [SQLITE_CACHE_PATH, CHECKPOINT_PATH]
    for p in temp_files:
        if p.exists():
            try:
                os.remove(p)
                print(f"  Removed: {p.name}")
            except Exception as e:
                print(f"  Could not remove {p.name}: {e}")

def main():
    start_time = time.time()
    print("================================================================================")
    print("        REAL-TIME DYNAMIC PRICE OPTIMIZATION ENGINE — DATASET PIPELINE          ")
    print("================================================================================")

    # Completion guard: exit cleanly if already generated unless --force is passed
    force_run = "--force" in sys.argv
    if not force_run and PARQUET_OUTPUT_PATH.exists() and METADATA_PATH.exists() and CSV_OUTPUT_PATH.exists():
        import json
        with open(METADATA_PATH, "r") as f:
            meta = json.load(f)
        total_rows = meta.get("dataset_dimensions", {}).get("total_rows", "N/A")
        print(f"\n[Info] Dataset already complete! Found {total_rows:,} rows in {PARQUET_OUTPUT_PATH}.")
        print("  All 8 deliverables are verified on disk.")
        print("  To force a fresh re-generation, run: python generate_dataset.py --force\n")
        return

    # 1. Generate Full Dataset
    df = generate_full_dataset(force=force_run)

    # 2. Run Comprehensive Validation Suite
    validated_df, validation_report = run_data_validation(df)

    # 3. Generate Documentation and Metadata Deliverables
    print("\n[Reports] Generating documentation, schema metadata, and quality reports...")
    generate_metadata_json(validated_df, validation_report)
    generate_data_dictionary()
    generate_quality_report_md(validated_df, validation_report)
    generate_readme_md(validated_df)

    # 4. Perform Auto-cleanup of Temporary Artifacts
    cleanup_temporary_files()

    elapsed = time.time() - start_time
    print("\n================================================================================")
    print(f"  PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed/60:.2f} MINUTES")
    print("================================================================================")
    print("Deliverables Summary:")
    print(f"  1. {CSV_OUTPUT_PATH} ({os.path.getsize(CSV_OUTPUT_PATH)/(1024*1024):.2f} MB)")
    print(f"  2. {PARQUET_OUTPUT_PATH} ({os.path.getsize(PARQUET_OUTPUT_PATH)/(1024*1024):.2f} MB)")
    print(f"  3. {METADATA_PATH}")
    print(f"  4. {DATA_DICTIONARY_PATH}")
    print(f"  5. {VALIDATION_REPORT_PATH}")
    print(f"  6. {REJECTED_ROWS_PATH}")
    print(f"  7. {DATA_QUALITY_REPORT_PATH}")
    print(f"  8. {README_PATH}")
    print("================================================================================\n")

if __name__ == "__main__":
    main()
