"""generate_clinical.py — observations, conditions, medications, procedures."""

import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm


# LOINC vital signs + common labs
VITALS = [
    ("8867-4",  "Heart rate",                "bpm",   60, 100),
    ("8480-6",  "Systolic blood pressure",   "mmHg",  100, 140),
    ("8462-4",  "Diastolic blood pressure",  "mmHg",  60, 90),
    ("8310-5",  "Body temperature",          "C",     36.1, 37.5),
    ("9279-1",  "Respiratory rate",          "/min",  12, 20),
    ("2708-6",  "Oxygen saturation",         "%",     95, 100),
]

LABS = [
    ("33747-0", "Glucose",                   "mg/dL", 70, 110),
    ("2160-0",  "Creatinine",                "mg/dL", 0.6, 1.3),
    ("2823-3",  "Potassium",                 "mEq/L", 3.5, 5.0),
    ("2951-2",  "Sodium",                    "mEq/L", 135, 145),
    ("718-7",   "Hemoglobin",                "g/dL",  12, 17),
    ("4544-3",  "Hematocrit",                "%",     36, 50),
    ("13457-7", "LDL cholesterol",           "mg/dL", 0, 100),
    ("2085-9",  "HDL cholesterol",           "mg/dL", 40, 80),
]

CONDITION_CODES = [
    ("I10",      "Essential hypertension",                 "active"),
    ("E11.9",    "Type 2 diabetes mellitus",                "active"),
    ("J45.909",  "Asthma",                                  "active"),
    ("E78.5",    "Hyperlipidemia",                          "active"),
    ("F41.9",    "Anxiety disorder",                        "active"),
    ("F32.9",    "Major depressive disorder",               "active"),
    ("M19.90",   "Osteoarthritis, unspecified",             "active"),
    ("J44.9",    "COPD",                                    "active"),
    ("N18.9",    "Chronic kidney disease",                  "active"),
    ("I25.10",   "Atherosclerotic heart disease",           "active"),
]

MEDICATIONS = [
    ("1551300",  "Metformin 500mg",        "500mg PO BID",                "oral"),
    ("314076",   "Lisinopril 10mg",        "10mg PO daily",               "oral"),
    ("197361",   "Atorvastatin 20mg",      "20mg PO daily",               "oral"),
    ("197517",   "Amlodipine 5mg",         "5mg PO daily",                "oral"),
    ("866513",   "Albuterol inhaler",      "2 puffs Q4H PRN",             "inhalation"),
    ("197361",   "Levothyroxine 50mcg",    "50mcg PO daily",              "oral"),
    ("310965",   "Sertraline 50mg",        "50mg PO daily",               "oral"),
    ("314231",   "Omeprazole 20mg",        "20mg PO daily",               "oral"),
    ("197535",   "Aspirin 81mg",           "81mg PO daily",               "oral"),
    ("198440",   "Ibuprofen 400mg",        "400mg PO Q6H PRN",            "oral"),
]

PROCEDURES = [
    ("99213", "Office visit, established patient, low complexity"),
    ("99214", "Office visit, established patient, moderate complexity"),
    ("36415", "Routine venipuncture"),
    ("85025", "Complete blood count with diff"),
    ("80053", "Comprehensive metabolic panel"),
    ("93000", "Electrocardiogram, complete"),
    ("71046", "Chest X-ray, 2 views"),
    ("76700", "Abdominal ultrasound, complete"),
    ("45378", "Colonoscopy, diagnostic"),
    ("47562", "Laparoscopic cholecystectomy"),
]


def _abnormal(value, low, high):
    if value < low * 0.7 or value > high * 1.3:  return "critical"
    if value < low      or value > high:         return "high" if value > high else "low"
    return "normal"


