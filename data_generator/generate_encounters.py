"""generate_encounters.py — synthetic FHIR Encounter."""

import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm


CLASSES = ["outpatient", "ambulatory", "emergency", "inpatient"]
CLASS_PROBS = [0.45, 0.25, 0.15, 0.15]

# Common ICD-10 codes for diagnosis
ICD_CODES = [
    ("I10",      "Essential hypertension"),
    ("E11.9",    "Type 2 diabetes mellitus without complications"),
    ("J45.909",  "Asthma, unspecified"),
    ("M25.50",   "Joint pain"),
    ("R51",      "Headache"),
    ("J06.9",    "Acute upper respiratory infection"),
    ("K21.9",    "Gastro-esophageal reflux disease"),
    ("F41.9",    "Anxiety disorder, unspecified"),
    ("F32.9",    "Major depressive disorder"),
    ("N39.0",    "Urinary tract infection"),
    ("R10.9",    "Abdominal pain"),
    ("M54.5",    "Low back pain"),
    ("E78.5",    "Hyperlipidemia"),
    ("Z00.00",   "Encounter for general adult medical exam"),
    ("Z23",      "Encounter for immunisation"),
    ("I25.10",   "Atherosclerotic heart disease"),
    ("J44.9",    "Chronic obstructive pulmonary disease"),
    ("N18.9",    "Chronic kidney disease, unspecified"),
    ("C50.911",  "Malignant neoplasm of breast"),
    ("I63.9",    "Cerebral infarction"),
]

DEPARTMENTS_BY_CLASS = {
    "outpatient": ["Family Medicine", "Internal Medicine", "Pediatrics", "Cardiology",
                   "Endocrinology", "Dermatology", "Orthopedics"],
    "ambulatory": ["Surgery Center", "Pain Clinic", "Imaging", "Lab Services"],
    "emergency":  ["Emergency Department"],
    "inpatient":  ["Med-Surg", "ICU", "CCU", "Telemetry", "Maternity", "Pediatric Ward"],
}

DISPOSITIONS = ["home", "skilled_nursing", "rehab", "expired", "ama", "transferred"]
DISPOSITION_PROBS = [0.78, 0.08, 0.05, 0.02, 0.02, 0.05]


def generate_encounters(out_dir, n, patients_df, seed=42):
    rng = np.random.default_rng(seed + 1)

    patient_ids = patients_df["patient_id"].to_numpy()
    today    = datetime(2025, 12, 31)
    earliest = datetime(2024, 1, 1)

    rows = []
    for _ in tqdm(range(n), unit="encounters", ncols=80, desc="encounters"):
        cls = str(rng.choice(CLASSES, p=CLASS_PROBS))
        # LOS depends on class
        los_hours = {
            "outpatient": float(rng.uniform(0.5, 2.0)),
            "ambulatory": float(rng.uniform(1.0, 6.0)),
            "emergency":  float(rng.uniform(2.0, 24.0)),
            "inpatient":  float(rng.exponential(72.0) + 24.0),
        }[cls]

        seconds_offset = int(rng.integers(0, int((today - earliest).total_seconds())))
        admit = earliest + timedelta(seconds=seconds_offset)
        discharge = admit + timedelta(hours=los_hours)

        diag_code, diag_text = ICD_CODES[int(rng.integers(0, len(ICD_CODES)))]
        # Charges: heavily class-dependent + skewed
        charge_base = {
            "outpatient": 250, "ambulatory": 800,
            "emergency": 1800, "inpatient": 12000
        }[cls]
        charges = round(float(rng.lognormal(np.log(charge_base), 0.6)), 2)

        rows.append({
            "encounter_id":           uuid.uuid4().hex,
            "patient_id":             str(rng.choice(patient_ids)),
            "encounter_class":        cls,
            "encounter_type":         f"{cls}_visit",
            "admission_timestamp":    admit.isoformat(),
            "discharge_timestamp":    discharge.isoformat(),
            "length_of_stay_hours":   round(los_hours, 2),
            "department":             str(rng.choice(DEPARTMENTS_BY_CLASS[cls])),
            "primary_diagnosis_code": diag_code,
            "primary_diagnosis_text": diag_text,
            "discharge_disposition":  str(rng.choice(DISPOSITIONS, p=DISPOSITION_PROBS)),
            "is_readmission_30d":     bool(rng.random() < 0.12),
            "total_charges":          charges,
            "created_at":             admit.isoformat(),
            "updated_at":             discharge.isoformat(),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_encounters.csv", index=False)
    print(f"  ✓ raw_encounters.csv    {len(df):,}")
    return df
