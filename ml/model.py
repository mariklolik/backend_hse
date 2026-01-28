import numpy as np
import pickle
import mlflow
from mlflow.sklearn import log_model, load_model as mlflow_load_model
from sklearn.linear_model import LogisticRegression

MODEL_NAME = "moderation-model"


def train_model() -> LogisticRegression:
    np.random.seed(42)
    n_samples = 1000

    is_verified = np.random.randint(0, 2, n_samples)
    images = np.random.randint(0, 11, n_samples)
    desc_len = np.random.randint(50, 1001, n_samples)
    category = np.random.randint(0, 100, n_samples)

    violation = (
        (is_verified == 0) &
        (images < 3) &
        (desc_len < 200)
    ).astype(int)

    noise_mask = np.random.random(n_samples) < 0.1
    violation[noise_mask] = 1 - violation[noise_mask]

    X = np.column_stack([
        is_verified,
        images / 10,
        desc_len / 1000,
        category / 100,
    ])

    model = LogisticRegression(random_state=42)
    model.fit(X, violation)
    return model


def save_model(model: LogisticRegression, path: str = "model.pkl") -> None:
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model(path: str = "model.pkl") -> LogisticRegression:
    with open(path, "rb") as f:
        return pickle.load(f)


def register_model(model: LogisticRegression) -> None:
    mlflow.set_tracking_uri("./mlruns")
    with mlflow.start_run():
        log_model(model, "model", registered_model_name=MODEL_NAME)


def promote_to_production() -> None:
    mlflow.set_tracking_uri("./mlruns")
    client = mlflow.MlflowClient()
    latest = client.get_latest_versions(MODEL_NAME, stages=["None"])
    if latest:
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=latest[0].version,
            stage="Production",
        )


def load_from_mlflow(stage: str = "Production") -> LogisticRegression:
    mlflow.set_tracking_uri("./mlruns")
    model_uri = f"models:/{MODEL_NAME}/{stage}"
    return mlflow_load_model(model_uri)
