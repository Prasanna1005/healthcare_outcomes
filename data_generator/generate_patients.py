"""generate_patients.py — synthetic patient master, FHIR-equivalent."""

import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from tqdm import tqdm


GENDERS = ["male", "female", "other"]
GENDER_PROBS = [0.49, 0.49, 0.02]

RACES = ["White", "Black", "Asian", "Other", "Mixed", "Native American"]
RACE_PROBS = [0.55, 0.15, 0.10, 0.10, 0.07, 0.03]

ETHNICITY = ["Non-Hispanic", "Hispanic"]
ETH_PROBS = [0.78, 0.22]

MARITAL = ["single", "married", "divorced", "widowed", "unknown"]
MARITAL_PROBS = [0.40, 0.45, 0.08, 0.05, 0.02]

INSURANCE_PLANS = ["Medicare", "Medicaid", "Aetna", "UnitedHealth", "BlueCross",
                   "Cigna", "Kaiser", "Self-Pay"]
INSURANCE_PROBS = [0.18, 0.20, 0.10, 0.12, 0.12, 0.10, 0.08, 0.10]

LANGUAGES = ["en", "es", "zh", "vi", "ar", "ko", "ru"]
LANG_PROBS = [0.78, 0.13, 0.03, 0.02, 0.02, 0.01, 0.01]

US_STATES = ["CA", "TX", "NY", "FL", "PA", "IL", "OH", "GA", "NC", "MI",
             "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI"]


def generate_patients(out_dir, n, seed=42):
    rng = np.random.default_rng(seed)
    fake = Faker(); Faker.seed(seed)

    today = datetime(2025, 12, 31).date()

    rows = []
    for i in tqdm(range(n), unit="patients", ncols=80, desc="patients"):
        gender = str(rng.choice(GENDERS, p=GENDER_PROBS))
        first_name = fake.first_name_female() if gender == "female" else (
                     fake.first_name_male() if gender == "male" else fake.first_name())
        last_name = fake.last_name()

        # Realistic age distribution: skewed right (more elderly)
        age_years = int(min(100, max(0, rng.gamma(3.5, 14))))
        dob = today - timedelta(days=age_years * 365 + int(rng.integers(0, 365)))

        is_deceased = bool(rng.random() < 0.04)   # ~4% deceased
        deceased_date = None
        if is_deceased:
            # Death within last 8 years
            offset_days = int(rng.integers(0, 8 * 365))
            deceased_date = (today - timedelta(days=offset_days)).isoformat()

        rows.append({
            "patient_id":          uuid.uuid4().hex,
            "mrn":                 f"MRN{i:08d}",
            "first_name":          first_name,
            "last_name":           last_name,
            "date_of_birth":       dob.isoformat(),
            "gender":              gender,
            "race":                str(rng.choice(RACES, p=RACE_PROBS)),
            "ethnicity":           str(rng.choice(ETHNICITY, p=ETH_PROBS)),
            "marital_status":      str(rng.choice(MARITAL, p=MARITAL_PROBS)),
            "address_line1":       fake.street_address(),
            "address_city":        fake.city(),
            "address_state":       str(rng.choice(US_STATES)),
            "address_postal_code": fake.zipcode(),
            "phone_number":        fake.phone_number(),
            "email":               fake.email(),
            "insurance_id":        f"INS{i:09d}",
            "insurance_plan":      str(rng.choice(INSURANCE_PLANS, p=INSURANCE_PROBS)),
            "primary_language":    str(rng.choice(LANGUAGES, p=LANG_PROBS)),
            "is_deceased":         is_deceased,
            "deceased_date":       deceased_date,
            "created_at":          datetime(2025, 1, 1).isoformat(),
            "updated_at":          datetime(2025, 1, 1).isoformat(),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "raw_patients.csv", index=False)
    print(f"  ✓ raw_patients.csv      {len(df):,}")
    return df
