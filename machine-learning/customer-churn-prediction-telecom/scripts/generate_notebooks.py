import os
import json

def create_notebook(cells, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    with open(filepath, "w") as f:
        json.dump(nb, f, indent=2)
    print(f"Created notebook at {filepath}")

# 1. EDA Notebook
eda_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 01 Exploratory Data Analysis (EDA)\n",
            "This notebook loads and analyzes the raw telecom churn dataset to uncover demographics, account, and service trends correlated with customer churn."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "\n",
            "# Load configurations\n",
            "from src.config import CONFIG\n",
            "from src.preprocessing import clean_data\n",
            "\n",
            "df_raw = pd.read_csv(CONFIG[\"paths\"][\"raw_data\"])\n",
            "df = clean_data(df_raw, is_train=True)\n",
            "df.head()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### Target Imbalance Analysis"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "plt.figure(figsize=(6, 4))\n",
            "sns.countplot(x='Churn', data=df_raw, palette='Blues')\n",
            "plt.title('Target Distribution (Churn Status)')\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### Demographics vs. Churn"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
            "sns.countplot(x='Contract', hue='Churn', data=df_raw, ax=axes[0], palette='Set1')\n",
            "axes[0].set_title('Churn by Contract Type')\n",
            "\n",
            "sns.countplot(x='PaymentMethod', hue='Churn', data=df_raw, ax=axes[1], palette='Set2')\n",
            "axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=30)\n",
            "axes[1].set_title('Churn by Payment Method')\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    }
]

# 2. Feature Engineering Notebook
fe_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 02 Feature Engineering\n",
            "This notebook details the custom scikit-learn preprocessing and feature engineering transformer pipeline."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import pandas as pd\n",
            "import numpy as np\n",
            "from src.preprocessing import clean_data, load_raw_data\n",
            "from src.feature_engineering import FeatureEngineer, get_preprocessing_pipeline\n",
            "\n",
            "# Load clean data\n",
            "df_clean = clean_data(load_raw_data(), is_train=True)\n",
            "X = df_clean.drop(columns=['Churn'])\n",
            "y = df_clean['Churn']\n",
            "\n",
            "fe = FeatureEngineer()\n",
            "fe.fit(X)\n",
            "X_engineered = fe.transform(X)\n",
            "X_engineered[['tenure_group', 'service_count', 'security_count', 'avg_monthly_revenue', 'high_value_customer']].head()"
        ]
    }
]

# 3. Model Training Notebook
train_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 03 Model Training, Optimization & Calibration\n",
            "This notebook compares classifiers, runs hyperparameter optimization using Optuna, calibrates probabilities, and estimates financial savings."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "from src.utils import load_json\n",
            "from src.config import CONFIG\n",
            "import pandas as pd\n",
            "\n",
            "metrics_path = os.path.join(CONFIG[\"paths\"][\"models_dir\"], \"metrics.json\")\n",
            "if os.path.exists(metrics_path):\n",
            "    metrics = load_json(metrics_path)\n",
            "    print(\"Optimal Threshold:\", metrics[\"optimal_threshold\"])\n",
            "    print(\"Test Set ROC-AUC:\", metrics[\"test_metrics\"][\"roc_auc\"])\n",
            "    print(\"Net Savings:\", metrics[\"test_business_simulation\"][\"financials\"][\"net_savings\"])\n",
            "else:\n",
            "    print(\"Please execute train.py first to populate the metrics database.\")"
        ]
    }
]

# 4. Explainability Notebook
explain_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 04 Model Explainability (SHAP)\n",
            "This notebook explores the model's global features and translates individual risk drivers into plain business recommendations."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import joblib\n",
            "from src.config import CONFIG\n",
            "from src.predict import ChurnPredictor\n",
            "\n",
            "predictor = ChurnPredictor()\n",
            "\n",
            "# Example single customer\n",
            "customer = {\n",
            "    \"gender\": \"Female\",\n",
            "    \"SeniorCitizen\": 0,\n",
            "    \"Partner\": \"Yes\",\n",
            "    \"Dependents\": \"No\",\n",
            "    \"tenure\": 1,\n",
            "    \"PhoneService\": \"No\",\n",
            "    \"MultipleLines\": \"No phone service\",\n",
            "    \"InternetService\": \"DSL\",\n",
            "    \"OnlineSecurity\": \"No\",\n",
            "    \"OnlineBackup\": \"Yes\",\n",
            "    \"DeviceProtection\": \"No\",\n",
            "    \"TechSupport\": \"No\",\n",
            "    \"StreamingTV\": \"No\",\n",
            "    \"StreamingMovies\": \"No\",\n",
            "    \"Contract\": \"Month-to-month\",\n",
            "    \"PaperlessBilling\": \"Yes\",\n",
            "    \"PaymentMethod\": \"Electronic check\",\n",
            "    \"MonthlyCharges\": 29.85,\n",
            "    \"TotalCharges\": 29.85\n",
            "}\n",
            "\n",
            "res = predictor.predict_single(customer)\n",
            "print(\"Churn Probability:\", res[\"churn_probability\"])\n",
            "print(\"Risk Category:\", res[\"risk_category\"])\n",
            "print(\"Recommended Action:\", res[\"recommended_action\"])\n",
            "print(\"Top Churn Drivers:\", [x['business_explanation'] for x in res['top_risk_drivers']])"
        ]
    }
]

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    notebooks_dir = os.path.join(root, "notebooks")
    create_notebook(eda_cells, os.path.join(notebooks_dir, "01_eda.ipynb"))
    create_notebook(fe_cells, os.path.join(notebooks_dir, "02_feature_engineering.ipynb"))
    create_notebook(train_cells, os.path.join(notebooks_dir, "03_model_training.ipynb"))
    create_notebook(explain_cells, os.path.join(notebooks_dir, "04_explainability.ipynb"))
