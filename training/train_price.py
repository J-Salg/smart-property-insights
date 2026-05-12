"""
Train house price model (Ames dataset).

Dataset: https://www.kaggle.com/datasets/prevek18/ames-housing-dataset
Expected file: training/data/raw/AmesHousing.csv
Outputs: 
    - artifacts/price_model.keras
    - artifacts/price_scaler.joblib
"""
import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_PATH = "training/data/raw/AmesHousing.csv"
ARTIFACTS_DIR = "artifacts/"
RANDOM_SEED = 42

FEATURES = [
    "Overall Qual",   
    "Gr Liv Area",    
    "Year Built",     
    "Garage Cars",    
    "Total Bsmt SF",  
    "Full Bath",      
    "Bedroom AbvGr",  
    "Lot Area",       
]
TARGET = "SalePrice"

tf.random.set_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_data(path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    df = df[FEATURES + [TARGET]].dropna()
    X = df[FEATURES].values.astype(np.float32)
    y = np.log1p(df[TARGET].values.astype(np.float32))  
    return X, y


def build_model(input_dim: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation="relu", input_shape=(input_dim,)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1),
    ], name="price_model")
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
    return model


def train() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print(f"Loading data from {DATA_PATH} ...")
    X, y = load_data(DATA_PATH)
    print(f"  {X.shape[0]} samples, {X.shape[1]} features")

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
            monitor="val_loss", patience=20, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", patience=10, factor=0.5, min_lr=1e-5
        ),
    ]

    print("\nTraining ...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=300,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    model_path = os.path.join(ARTIFACTS_DIR, "price_model.keras")
    scaler_path = os.path.join(ARTIFACTS_DIR, "price_scaler.joblib")
    model.save(model_path)
    joblib.dump(scaler, scaler_path)

    best_val_mae = min(history.history["val_mae"])
    approx_dollar_mae = np.expm1(best_val_mae)

    print(f"\nDone.")
    print(f"  Best val MAE (log space): {best_val_mae:.4f}")
    print(f"  Approx. dollar MAE:       ${approx_dollar_mae:,.0f}")
    print(f"  Model  → {model_path}")
    print(f"  Scaler → {scaler_path}")


if __name__ == "__main__":
    train()
