import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, roc_curve,
    confusion_matrix, balanced_accuracy_score, matthews_corrcoef
)
from typing import Dict, Any, Tuple
from src.config import CONFIG
from src.logger import logger
from src.utils import save_json

def compute_metrics(y_true: pd.Series, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    """Computes a wide variety of machine learning classification metrics."""
    y_pred = (y_prob >= threshold).astype(int)
    
    # Standard metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    mcc = matthews_corrcoef(y_true, y_pred)
    
    # Area under curves
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)
    
    prec_vals, rec_vals, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(rec_vals, prec_vals)
    
    return {
        "accuracy": float(acc),
        "balanced_accuracy": float(bal_acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "matthews_correlation_coefficient": float(mcc),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "threshold": float(threshold)
    }

def simulate_business_roi(
    y_true: pd.Series, 
    y_prob: np.ndarray, 
    threshold: float, 
    monthly_charges: pd.Series
) -> Dict[str, Any]:
    """
    Simulates the financial impact of a proactive retention campaign.
    Calculates campaign costs, retention discount payouts, and value saved.
    """
    # Business assumptions from config
    c_cost = CONFIG["business"]["campaign_cost"]
    r_discount = CONFIG["business"]["retention_discount"]
    r_rate = CONFIG["business"]["retention_rate"]
    
    # Value saved is estimated as monthly charges * 6 (retention duration: 6 months)
    retention_period_months = 6
    customer_value = monthly_charges * retention_period_months
    
    y_pred = (y_prob >= threshold).astype(int)
    y_true = np.array(y_true)
    
    # Financial components
    total_customers = len(y_true)
    actual_churners = int(np.sum(y_true == 1))
    
    targeted = y_pred == 1
    not_targeted = y_pred == 0
    actual_churn = y_true == 1
    actual_no_churn = y_true == 0
    
    tp = targeted & actual_churn
    fp = targeted & actual_no_churn
    fn = not_targeted & actual_churn
    tn = not_targeted & actual_no_churn
    
    tp_count = int(np.sum(tp))
    fp_count = int(np.sum(fp))
    fn_count = int(np.sum(fn))
    tn_count = int(np.sum(tn))
    
    # 1. Baseline: Do Nothing (all actual churners are lost)
    baseline_loss = float(np.sum(customer_value[actual_churn]))
    
    # 2. Campaign Costs
    campaign_outreach_cost = float(np.sum(targeted) * c_cost)
    
    # 3. Retention Discount Payouts
    # TP: actual churners offered discount. They accept with probability r_rate.
    tp_discount_cost = float(tp_count * r_rate * r_discount)
    # FP: non-churners offered discount. They will accept the discount since they stay!
    fp_discount_cost = float(fp_count * r_discount)
    total_discount_cost = tp_discount_cost + fp_discount_cost
    
    total_campaign_cost = campaign_outreach_cost + total_discount_cost
    
    # 4. Revenue Saved (TP who accept the offer)
    revenue_saved = float(np.sum(customer_value[tp]) * r_rate)
    
    # 5. Opportunity Cost (revenue lost from FN)
    opportunity_loss = float(np.sum(customer_value[fn]))
    
    # Net Financial Outcomes
    # Financial outcome under the campaign:
    # We start with the original baseline revenue.
    # We save some revenue, but pay campaign costs and lose opportunity_loss.
    net_savings = revenue_saved - total_campaign_cost
    roi = (net_savings / total_campaign_cost * 100) if total_campaign_cost > 0 else 0.0
    
    return {
        "threshold": float(threshold),
        "confusion_matrix": {
            "tp": tp_count,
            "fp": fp_count,
            "fn": fn_count,
            "tn": tn_count
        },
        "metrics": {
            "total_customers": total_customers,
            "actual_churners": actual_churners,
            "targeted_customers": int(np.sum(targeted)),
            "retained_customers_estimate": float(tp_count * r_rate)
        },
        "financials": {
            "baseline_loss": baseline_loss,
            "campaign_outreach_cost": campaign_outreach_cost,
            "discount_payout_cost": total_discount_cost,
            "total_campaign_cost": total_campaign_cost,
            "revenue_saved": revenue_saved,
            "opportunity_loss": opportunity_loss,
            "net_savings": net_savings,
            "roi_percentage": float(roi)
        }
    }

def find_optimal_threshold(
    y_true: pd.Series, 
    y_prob: np.ndarray, 
    monthly_charges: pd.Series
) -> Tuple[float, Dict[str, Any]]:
    """Sweeps thresholds from 0.01 to 0.99 to find the threshold that maximizes Net Savings."""
    best_savings = -float("inf")
    best_threshold = 0.5
    best_simulation = {}
    
    thresholds = np.linspace(0.01, 0.99, 99)
    for t in thresholds:
        sim = simulate_business_roi(y_true, y_prob, t, monthly_charges)
        savings = sim["financials"]["net_savings"]
        if savings > best_savings:
            best_savings = savings
            best_threshold = t
            best_simulation = sim
            
    logger.info(f"Optimal decision threshold found: {best_threshold:.2f} (Savings: ${best_savings:,.2f})")
    return float(best_threshold), best_simulation

def generate_evaluation_plots(
    y_true: pd.Series, 
    y_prob: np.ndarray, 
    threshold: float, 
    monthly_charges: pd.Series,
    figures_dir: str = None
) -> None:
    """Generates and saves the ROC Curve, Precision-Recall Curve, and Confusion Matrix heatmap."""
    if figures_dir is None:
        figures_dir = CONFIG["paths"]["figures_dir"]
    os.makedirs(figures_dir, exist_ok=True)
    
    y_pred = (y_prob >= threshold).astype(int)
    
    # 1. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Retained", "Churned"], yticklabels=["Retained", "Churned"])
    plt.title(f"Confusion Matrix (Threshold = {threshold:.2f})", fontsize=14)
    plt.ylabel("Actual", fontsize=12)
    plt.xlabel("Predicted", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "confusion_matrix.png"), dpi=300)
    plt.close()
    
    # 2. ROC and PR Curves combined
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)
    axes[0].plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.4f})")
    axes[0].plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    # Draw point for the threshold
    idx = np.argmin(np.abs(np.linspace(0.01, 0.99, len(fpr)) - threshold)) # approximate
    # To get exact point:
    closest_idx = np.argmin(np.abs(roc_curve(y_true, y_prob)[2] - threshold))
    axes[0].scatter(fpr[closest_idx], tpr[closest_idx], color="black", s=100, zorder=5, label=f"Threshold {threshold:.2f}")
    axes[0].set_xlim([0.0, 1.0])
    axes[0].set_ylim([0.0, 1.05])
    axes[0].set_xlabel("False Positive Rate", fontsize=12)
    axes[0].set_ylabel("True Positive Rate", fontsize=12)
    axes[0].set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=14)
    axes[0].legend(loc="lower right")
    axes[0].grid(True, linestyle=":")
    
    # PR Curve
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(rec, prec)
    axes[1].plot(rec, prec, color="blue", lw=2, label=f"PR curve (AUC = {pr_auc:.4f})")
    axes[1].set_xlim([0.0, 1.0])
    axes[1].set_ylim([0.0, 1.05])
    axes[1].set_xlabel("Recall", fontsize=12)
    axes[1].set_ylabel("Precision", fontsize=12)
    axes[1].set_title("Precision-Recall Curve", fontsize=14)
    axes[1].legend(loc="lower left")
    axes[1].grid(True, linestyle=":")
    
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "evaluation_curves.png"), dpi=300)
    plt.close()
    
    # 3. Threshold vs. Net Savings curve
    thresholds = np.linspace(0.01, 0.99, 99)
    savings = []
    c_cost = CONFIG["business"]["campaign_cost"]
    r_discount = CONFIG["business"]["retention_discount"]
    r_rate = CONFIG["business"]["retention_rate"]
    retention_period_months = 6
    customer_val_array = np.array(monthly_charges) * retention_period_months
    
    for t in thresholds:
        preds = (y_prob >= t).astype(int)
        tp_m = (preds == 1) & (y_true == 1)
        fp_m = (preds == 1) & (y_true == 0)
        
        rev_saved = np.sum(customer_val_array[tp_m]) * r_rate
        outreach_cost = np.sum(preds) * c_cost
        disc_cost = np.sum(tp_m) * r_rate * r_discount + np.sum(fp_m) * r_discount
        net_save = rev_saved - (outreach_cost + disc_cost)
        savings.append(net_save)
        
    plt.figure(figsize=(8, 5))
    plt.plot(thresholds, savings, color="green", lw=2)
    plt.axvline(x=threshold, color="red", linestyle="--", label=f"Optimal Threshold: {threshold:.2f}")
    plt.title("Net Savings vs. Decision Threshold", fontsize=14)
    plt.xlabel("Decision Threshold", fontsize=12)
    plt.ylabel("Expected Net Savings ($)", fontsize=12)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    plt.legend()
    plt.grid(True, linestyle=":")
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "threshold_vs_savings.png"), dpi=300)
    plt.close()
    
    logger.info("Saved all evaluation figures.")

