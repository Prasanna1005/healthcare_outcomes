"""generate_all.py — synthetic FHIR-equivalent healthcare data."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from generate_patients   import generate_patients
from generate_encounters import generate_encounters
from generate_clinical   import generate_observations, generate_conditions, generate_medications, generate_procedures


OUT = Path(__file__).resolve().parent.parent / "synthetic_data"
OUT.mkdir(exist_ok=True)


def main():
    seed         = int(os.getenv("DATA_RANDOM_SEED", "42"))
    n_patients   = int(os.getenv("DATA_NUM_PATIENTS", "100000"))
    n_encounters = int(os.getenv("DATA_NUM_ENCOUNTERS", "800000"))
    n_obs        = int(os.getenv("DATA_NUM_OBSERVATIONS", "5000000"))
    n_conditions = int(os.getenv("DATA_NUM_CONDITIONS", "400000"))
    n_meds       = int(os.getenv("DATA_NUM_MEDICATIONS", "600000"))

    print(f"=== healthcare data generation ===")
    print(f"  seed         = {seed}")
    print(f"  patients     = {n_patients:,}")
    print(f"  encounters   = {n_encounters:,}")
    print(f"  observations = {n_obs:,}")
    print(f"  conditions   = {n_conditions:,}")
    print(f"  medications  = {n_meds:,}\n")

    patients   = generate_patients(out_dir=OUT, n=n_patients, seed=seed)
    encounters = generate_encounters(out_dir=OUT, n=n_encounters, patients_df=patients, seed=seed)
    generate_observations(out_dir=OUT, n=n_obs, encounters_df=encounters, seed=seed)
    generate_conditions(out_dir=OUT, n=n_conditions, encounters_df=encounters, seed=seed)
    generate_medications(out_dir=OUT, n=n_meds, encounters_df=encounters, seed=seed)
    generate_procedures(out_dir=OUT, n=int(n_encounters * 0.4), encounters_df=encounters, seed=seed)

    print("\n=== generation complete ===")
    print("next: python /workspace/data_generator/load_to_snowflake.py")


if __name__ == "__main__":
    main()
