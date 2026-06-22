"""
Inference script — generate flood risk alerts for current/future timestamps.

Usage:
    python predict.py --kelurahan "Kampung Melayu" --timestamp "2024-02-15 18:00"
    python predict.py --all  # all 15 pilot kelurahan, latest data
    python predict.py --all --save-json static-web-app/public/data/latest_predictions.json
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("predict")

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Static metadata not available in config (elevation from DEMNAS estimates, population from BPS 2023)
_KELURAHAN_META = {
    "Kampung Melayu":      {"elevation_m": 4.5,  "population": 28500},
    "Bidara Cina":         {"elevation_m": 4.1,  "population": 32100},
    "Bukit Duri":          {"elevation_m": 5.8,  "population": 21400},
    "Pengadegan":          {"elevation_m": 5.2,  "population": 18900},
    "Rawajati":            {"elevation_m": 5.5,  "population": 17200},
    "Cipinang Melayu":     {"elevation_m": 8.4,  "population": 24800},
    "Pejaten Timur":       {"elevation_m": 9.1,  "population": 19500},
    "Kebon Baru":          {"elevation_m": 6.2,  "population": 22300},
    "Cawang":              {"elevation_m": 6.8,  "population": 26100},
    "Duren Tiga":          {"elevation_m": 6.5,  "population": 16800},
    "Cililitan":           {"elevation_m": 7.8,  "population": 19200},
    "Balekambang":         {"elevation_m": 7.2,  "population": 14700},
    "Batu Ampar":          {"elevation_m": 7.5,  "population": 17900},
    "Halim Perdanakusuma": {"elevation_m": 9.5,  "population": 12400},
    "Ragunan":             {"elevation_m": 12.3, "population": 22100},
}

# Features that typically indicate lower flood risk (shown as direction "down")
_NEGATIVE_RISK_FEATURES = {"drainage_density", "elevation", "slope", "aspect", "distance_to_river"}


def _risk_label(prob: float) -> str:
    """Map probability to dashboard risk label. 'Bahaya' (model) → 'Awas' (dashboard)."""
    if prob < 0.20:
        return "Aman"
    elif prob < 0.50:
        return "Waspada"
    elif prob < 0.80:
        return "Siaga"
    return "Awas"


def _top_factors(model_obj, feature_cols: list, n: int = 5) -> list:
    """Extract top-N feature importances from an XGBoost model."""
    try:
        importances = model_obj.model.feature_importances_
        names = model_obj.feature_names or feature_cols
        pairs = sorted(zip(names, importances), key=lambda x: -x[1])[:n]
        total = sum(imp for _, imp in pairs) or 1.0
        result = []
        for feat, imp in pairs:
            feat_lower = feat.lower()
            direction = "down" if any(neg in feat_lower for neg in _NEGATIVE_RISK_FEATURES) else "up"
            result.append({
                "feature": feat,
                "importance": round(imp / total, 3),
                "direction": direction,
            })
        return result
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kelurahan", default=None)
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--save-json",
        default=None,
        metavar="PATH",
        help="Export predictions to JSON (readable by the dashboard).",
    )
    args = parser.parse_args()

    from flood_risk.config import MODELS_DIR, PILOT_KELURAHAN
    from flood_risk.data.pipeline import FloodDataPipeline
    from flood_risk.models.xgb_flood import MultiHorizonFloodModel

    ts = args.timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    end = ts[:10]
    start = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    log.info("Loading recent data %s → %s", start, end)
    pipeline = FloodDataPipeline()
    combined = pipeline.build_combined(start=start, end=end)

    model = MultiHorizonFloodModel.load(MODELS_DIR)

    kelurahan_list = (
        list(PILOT_KELURAHAN.keys()) if args.all
        else ([args.kelurahan] if args.kelurahan else list(PILOT_KELURAHAN.keys()))
    )

    from flood_risk.models.xgb_flood import _EXCLUDE_COLS
    import numpy as np

    json_records = []

    for kel in kelurahan_list:
        subset = combined[combined["kelurahan"] == kel] if "kelurahan" in combined.columns else combined
        if subset.empty:
            log.warning("No data for %s", kel)
            continue

        feature_cols = [c for c in subset.columns if c not in _EXCLUDE_COLS and c != "kelurahan"]
        X = subset[feature_cols].select_dtypes(include=[np.number]).tail(1)

        alerts = model.predict_all(X)
        print(f"\n{'='*50}")
        print(f"Kelurahan: {kel} | Time: {X.index[-1]}")
        for h in [6, 12, 24]:
            prob = alerts[f"prob_{h}h"].iloc[0]
            level = _risk_label(prob)
            bar = "█" * int(prob * 20) + "░" * (20 - int(prob * 20))
            print(f"  {h:2d}h: [{bar}] {prob:.1%}  →  {level}")

        if args.save_json:
            cfg = PILOT_KELURAHAN[kel]
            meta = _KELURAHAN_META.get(kel, {"elevation_m": None, "population": None})
            # Use 24h model's top factors as representative (most strategic horizon)
            factors = _top_factors(model.models[24], feature_cols)
            record = {
                "name": kel,
                "kecamatan": cfg["kec"],
                "lat": cfg["lat"],
                "lon": cfg["lon"],
                "elevation_m": meta["elevation_m"],
                "population": meta["population"],
                "predictions": {
                    f"{h}h": {
                        "probability": round(float(alerts[f"prob_{h}h"].iloc[0]), 4),
                        "risk_level": _risk_label(float(alerts[f"prob_{h}h"].iloc[0])),
                    }
                    for h in [6, 12, 24]
                },
                "top_factors": factors,
            }
            json_records.append(record)

    if args.save_json and json_records:
        output = {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data_source": "model",
            "kelurahan": json_records,
        }
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
        log.info("Predictions saved → %s", out_path)


if __name__ == "__main__":
    main()
