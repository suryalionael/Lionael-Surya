import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import io

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CONFIG
from src.predict import ChurnPredictor
from src.utils import load_json

st.set_page_config(
    page_title="Telecom Churn Prediction Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f1f5f9;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stMetric label {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
    }
    .css-1542moe {
        background-color: #1e293b;
    }
    h1, h2, h3 {
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to check if models exist
@st.cache_resource
def get_predictor():
    models_dir = CONFIG["paths"]["models_dir"]
    model_path = os.path.join(models_dir, "model.pkl")
    if not os.path.exists(model_path):
        return None
    try:
        return ChurnPredictor()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Load dataset for EDA
@st.cache_data
def get_cleaned_data():
    processed_dir = CONFIG["paths"]["processed_data_dir"]
    data_path = os.path.join(processed_dir, "cleaned_customer_churn.csv")
    if os.path.exists(data_path):
        return pd.read_csv(data_path)
    # Fallback to raw if processed doesn't exist yet
    raw_path = CONFIG["paths"]["raw_data"]
    if os.path.exists(raw_path):
        # Apply standard clean
        from src.preprocessing import clean_data
        df = pd.read_csv(raw_path)
        return clean_data(df, is_train=True)
    return None

predictor = get_predictor()
df_data = get_cleaned_data()

st.sidebar.title("📊 Churn Portal")
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    "Select Page:",
    [
        "Overview & Business Impact",
        "Exploratory Data Analysis",
        "Model Performance",
        "Individual Customer Prediction",
        "Batch Prediction",
        "Model Explainability"
    ]
)

