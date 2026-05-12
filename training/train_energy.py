"""
Train building energy model (ENB2012 dataset).

Dataset: https://archive.ics.uci.edu/ml/datasets/Energy+efficiency
Expected file: training/data/raw/ENB2012_data.xlsx
Outputs:
    - artifacts/energy_model.keras
    - artifacts/energy_scaler.joblib
"""
import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_PATH = "training/data/raw/ENB2012_data.xlsx"
ARTIFACTS_DIR = "artifacts/"
RANDOM_SEED = 42

FEATURES = ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8"]
TARGETS = ["Y1", "Y2"]

tf.random.set_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_data(path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_excel(path).dropna()
    X = df[FEATURES].values.astype(np.float32)
    y = df[TARGETS].values.astype(np.float32)
    return X, y


def build_model(input_dim: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation="relu", input_shape=(input_dim,)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(2),  
    ], name="energy_model")

    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
    
    return model


def train() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print(f"Loading data from {DATA_PATH} ...")
    X, y = load_data(DATA_PATH)
    print(f"  {X.shape[0]} samples, {X.shape[1]} features, {y.shape[1]} targets")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    model = build_model(X_train.shape[1])
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=25, restore_best_weights=True
        ),
    ]

    print("\nTraining ...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=400,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    model_path = os.path.join(ARTIFACTS_DIR, "energy_model.keras")
    scaler_path = os.path.join(ARTIFACTS_DIR, "energy_scaler.joblib")
    model.save(model_path)
    joblib.dump(scaler, scaler_path)

    best_val_mae = min(history.history["val_mae"])
    print(f"\nDone.")
    print(f"  Best val MAE: {best_val_mae:.4f} kWh/m²")
    print(f"  Model  → {model_path}")
    print(f"  Scaler → {scaler_path}")


if __name__ == "__main__":
    train()
