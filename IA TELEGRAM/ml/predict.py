# predict.py
import pickle
import numpy as np
import pandas as pd

def recomendar_items(telegram_id, top_n=5):
    # --- 1. Cargar el modelo entrenado ---
    with open("modelo_recomendacion_scipy_svd.pkl", "rb") as f:
        modelo = pickle.load(f)

    U = modelo["U"]
    Sigma_diag = modelo["Sigma_diag"]
    Vt = modelo["Vt"]
    user_ids = modelo["user_ids"]
    item_names = modelo["item_names"]

    # --- 2. Reconstruir la matriz de predicciones ---
    R_pred = np.dot(np.dot(U, Sigma_diag), Vt)

    # --- 3. Ubicar el índice del usuario ---
    if telegram_id not in user_ids:
        print(f"Usuario {telegram_id} no encontrado en el modelo.")
        return []

    user_index = list(user_ids).index(telegram_id)

    # --- 4. Obtener las predicciones para ese usuario ---
    user_predictions = R_pred[user_index]

    # --- 5. Ordenar ítems por score (mayor a menor) ---
    pred_df = pd.DataFrame({
        "item": item_names,
        "pred_score": user_predictions
    }).sort_values("pred_score", ascending=False)

    # --- 6. Seleccionar los Top-N recomendados ---
    recomendaciones = pred_df.head(top_n)

    return recomendaciones

# --- Ejemplo de uso ---
if __name__ == "__main__":
    telegram_id = 123456789  # reemplaza con el ID real del cliente
    recomendaciones = recomendar_items(telegram_id, top_n=5)
    print("\nRecomendaciones para el usuario:")
    print(recomendaciones)
