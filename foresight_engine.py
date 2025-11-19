"""
Foresight Engine
================
Simulates next state deltas given current memory + directive trajectory.
Predictive simulation for forward optimization.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List


FUTURES_PATH = "futures/"
MEMORY_PATH = "memory_store.json"


def load_memory() -> Dict[str, Any]:
    """Load current memory state"""
    try:
        with open(MEMORY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"goal": "Awaiting injection", "quantum": {}, "action": None}


def predict_next_state() -> Dict[str, Any]:
    """
    Predict next system state based on current memory.
    
    Returns:
        Predicted state
    """
    mem = load_memory()
    
    # Get current quantum metrics
    drift = mem.get("quantum", {}).get("drift", 0)
    fidelity = mem.get("quantum", {}).get("fidelity", 1.0)
    coherence = mem.get("quantum", {}).get("coherence", 1.0)
    loop_depth = mem.get("loop_depth", 0)
    
    # Prediction logic
    prediction = {
        "timestamp": time.time(),
        "current_state": {
            "drift": drift,
            "fidelity": fidelity,
            "coherence": coherence,
            "depth": loop_depth
        }
    }
    
    # Predict based on drift
    if drift > 0.05:
        prediction["future_action"] = "spawn harmonizer"
        prediction["future_loop_depth"] = loop_depth + 1
        prediction["risk"] = "moderate"
        prediction["recommendation"] = "Engage correction sequence"
        
        # Predict drift trend
        prediction["predicted_drift"] = min(drift * 1.1, 0.15)
        prediction["confidence"] = 0.75
    
    elif drift > 0.03:
        prediction["future_action"] = "monitor"
        prediction["future_loop_depth"] = loop_depth
        prediction["risk"] = "low"
        prediction["recommendation"] = "Continue monitoring"
        
        prediction["predicted_drift"] = drift * 1.05
        prediction["confidence"] = 0.85
    
    else:
        prediction["future_action"] = "idle"
        prediction["future_loop_depth"] = 0
        prediction["risk"] = "minimal"
        prediction["recommendation"] = "System stable"
        
        prediction["predicted_drift"] = drift * 0.95
        prediction["confidence"] = 0.90
    
    # Predict coherence decay
    if coherence < 0.90:
        prediction["coherence_warning"] = True
        prediction["future_coherence"] = max(coherence * 0.98, 0.85)
    else:
        prediction["coherence_warning"] = False
        prediction["future_coherence"] = coherence * 0.99
    
    return prediction


def save_prediction(prediction: Dict[str, Any], prediction_id: str = None) -> str:
    """
    Save prediction to futures directory.
    
    Args:
        prediction: Prediction data
        prediction_id: Optional ID (auto-generated if None)
        
    Returns:
        Prediction ID
    """
    # Ensure futures directory exists
    Path(FUTURES_PATH).mkdir(exist_ok=True)
    
    # Generate ID if not provided
    if prediction_id is None:
        prediction_id = f"pred_{int(time.time())}"
    
    # Save prediction
    prediction_path = Path(FUTURES_PATH) / f"{prediction_id}.json"
    
    with open(prediction_path, 'w') as f:
        json.dump(prediction, f, indent=2)
    
    print(f"[⟳] Prediction saved: {prediction_path}")
    
    return prediction_id


def load_prediction(prediction_id: str) -> Dict[str, Any]:
    """
    Load a saved prediction.
    
    Args:
        prediction_id: Prediction ID
        
    Returns:
        Prediction data
    """
    prediction_path = Path(FUTURES_PATH) / f"{prediction_id}.json"
    
    with open(prediction_path, 'r') as f:
        return json.load(f)


def compare_prediction_to_actual() -> Dict[str, Any]:
    """
    Compare most recent prediction to actual outcome.
    
    Returns:
        Comparison results
    """
    futures_dir = Path(FUTURES_PATH)
    
    if not futures_dir.exists():
        return {"error": "No predictions available"}
    
    # Get most recent prediction
    predictions = sorted(
        futures_dir.glob("pred_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not predictions:
        return {"error": "No predictions found"}
    
    # Load prediction
    with open(predictions[0], 'r') as f:
        prediction = json.load(f)
    
    # Load current actual state
    actual = load_memory()
    
    # Compare
    comparison = {
        "prediction_id": predictions[0].stem,
        "predicted": {
            "action": prediction.get("future_action"),
            "depth": prediction.get("future_loop_depth"),
            "drift": prediction.get("predicted_drift")
        },
        "actual": {
            "action": actual.get("action"),
            "depth": actual.get("loop_depth", 0),
            "drift": actual.get("quantum", {}).get("drift")
        }
    }
    
    # Calculate accuracy
    accuracy = []
    
    if comparison["predicted"]["action"] == comparison["actual"]["action"]:
        accuracy.append("action")
    
    if comparison["predicted"]["depth"] == comparison["actual"]["depth"]:
        accuracy.append("depth")
    
    comparison["accuracy"] = len(accuracy) / 3.0  # 3 metrics
    comparison["matched_metrics"] = accuracy
    
    return comparison


def generate_forecast_report() -> str:
    """
    Generate comprehensive forecast report.
    
    Returns:
        Report text
    """
    print("\n" + "="*60)
    print("Foresight Engine - Forecast Report")
    print("="*60 + "\n")
    
    # Generate prediction
    prediction = predict_next_state()
    prediction_id = save_prediction(prediction)
    
    # Format report
    report = []
    report.append("Current State:")
    report.append(f"  Drift: {prediction['current_state']['drift']:.4f}")
    report.append(f"  Coherence: {prediction['current_state']['coherence']:.4f}")
    report.append(f"  Depth: {prediction['current_state']['depth']}")
    
    report.append("\nPredicted Next State:")
    report.append(f"  Action: {prediction['future_action']}")
    report.append(f"  Depth: {prediction['future_loop_depth']}")
    report.append(f"  Predicted Drift: {prediction['predicted_drift']:.4f}")
    report.append(f"  Risk Level: {prediction['risk']}")
    
    report.append(f"\nConfidence: {prediction['confidence'] * 100:.1f}%")
    report.append(f"Recommendation: {prediction['recommendation']}")
    
    if prediction.get("coherence_warning"):
        report.append("\n⚠️  WARNING: Coherence degradation detected")
    
    report.append(f"\nPrediction ID: {prediction_id}")
    
    # Check historical accuracy
    comparison = compare_prediction_to_actual()
    if "accuracy" in comparison:
        report.append(f"\nHistorical Accuracy: {comparison['accuracy'] * 100:.1f}%")
        report.append(f"Matched Metrics: {', '.join(comparison['matched_metrics'])}")
    
    report_text = "\n".join(report)
    print(report_text)
    print("\n" + "="*60 + "\n")
    
    return report_text


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        generate_forecast_report()
    elif len(sys.argv) > 1 and sys.argv[1] == "--compare":
        comparison = compare_prediction_to_actual()
        print(json.dumps(comparison, indent=2))
    else:
        # Default: predict and save
        prediction = predict_next_state()
        prediction_id = save_prediction(prediction)
        print(json.dumps(prediction, indent=2))
        print(f"\n[⟳] Future state prediction complete: {prediction_id}")
