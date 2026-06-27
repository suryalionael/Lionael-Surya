import os
import json
import pandas as pd
import numpy as np
from src.config import CONFIG
from src.logger import logger

def validate_dataset(df: pd.DataFrame, is_train: bool = True) -> dict:
    """
    Performs data quality and schema validation on the input DataFrame.
    Generates a dictionary report and saves a Markdown validation report.
    """
    report = {
        "passed_all": True,
        "checks": {},
        "summary": {}
    }

    # 1. Row Count & Columns
    report["summary"]["row_count"] = int(len(df))
    report["summary"]["col_count"] = int(df.shape[1])
    
    # 2. Schema check (Expected columns)
    expected_numerical = CONFIG["data"]["numerical_features"]
    expected_categorical = CONFIG["data"]["categorical_features"]
    target_col = CONFIG["data"]["target"]
    id_col = CONFIG["data"]["id_column"]
    
    expected_cols = [id_col] + expected_numerical + expected_categorical
    if is_train:
        expected_cols.append(target_col)
        
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        report["checks"]["schema_validation"] = {
            "status": "FAIL",
            "message": f"Missing columns in input: {missing_cols}"
        }
        report["passed_all"] = False
    else:
        report["checks"]["schema_validation"] = {
            "status": "PASS",
            "message": "All required columns are present."
        }

    # 3. Missing values check (including whitespaces in string columns)
    # TotalCharges contains empty spaces ' ' in raw data.
    # Convert ' ' to NaN in a copy of the dataframe for checking missing values properly.
    df_check = df.copy()
    if "TotalCharges" in df_check.columns:
        if not pd.api.types.is_numeric_dtype(df_check["TotalCharges"]):
            df_check["TotalCharges"] = df_check["TotalCharges"].astype(str).replace(r"^\s*$", np.nan, regex=True)
        df_check["TotalCharges"] = pd.to_numeric(df_check["TotalCharges"], errors="coerce")
        
    missing_counts = df_check.isnull().sum()
    missing_summary = {}
    for col, count in missing_counts.items():
        if count > 0:
            missing_summary[col] = {
                "count": int(count),
                "percentage": float(round((count / len(df)) * 100, 2))
            }
            
    if missing_summary:
        report["checks"]["missing_values"] = {
            "status": "WARNING",
            "message": f"Missing values detected in: {list(missing_summary.keys())}",
            "details": missing_summary
        }
    else:
        report["checks"]["missing_values"] = {
            "status": "PASS",
            "message": "No missing values detected."
        }

    # 4. Duplicate rows (excluding customerID if present)
    check_cols = [c for c in df.columns if c != id_col]
    dup_count = df.duplicated(subset=check_cols).sum()
    if dup_count > 0:
        report["checks"]["duplicate_rows"] = {
            "status": "WARNING",
            "message": f"Detected {dup_count} duplicate rows (excluding customerID)."
        }
    else:
        report["checks"]["duplicate_rows"] = {
            "status": "PASS",
            "message": "No duplicate rows detected."
        }

    # 5. Invalid Categories Check
    invalid_categories = {}
    expected_categories = {
        "gender": ["Male", "Female"],
        "SeniorCitizen": [0, 1, "0", "1"],
        "Partner": ["Yes", "No"],
        "Dependents": ["Yes", "No"],
        "PhoneService": ["Yes", "No"],
        "MultipleLines": ["Yes", "No", "No phone service"],
        "InternetService": ["DSL", "Fiber optic", "No"],
        "OnlineSecurity": ["Yes", "No", "No internet service"],
        "OnlineBackup": ["Yes", "No", "No internet service"],
        "DeviceProtection": ["Yes", "No", "No internet service"],
        "TechSupport": ["Yes", "No", "No internet service"],
        "StreamingTV": ["Yes", "No", "No internet service"],
        "StreamingMovies": ["Yes", "No", "No internet service"],
        "Contract": ["Month-to-month", "One year", "Two year"],
        "PaperlessBilling": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
    }
    
    for col, valid_vals in expected_categories.items():
        if col in df.columns:
            # Drop NaN for category checking
            unique_vals = df[col].dropna().unique()
            invalid = [val for val in unique_vals if val not in valid_vals]
            if invalid:
                invalid_categories[col] = [str(x) for x in invalid]
                
    if invalid_categories:
        report["checks"]["invalid_categories"] = {
            "status": "FAIL",
            "message": f"Columns with unexpected categories: {list(invalid_categories.keys())}",
            "details": invalid_categories
        }
        report["passed_all"] = False
    else:
        report["checks"]["invalid_categories"] = {
            "status": "PASS",
            "message": "All categorical columns have expected categories."
        }

    # 6. Negative Tenure or impossible values
    impossible_vals = {}
    if "tenure" in df.columns:
        tenure_min = df["tenure"].min()
        tenure_max = df["tenure"].max()
        if tenure_min < 0:
            impossible_vals["tenure"] = f"Min tenure is negative: {tenure_min}"
        elif tenure_max > 120: # Assuming max tenure 10 years (120 months)
            impossible_vals["tenure"] = f"Tenure exceeds 120 months: {tenure_max}"
            
    if "MonthlyCharges" in df.columns:
        mc_min = df["MonthlyCharges"].min()
        if mc_min < 0:
            impossible_vals["MonthlyCharges"] = f"Negative monthly charges: {mc_min}"

    if "TotalCharges" in df_check.columns:
        tc_min = df_check["TotalCharges"].min()
        if tc_min < 0:
            impossible_vals["TotalCharges"] = f"Negative total charges: {tc_min}"

    if impossible_vals:
        report["checks"]["impossible_values"] = {
            "status": "FAIL",
            "message": "Impossible values found in numerical features.",
            "details": impossible_vals
        }
        report["passed_all"] = False
    else:
        report["checks"]["impossible_values"] = {
            "status": "PASS",
            "message": "All numerical features are within valid, realistic ranges."
        }

    # 7. Target balance check
    if is_train and target_col in df.columns:
        target_counts = df[target_col].value_counts()
        target_pct = df[target_col].value_counts(normalize=True) * 100
        balance_info = {}
        for val, count in target_counts.items():
            balance_info[str(val)] = {
                "count": int(count),
                "percentage": float(round(target_pct[val], 2))
            }
        report["checks"]["target_balance"] = {
            "status": "PASS",
            "message": f"Target balance details: {balance_info}",
            "details": balance_info
        }
    else:
        report["checks"]["target_balance"] = {
            "status": "INFO",
            "message": "Target column is not present or validation is not run on train set."
        }

    # 8. Outliers summary (IQR Method)
    outlier_summary = {}
    for col in expected_numerical:
        if col in df_check.columns:
            q1 = df_check[col].quantile(0.25)
            q3 = df_check[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = df_check[(df_check[col] < lower_bound) | (df_check[col] > upper_bound)]
            if len(outliers) > 0:
                outlier_summary[col] = {
                    "count": int(len(outliers)),
                    "percentage": float(round((len(outliers) / len(df)) * 100, 2)),
                    "bounds": [float(round(lower_bound, 2)), float(round(upper_bound, 2))]
                }
    
    report["checks"]["outlier_summary"] = {
        "status": "INFO",
        "message": f"Outliers detected in: {list(outlier_summary.keys())}",
        "details": outlier_summary
    }

    # Generate Markdown Report
    save_validation_report(report)

    return report


def save_validation_report(report: dict) -> None:
    """Saves the validation report as a markdown file."""
    reports_dir = CONFIG["paths"]["reports_dir"]
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "data_validation_report.md")
    
    markdown_content = []
    markdown_content.append("# Data Validation Report")
    markdown_content.append(f"**Passed All Checks:** {'✅ PASS' if report['passed_all'] else '❌ FAIL'}\n")
    
    markdown_content.append("## Dataset Summary")
    markdown_content.append(f"- **Total Rows:** {report['summary']['row_count']}")
    markdown_content.append(f"- **Total Columns:** {report['summary']['col_count']}\n")
    
    markdown_content.append("## Check Details")
    for check_name, info in report["checks"].items():
        status = info["status"]
        status_emoji = "✅" if status == "PASS" else ("⚠️" if status in ["WARNING", "INFO"] else "❌")
        markdown_content.append(f"### {status_emoji} {check_name.replace('_', ' ').title()}")
        markdown_content.append(f"- **Status:** {status}")
        markdown_content.append(f"- **Message:** {info['message']}")
        
        if "details" in info and info["details"]:
            markdown_content.append("- **Details:**")
            markdown_content.append("```json")
            markdown_content.append(json.dumps(info["details"], indent=2))
            markdown_content.append("```")
        markdown_content.append("")
        
    with open(report_path, "w") as f:
        f.write("\n".join(markdown_content))
    
    logger.info(f"Data validation report written to {report_path}")
