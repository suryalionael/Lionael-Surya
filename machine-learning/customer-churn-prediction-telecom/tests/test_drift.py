import pandas as pd

from src.drift import build_drift_reference, evaluate_drift


def _base_records():
    return pd.DataFrame(
        {
            "customerID": [str(i) for i in range(20)],
            "tenure": [
                1,
                2,
                3,
                4,
                5,
                6,
                12,
                18,
                24,
                30,
                36,
                42,
                48,
                54,
                60,
                66,
                70,
                71,
                72,
                72,
            ],
            "MonthlyCharges": [
                30,
                32,
                35,
                36,
                40,
                44,
                45,
                50,
                52,
                55,
                60,
                63,
                65,
                70,
                74,
                78,
                80,
                84,
                88,
                90,
            ],
            "TotalCharges": [
                30,
                64,
                105,
                144,
                200,
                264,
                540,
                900,
                1248,
                1650,
                2160,
                2646,
                3120,
                3780,
                4440,
                5148,
                5600,
                5964,
                6336,
                6480,
            ],
            "gender": ["Female", "Male"] * 10,
            "SeniorCitizen": [0] * 18 + [1, 1],
            "Partner": ["Yes", "No"] * 10,
            "Dependents": ["No"] * 20,
            "PhoneService": ["Yes"] * 20,
            "MultipleLines": ["No", "Yes"] * 10,
            "InternetService": ["DSL"] * 10 + ["Fiber optic"] * 10,
            "OnlineSecurity": ["Yes", "No"] * 10,
            "OnlineBackup": ["Yes", "No"] * 10,
            "DeviceProtection": ["No"] * 20,
            "TechSupport": ["Yes", "No"] * 10,
            "StreamingTV": ["No", "Yes"] * 10,
            "StreamingMovies": ["No", "Yes"] * 10,
            "Contract": ["Month-to-month"] * 10 + ["Two year"] * 10,
            "PaperlessBilling": ["Yes", "No"] * 10,
            "PaymentMethod": ["Electronic check"] * 10
            + ["Credit card (automatic)"] * 10,
        }
    )


def test_build_drift_reference_contains_expected_profiles():
    reference = build_drift_reference(_base_records(), n_bins=4)

    assert reference["row_count"] == 20
    assert "tenure" in reference["numeric_features"]
    assert "Contract" in reference["categorical_features"]
    assert sum(reference["numeric_features"]["tenure"]["distribution"]) == 1.0


def test_evaluate_drift_flags_shifted_batch():
    reference = build_drift_reference(_base_records(), n_bins=4)
    shifted = _base_records().copy()
    shifted["Contract"] = "Month-to-month"
    shifted["MonthlyCharges"] = 120.0

    report = evaluate_drift(reference, shifted)

    assert report["drift_detected"] is True
    assert "MonthlyCharges" in report["drifted_features"]
    assert report["max_psi"] >= report["thresholds"]["drift_psi"]


def test_evaluate_drift_reports_missing_feature():
    reference = build_drift_reference(_base_records(), n_bins=4)
    current = _base_records().drop(columns=["tenure"])

    report = evaluate_drift(reference, current)

    tenure_report = next(
        item for item in report["features"] if item["feature"] == "tenure"
    )
    assert tenure_report["status"] == "missing"