def generate_observations(out_dir, n, encounters_df, seed=42):
    rng = np.random.default_rng(seed + 2)
    enc_ids = encounters_df["encounter_id"].to_numpy()
    pat_ids = encounters_df["patient_id"].to_numpy()
    enc_admit = pd.to_datetime(encounters_df["admission_timestamp"]).to_numpy()

    rows = []
    print(f"  generating {n:,} observations …")
    for i in tqdm(range(n), unit="obs", ncols=80):
        eix = int(rng.integers(0, len(enc_ids)))
        is_vital = bool(rng.random() < 0.7)
        spec = VITALS[int(rng.integers(0, len(VITALS)))] if is_vital else \
               LABS[int(rng.integers(0, len(LABS)))]
        code, text, unit, lo, hi = spec
        # Generate value with realistic noise
        val = round(float(rng.uniform(lo - 0.2 * (hi - lo), hi + 0.2 * (hi - lo))), 2)
        # Time roughly within the encounter window
        ts = pd.Timestamp(enc_admit[eix]) + timedelta(minutes=int(rng.integers(0, 1440)))
        rows.append({
            "observation_id":      uuid.uuid4().hex,
            "patient_id":          str(pat_ids[eix]),
            "encounter_id":        str(enc_ids[eix]),
            "observation_type":    "vital" if is_vital else "lab",
            "code":                code,
            "code_text":           text,
            "value":               val,
            "unit":                unit,
            "observation_timestamp": ts.isoformat(),
            "abnormal_flag":       _abnormal(val, lo, hi),
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_observations.csv", index=False)
    print(f"  ✓ raw_observations.csv  {len(df):,}")


def generate_conditions(out_dir, n, encounters_df, seed=42):
    rng = np.random.default_rng(seed + 3)
    enc_ids = encounters_df["encounter_id"].to_numpy()
    pat_ids = encounters_df["patient_id"].to_numpy()
    enc_admit = pd.to_datetime(encounters_df["admission_timestamp"]).to_numpy()

    rows = []
    print(f"  generating {n:,} conditions …")
    for _ in tqdm(range(n), unit="cond", ncols=80):
        eix = int(rng.integers(0, len(enc_ids)))
        code, text, status = CONDITION_CODES[int(rng.integers(0, len(CONDITION_CODES)))]
        onset = (pd.Timestamp(enc_admit[eix]) - timedelta(days=int(rng.integers(0, 1825)))).date()
        rows.append({
            "condition_id":        uuid.uuid4().hex,
            "patient_id":          str(pat_ids[eix]),
            "encounter_id":        str(enc_ids[eix]),
            "code":                code,
            "code_text":           text,
            "onset_date":          onset.isoformat(),
            "abated_date":         None,
            "clinical_status":     status,
            "verification_status": "confirmed",
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_conditions.csv", index=False)
    print(f"  ✓ raw_conditions.csv    {len(df):,}")


def generate_medications(out_dir, n, encounters_df, seed=42):
    rng = np.random.default_rng(seed + 4)
    enc_ids = encounters_df["encounter_id"].to_numpy()
    pat_ids = encounters_df["patient_id"].to_numpy()
    enc_admit = pd.to_datetime(encounters_df["admission_timestamp"]).to_numpy()

    rows = []
    print(f"  generating {n:,} medications …")
    for _ in tqdm(range(n), unit="meds", ncols=80):
        eix = int(rng.integers(0, len(enc_ids)))
        rxnorm, name, dose, route = MEDICATIONS[int(rng.integers(0, len(MEDICATIONS)))]
        rows.append({
            "medication_request_id": uuid.uuid4().hex,
            "patient_id":            str(pat_ids[eix]),
            "encounter_id":          str(enc_ids[eix]),
            "rxnorm_code":           rxnorm,
            "medication_name":       name,
            "dosage_text":           dose,
            "route":                 route,
            "prescribed_at":         pd.Timestamp(enc_admit[eix]).isoformat(),
            "days_supply":           int(rng.choice([7, 30, 90])),
            "refills_allowed":       int(rng.choice([0, 1, 3, 5, 11])),
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_medications.csv", index=False)
    print(f"  ✓ raw_medications.csv   {len(df):,}")


def generate_procedures(out_dir, n, encounters_df, seed=42):
    rng = np.random.default_rng(seed + 5)
    enc_ids = encounters_df["encounter_id"].to_numpy()
    pat_ids = encounters_df["patient_id"].to_numpy()
    enc_admit = pd.to_datetime(encounters_df["admission_timestamp"]).to_numpy()

    rows = []
    print(f"  generating {n:,} procedures …")
    for _ in tqdm(range(n), unit="proc", ncols=80):
        eix = int(rng.integers(0, len(enc_ids)))
        cpt, text = PROCEDURES[int(rng.integers(0, len(PROCEDURES)))]
        ts = pd.Timestamp(enc_admit[eix]) + timedelta(minutes=int(rng.integers(0, 720)))
        rows.append({
            "procedure_id":       uuid.uuid4().hex,
            "patient_id":         str(pat_ids[eix]),
            "encounter_id":       str(enc_ids[eix]),
            "cpt_code":           cpt,
            "procedure_text":     text,
            "performed_at":       ts.isoformat(),
            "performer_provider": f"Dr.{int(rng.integers(1, 200))}",
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_procedures.csv", index=False)
    print(f"  ✓ raw_procedures.csv    {len(df):,}")
