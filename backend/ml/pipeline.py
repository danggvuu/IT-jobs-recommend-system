import subprocess
import mlflow
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os

def run_full_pipeline():
    print("Running Full Data & ML Pipeline...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    subprocess.run(["python", "recommendation/01_cleaning.py"], cwd=base_dir)
    subprocess.run(["python", "recommendation/02_features.py"], cwd=base_dir)
    subprocess.run(["python", "recommendation/04_evaluate.py"], cwd=base_dir)
    
    # Log to MLFlow
    try:
        with open(os.path.join(base_dir, "database/evaluation_results.json")) as f:
            eval_results = json.load(f)
            
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001"))
        mlflow.set_experiment("job-recommender")
        
        with mlflow.start_run():
            mlflow.log_metric("precision_at_5", eval_results.get("precision@5", 0))
            mlflow.log_metric("ndcg_at_10", eval_results.get("ndcg@10", 0))
            mlflow.log_artifact(os.path.join(base_dir, "database/evaluation_results.json"))
            mlflow.log_artifact(os.path.join(base_dir, "database/feature_matrix.npz"))
            
    except Exception as e:
        print("Error logging to MLflow:", e)

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Chạy lúc 2h sáng mỗi ngày
    scheduler.add_job(run_full_pipeline, 'cron', hour=2, minute=0)
    scheduler.start()