# ----------------- PAGE 1: OVERVIEW & BUSINESS IMPACT -----------------
if page == "Overview & Business Impact":
    st.title("📞 Telecom Customer Churn Prediction System")
    st.write(
        "This platform enables the subscriber retention team to proactively identify, explain, and target customers "
        "at high risk of churn before the next billing cycle. By replacing blanket discounts with machine-learning "
        "driven campaigns, we maximize the retention ROI."
    )
    
    st.header("💼 Business ROI What-If Simulator")
    st.write("Adjust the financial and response parameters below to simulate the financial impact of the campaign.")
    
    # Check if we have metrics loaded
    metrics_path = os.path.join(CONFIG["paths"]["models_dir"], "metrics.json")
    if os.path.exists(metrics_path):
        metrics = load_json(metrics_path)
        default_threshold = metrics.get("optimal_threshold", 0.5)
        test_sim = metrics.get("test_business_simulation", {})
        baseline_loss = test_sim.get("financials", {}).get("baseline_loss", 200000.0)
    else:
        default_threshold = 0.5
        baseline_loss = 250000.0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        campaign_cost = st.slider("Campaign Outreach Cost ($)", 5.0, 50.0, float(CONFIG["business"]["campaign_cost"]), step=1.0)
        retention_discount = st.slider("Retention Discount / Incentive ($)", 20.0, 200.0, float(CONFIG["business"]["retention_discount"]), step=5.0)
    with col2:
        retention_rate = st.slider("Retention Success Rate (%)", 10, 100, int(CONFIG["business"]["retention_rate"] * 100), step=5) / 100.0
        retention_period = st.slider("Retention Duration (Months Saved)", 1, 24, 6, step=1)
    with col3:
        threshold = st.slider("Decision Probability Threshold", 0.05, 0.95, float(default_threshold), step=0.05)
        
    # Perform simulation if data is available
    if df_data is not None and predictor is not None:
        # Get predictions for the entire dataset to show overall business impact
        df_clean = df_data.drop(columns=[CONFIG["data"]["target"]], errors="ignore")
        trans = predictor.pipeline.transform(df_clean)
        probs = predictor.model.predict_proba(trans)[:, 1]
        y_true = df_data[CONFIG["data"]["target"]].map({"Yes": 1, "No": 0, 1: 1, 0: 0})
        
        # Recalculate simulation with slider variables
        c_cost = campaign_cost
        r_discount = retention_discount
        r_rate = retention_rate
        customer_value = df_data["MonthlyCharges"] * retention_period
        
        y_pred = (probs >= threshold).astype(int)
        targeted = y_pred == 1
        actual_churn = y_true == 1
        actual_no_churn = y_true == 0
        
        tp_count = int(np.sum(targeted & actual_churn))
        fp_count = int(np.sum(targeted & actual_no_churn))
        fn_count = int(np.sum((y_pred == 0) & actual_churn))
        
        base_loss = float(np.sum(customer_value[actual_churn]))
        outreach_cost = float(np.sum(targeted) * c_cost)
        discount_cost = float(tp_count * r_rate * r_discount + fp_count * r_discount)
        total_cost = outreach_cost + discount_cost
        
        revenue_saved = float(np.sum(customer_value[targeted & actual_churn]) * r_rate)
        net_savings = revenue_saved - total_cost
        roi = (net_savings / total_cost * 100) if total_cost > 0 else 0.0
        
        # Display simulated metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Baseline Churn Loss", f"${base_loss:,.2f}", help="Total revenue lost if we run no retention campaign.")
        m2.metric("Simulated Net Savings", f"${net_savings:,.2f}", help="Expected net profit of the retention campaign (revenue saved - outreach & discount costs).")
        m3.metric("Outreach + Discount Cost", f"${total_cost:,.2f}", help="Total cost of campaign outreach and incentives paid.")
        m4.metric("Campaign ROI", f"{roi:.1f}%", help="Percentage return on campaign spending.")
        
        st.subheader("Campaign Details & Funnel Analysis")
        f1, f2 = st.columns(2)
        with f1:
            st.markdown(f"""
            - **Total Subscribers:** {len(y_true):,}
            - **Actual Churn Rate:** {y_true.mean() * 100:.1f}% ({y_true.sum():,} subscribers)
            - **Subscribers Targeted:** {targeted.sum():,} ({targeted.mean() * 100:.1f}% of base)
            - **Customers Retained:** {tp_count * r_rate:.1f} subscribers (at {r_rate * 100:.0f}% retention success rate)
            - **Frictionless Non-Churners Offered Offer (Cannibalization):** {fp_count:,} customers (who would have stayed anyway)
            """)
        with f2:
            # Funnel Chart
            fig = go.Figure(go.Funnel(
                y = ["Total Subscribers", "Actual Churners", "Targeted by Campaign", "Successfully Retained"],
                x = [len(y_true), y_true.sum(), targeted.sum(), int(tp_count * r_rate)],
                textinfo = "value+percent initial"
            ))
            fig.update_layout(title="Retention Funnel Simulation", template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.warning("Model or data is not fully loaded. Displaying static baseline estimation.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Baseline Churn Loss", f"${baseline_loss:,.2f}")
        m2.metric("Simulated Net Savings", "$35,420.00 (Estimated)")
        m3.metric("Outreach + Discount Cost", "$15,200.00")
        m4.metric("Campaign ROI", "233.0%")

# ----------------- PAGE 2: EXPLORATORY DATA ANALYSIS -----------------
elif page == "Exploratory Data Analysis":
    st.title("🔍 Exploratory Data Analysis")
    st.write("Understand demographics, account details, and services and their correlation with churn.")
    
    if df_data is None:
        st.error("Dataset not found. Please run the training pipeline first.")
    else:
        # Summary metrics
        churn_rate = (df_data["Churn"].map({"Yes": 1, "No": 0, 1: 1, 0: 0}).mean() * 100)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Customer Records", f"{len(df_data):,}")
        c2.metric("Overall Churn Rate", f"{churn_rate:.2f}%")
        c3.metric("Average Monthly Charges", f"${df_data['MonthlyCharges'].mean():.2f}")
        
        st.subheader("Demographics & Churn Relationship")
        d1, d2 = st.columns(2)
        with d1:
            fig = px.histogram(df_data, x="Contract", color="Churn", barmode="group",
                               title="Churn Rate by Contract Type",
                               color_discrete_map={"Yes": "#ef4444", "No": "#10b981", 1: "#ef4444", 0: "#10b981"})
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Business Insight: Month-to-month contracts account for the vast majority of churn. Locking customers into 1-year or 2-year contracts significantly reduces churn risk.*")
        with d2:
            fig = px.histogram(df_data, x="PaymentMethod", color="Churn", barmode="group",
                               title="Churn Rate by Payment Method",
                               color_discrete_map={"Yes": "#ef4444", "No": "#10b981", 1: "#ef4444", 0: "#10b981"})
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Business Insight: Customers paying via Electronic Check show the highest propensity to churn. Automatic payment methods (credit card/bank transfer) have much lower churn rates.*")

        st.subheader("Numerical Distributions")
        n1, n2 = st.columns(2)
        with n1:
            fig = px.box(df_data, x="Churn", y="tenure", color="Churn",
                         title="Tenure (Months) Distribution by Churn Status",
                         color_discrete_map={"Yes": "#ef4444", "No": "#10b981", 1: "#ef4444", 0: "#10b981"})
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Business Insight: Customers who churn typically leave within their first 12 months. Once a customer survives 24 months, their churn risk drops dramatically.*")
        with n2:
            fig = px.violin(df_data, x="Churn", y="MonthlyCharges", color="Churn", box=True,
                           title="Monthly Charges ($) Distribution by Churn Status",
                           color_discrete_map={"Yes": "#ef4444", "No": "#10b981", 1: "#ef4444", 0: "#10b981"})
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("*Business Insight: Customers who churn have higher average monthly charges (median around $80) compared to retained customers (median around $65), suggesting price-sensitivity.*")

# ----------------- PAGE 3: MODEL PERFORMANCE -----------------
elif page == "Model Performance":
    st.title("📈 Model Performance & Calibration")
    st.write("Detailed view of validation and test metrics, calibration, and classification thresholds.")
    
    metrics_path = os.path.join(CONFIG["paths"]["models_dir"], "metrics.json")
    if not os.path.exists(metrics_path):
        st.warning("Model metrics are not available. Please run the training pipeline first.")
    else:
        metrics = load_json(metrics_path)
        
        # Classification metrics table
        test_m = metrics["test_metrics"]
        st.subheader("Model Evaluation Metrics (Holdout Test Set)")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("ROC-AUC", f"{test_m['roc_auc']:.4f}")
        m_col2.metric("PR-AUC", f"{test_m['pr_auc']:.4f}")
        m_col3.metric("F1-Score", f"{test_m['f1_score']:.4f}")
        m_col4.metric("Matthews Corr (MCC)", f"{test_m['matthews_correlation_coefficient']:.4f}")
        
        st.write("### Model Comparison (5-Fold Stratified Cross-Validation)")
        comp_df = pd.DataFrame(metrics["model_comparison"])
        st.dataframe(comp_df.style.highlight_max(subset=["CV_AUC"], color="#1e3a8a"), use_container_width=True)
        
        st.subheader("Model Calibration Curve")
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.image(os.path.join(CONFIG["paths"]["figures_dir"], "calibration_comparison.png"), caption="Uncalibrated vs. Calibrated Classifier")
        with c_col2:
            st.markdown("""
            **Why Calibrate?**
            - Standard machine learning models (like raw XGBoost or Random Forests) output scores that do not represent true empirical probabilities.
            - Calibration adjusts prediction scores so that a predicted probability of 80% means exactly 80% of those customers churn.
            - Reliable probabilities are critical because our ROI simulator and decision thresholding depend on the absolute dollars saved, which directly multiplies probability by customer value.
            """)
            st.write(f"- **Uncalibrated Brier Score:** {metrics['calibration']['uncalibrated_brier']:.5f}")
            st.write(f"- **Calibrated Brier Score:** {metrics['calibration']['calibrated_brier']:.5f}")
            st.write(f"- **Brier Score Improvement:** {metrics['calibration']['brier_improvement']:.5f}")
            
        st.subheader("Optimal Decision Boundary and Metrics")
        st.image(os.path.join(CONFIG["paths"]["figures_dir"], "threshold_vs_savings.png"), caption="Threshold Sweep maximizing Net Savings")

# ----------------- PAGE 4: INDIVIDUAL CUSTOMER PREDICTION -----------------
elif page == "Individual Customer Prediction":
    st.title("👤 Individual Customer Churn Predictor")
    st.write("Predict churn risk, view tailored recommendations, and examine local risk drivers for a single customer.")
    
    if predictor is None:
        st.error("Model artifacts not loaded. Please run the training pipeline first.")
    else:
        # Prepopulate with standard example
        st.write("### Customer Profile Input")
        col1, col2, col3 = st.columns(3)
        with col1:
            gender = st.selectbox("Gender", ["Female", "Male"])
            senior = st.selectbox("Senior Citizen (1: Yes, 0: No)", [0, 1])
            partner = st.selectbox("Partner", ["Yes", "No"])
            dependents = st.selectbox("Dependents", ["Yes", "No"])
            tenure = st.slider("Tenure (Months)", 0, 72, 12)
            phone_service = st.selectbox("Phone Service", ["Yes", "No"])
            
        with col2:
            multiple_lines = st.selectbox("Multiple Lines", ["No", "Yes", "No phone service"])
            internet_service = st.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])
            online_security = st.selectbox("Online Security", ["No", "Yes", "No internet service"])
            online_backup = st.selectbox("Online Backup", ["Yes", "No", "No internet service"])
            device_protection = st.selectbox("Device Protection", ["No", "Yes", "No internet service"])
            tech_support = st.selectbox("Tech Support", ["No", "Yes", "No internet service"])
            
        with col3:
            streaming_tv = st.selectbox("Streaming TV", ["No", "Yes", "No internet service"])
            streaming_movies = st.selectbox("Streaming Movies", ["No", "Yes", "No internet service"])
            contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
            paperless = st.selectbox("Paperless Billing", ["Yes", "No"])
            payment = st.selectbox("Payment Method", [
                "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
            ])
            monthly_charges = st.number_input("Monthly Charges ($)", min_value=15.0, max_value=150.0, value=75.0)
            total_charges = st.number_input("Total Charges ($)", min_value=0.0, max_value=9000.0, value=tenure * monthly_charges)
            
        customer_dict = {
            "customerID": "INPUT-CUSTOMER",
            "gender": gender,
            "SeniorCitizen": int(senior),
            "Partner": partner,
            "Dependents": dependents,
            "tenure": int(tenure),
            "PhoneService": phone_service,
            "MultipleLines": multiple_lines,
            "InternetService": internet_service,
            "OnlineSecurity": online_security,
            "OnlineBackup": online_backup,
            "DeviceProtection": device_protection,
            "TechSupport": tech_support,
            "StreamingTV": streaming_tv,
            "StreamingMovies": streaming_movies,
            "Contract": contract,
            "PaperlessBilling": paperless,
            "PaymentMethod": payment,
            "MonthlyCharges": float(monthly_charges),
            "TotalCharges": float(total_charges)
        }
        
        if st.button("Predict Churn Risk"):
            with st.spinner("Analyzing profile..."):
                res = predictor.predict_single(customer_dict)
                
            st.header("Prediction Results")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                # Probability Gauge
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = res["churn_probability"] * 100,
                    title = {'text': "Churn Probability (%)"},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#38bdf8"},
                        'steps': [
                            {'range': [0, 20], 'color': "#10b981"},
                            {'range': [20, 50], 'color': "#eab308"},
                            {'range': [50, 80], 'color': "#f97316"},
                            {'range': [80, 100], 'color': "#ef4444"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': predictor.optimal_threshold * 100
                        }
                    }
                ))
                fig.update_layout(template="plotly_dark", height=280)
                st.plotly_chart(fig, use_container_width=True)
                
            with p_col2:
                st.metric("Risk Category", res["risk_category"])
                st.metric("Model Confidence", f"{res['confidence']*100:.1f}%")
                st.write("#### Recommended Business Action")
                st.success(res["recommended_action"])
                
            st.subheader("Model Decision Logic (SHAP Explanations)")
            e1, e2 = st.columns(2)
            with e1:
                st.write("🔺 **Risk Factors (Increasing Risk)**")
                if res["top_risk_drivers"]:
                    for item in res["top_risk_drivers"]:
                        st.markdown(f"- **{item['feature']}** (value: {item['raw_value']}): {item['business_explanation']} *(Impact score: +{item['shap_value']:.3f})*")
                else:
                    st.write("No major risk factors found.")
            with e2:
                st.write("🟢 **Protective Factors (Supporting Retention)**")
                if res["top_protective_factors"]:
                    for item in res["top_protective_factors"]:
                        st.markdown(f"- **{item['feature']}** (value: {item['raw_value']}): {item['business_explanation']} *(Impact score: {item['shap_value']:.3f})*")
                else:
                    st.write("No major protective factors found.")

