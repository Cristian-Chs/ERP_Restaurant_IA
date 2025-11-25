import pandas as pd
import numpy as np
import pickle
from scipy.sparse.linalg import svds # SVD para matrices dispersas
from scipy.sparse import csr_matrix # Para manejar matrices eficientemente

# Cargar datos exportados
df = pd.read_csv("orders.csv")

# --- 1. Crear la Matriz Usuario-Ítem (R) ---
# Se pivotea el DataFrame para tener usuarios en filas, ítems en columnas y ratings en valores.
R_df = df.pivot_table(index='telegram_id', columns='item', values='rating').fillna(0)

# Obtener los nombres de filas y columnas para futuras predicciones
user_ids = R_df.index
item_names = R_df.columns

# Convertir la matriz de Pandas a una matriz SciPy esparsa (CSR)
R_sparse = csr_matrix(R_df.values)

# --- 2. Entrenar el modelo SVD ---
# Descomponer la matriz R en tres matrices: U, Sigma (diagonal), y V transpuesta (V_t)
# k = número de factores latentes (puedes ajustar este número, 50 es un buen inicio)
K = 50 
U, sigma, Vt = svds(R_sparse, k=K)

# Convertir sigma (vector) en una matriz diagonal para la reconstrucción
sigma_diag = np.diag(sigma)

# El "modelo" entrenado es el conjunto de estas tres matrices y los mapeos
modelo_svd = {
    'U': U,
    'Sigma_diag': sigma_diag,
    'Vt': Vt,
    'user_ids': user_ids,
    'item_names': item_names,
    # Puedes añadir la media de calificaciones para usarla en la predicción (opcional)
}

# --- 3. Guardar el "modelo" entrenado ---
with open("modelo_recomendacion_scipy_svd.pkl", "wb") as f:
    pickle.dump(modelo_svd, f)

print("Modelo SVD entrenado y guardado usando SciPy en modelo_recomendacion_scipy_svd.pkl")

# --- (Opcional) Ejemplo de reconstrucción para verificar ---
# R_pred = np.dot(np.dot(U, sigma_diag), Vt)
# print("\nMatriz de predicción reconstruida (primeras 5x5):\n", R_pred[:5, :5])