def generate_evaluation_report(metrics: Dict[str, Any], sim: Dict[str, Any], output_path: str = None) -> None:
    """Generates a comprehensive markdown report for the model performance and business ROI."""
    if output_path is None:
        output_path = os.path.join(CONFIG["paths"]["reports_dir"], "model_evaluation_report.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    markdown_content = []
    markdown_content.append("# Model Evaluation & Business Impact Report")
    
    markdown_content.append("## Executive Summary")
    markdown_content.append(f"By deploying the calibrated churn prediction model at the optimal decision threshold of **{sim['threshold']:.2f}**, the retention team can maximize the campaign financial impact:")
    markdown_content.append(f"- **Estimated Net Savings:** **${sim['financials']['net_savings']:,.2f}** (above a 'do-nothing' baseline)")
    markdown_content.append(f"- **Campaign ROI:** **{sim['financials']['roi_percentage']:.2f}%**")
    markdown_content.append(f"- **Customers Targeted:** {sim['metrics']['targeted_customers']} out of {sim['metrics']['total_customers']}")
    markdown_content.append(f"- **Expected Retained Customers:** {sim['metrics']['retained_customers_estimate']:.1f} customers\n")
    
    markdown_content.append("## Machine Learning Metrics")
    markdown_content.append("| Metric | Value | Description |")
    markdown_content.append("| :--- | :--- | :--- |")
    markdown_content.append(f"| ROC-AUC | {metrics['roc_auc']:.4f} | Ability of the model to distinguish between classes |")
    markdown_content.append(f"| PR-AUC | {metrics['pr_auc']:.4f} | Area under Precision-Recall Curve (essential for class imbalance) |")
    markdown_content.append(f"| F1-Score | {metrics['f1_score']:.4f} | Harmonic mean of Precision and Recall |")
    markdown_content.append(f"| Precision | {metrics['precision']:.4f} | Out of all predicted churners, how many actually churned |")
    markdown_content.append(f"| Recall | {metrics['recall']:.4f} | Out of all actual churners, how many did we identify |")
    markdown_content.append(f"| Balanced Accuracy | {metrics['balanced_accuracy']:.4f} | Average of recall obtained on each class |")
    markdown_content.append(f"| MCC | {metrics['matthews_correlation_coefficient']:.4f} | Matthews Correlation Coefficient (balanced measure for binary classification) |")
    markdown_content.append(f"| Decision Threshold | {metrics['threshold']:.2f} | Probability cutoff used for evaluation |")
    markdown_content.append("")
    
    markdown_content.append("## Business ROI Simulation Details")
    markdown_content.append(f"- **Baseline Loss (Do Nothing):** ${sim['financials']['baseline_loss']:,.2f}")
    markdown_content.append(f"- **Outreach Cost:** ${sim['financials']['campaign_outreach_cost']:,.2f}")
    markdown_content.append(f"- **Discount Payout Cost:** ${sim['financials']['discount_payout_cost']:,.2f}")
    markdown_content.append(f"- **Total Campaign Cost:** ${sim['financials']['total_campaign_cost']:,.2f}")
    markdown_content.append(f"- **Expected Gross Revenue Saved:** ${sim['financials']['revenue_saved']:,.2f}")
    markdown_content.append(f"- **Opportunity Loss (FN):** ${sim['financials']['opportunity_loss']:,.2f}")
    markdown_content.append(f"- **Net Savings:** **${sim['financials']['net_savings']:,.2f}**")
    markdown_content.append(f"- **ROI:** **{sim['financials']['roi_percentage']:.2f}%**\n")
    
    markdown_content.append("### Confusion Matrix Breakdown")
    markdown_content.append(f"- **True Positives (TP):** {sim['confusion_matrix']['tp']} (Churning customers correctly targeted)")
    markdown_content.append(f"- **False Positives (FP):** {sim['confusion_matrix']['fp']} (Non-churning customers targeted - cannibalization cost)")
    markdown_content.append(f"- **False Negatives (FN):** {sim['confusion_matrix']['fn']} (Churning customers missed)")
    markdown_content.append(f"- **True Negatives (TN):** {sim['confusion_matrix']['tn']} (Non-churning customers correctly ignored)")
    
    with open(output_path, "w") as f:
        f.write("\n".join(markdown_content))
    logger.info(f"Model evaluation report written to {output_path}")