# ----------------- PAGE 5: BATCH PREDICTION -----------------
elif page == "Batch Prediction":
    st.title("📁 Batch Customer Churn Prediction")
    st.write("Upload a CSV file containing customer profiles to analyze churn risks in bulk.")
    
    if predictor is None:
        st.error("Model artifacts not loaded. Please run the training pipeline first.")
    else:
        # File uploader
        uploaded_file = st.file_uploader("Upload Customer CSV File", type="csv")
        
        # Provide sample template download
        if df_data is not None:
            # Generate a sample CSV with 10 rows from the dataset (without churn label)
            sample_df = df_data.drop(columns=[CONFIG["data"]["target"]]).head(10)
            csv_buffer = io.StringIO()
            sample_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Sample CSV Template",
                data=csv_buffer.getvalue(),
                file_name="churn_batch_template.csv",
                mime="text/csv"
            )
            
        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.success("File uploaded successfully!")
                
                # Check for ID column
                id_col = CONFIG["data"]["id_column"]
                if id_col not in df_upload.columns:
                    st.warning(f"Column '{id_col}' not found in uploaded file. Using index values as IDs.")
                
                # Run predictions
                with st.spinner("Processing batch predictions..."):
                    df_preds = predictor.predict_batch(df_upload)
                    
                st.subheader("Batch Results Summary")
                b1, b2 = st.columns(2)
                with b1:
                    # Risk categories pie chart
                    category_counts = df_preds["risk_category"].value_counts().reset_index()
                    fig = px.pie(category_counts, names="risk_category", values="count",
                                 title="Subscribers by Risk Category",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                with b2:
                    # Churn prediction count
                    pred_counts = df_preds["prediction"].value_counts().reset_index()
                    pred_counts["Status"] = pred_counts["prediction"].map({1: "Predicted Churn", 0: "Predicted Retained"})
                    fig = px.bar(pred_counts, x="Status", y="count", color="Status",
                                 title="Retention Action Targets",
                                 color_discrete_map={"Predicted Churn": "#ef4444", "Predicted Retained": "#10b981"})
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Full Prediction Table
                st.subheader("Prediction Details")
                st.dataframe(df_preds, use_container_width=True)
                
                # Download results button
                out_buffer = io.StringIO()
                df_preds.to_csv(out_buffer, index=False)
                st.download_button(
                    label="📥 Download Predictions CSV",
                    data=out_buffer.getvalue(),
                    file_name="churn_predictions_results.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

# ----------------- PAGE 6: MODEL EXPLAINABILITY -----------------
elif page == "Model Explainability":
    st.title("🧠 Global Model Explainability (SHAP)")
    st.write(
        "SHAP (SHapley Additive exPlanations) values explain how much each feature contributes to the "
        "model's final prediction relative to a baseline."
    )
    
    st.subheader("Global Feature Importance Summary")
    st.write("This summary plot shows the magnitude and directional impact of features on churn risk:")
    st.image(os.path.join(CONFIG["paths"]["figures_dir"], "shap_summary_plot.png"), caption="SHAP Summary Plot")
    
    st.write("### Key Global Findings & Business Explanations")
    st.markdown("""
    1. **Contract Type (Month-to-month):** Month-to-month contracts are by far the strongest driver of high churn risk (red dots on the right side). Annual contract terms provide powerful barriers to exit.
    2. **Tenure (Months):** Longer tenure acts as a major protective factor (retains customers). High tenure values have negative SHAP values (blue dots on the left side).
    3. **Internet Service (Fiber Optic):** Subscribing to Fiber Optic internet service is linked to higher churn risk. The marketing team should investigate if this is caused by billing discrepancies, high base pricing, or service stability issues.
    4. **Online Security & Tech Support (None):** Customers without Online Security or active Technical Support options have a higher churn risk. Promoting these support services increases account stickiness.
    5. **Electronic Check Payment:** Utilizing Electronic Check payment methods is a strong driver of churn risk. Directing these customers to configure auto-pay is a high-yield retention action.
    """)
