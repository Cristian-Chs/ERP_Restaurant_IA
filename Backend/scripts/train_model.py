import os
import sys
import django
import pandas as pd
import pickle
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import csr_matrix

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order, Rating

def train_model():
    orders = Order.objects.all().values("telegram_id", "item")
    df = pd.DataFrame(list(orders))

    if df.empty:
        print(" No hay pedidos en la base de datos. Entrenamiento cancelado.")
        return

    # si tienes Rating, lo ideal es usarlo; por ahora, rating fijo
    df["rating"] = 5  

    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()

    df["user_id"] = user_encoder.fit_transform(df["telegram_id"])
    df["item_id"] = item_encoder.fit_transform(df["item"])

    user_item_matrix = csr_matrix(
        (df["rating"], (df["user_id"], df["item_id"]))
    )

    num_items = user_item_matrix.shape[1]
    if num_items < 2:
        print(f" No hay suficientes platos únicos para entrenar (solo {num_items}).")
        return

    n_components = min(20, num_items - 1)
    svd = TruncatedSVD(n_components=n_components)
    user_latent_matrix = svd.fit_transform(user_item_matrix)

    modelo_path = os.path.join(os.path.dirname(__file__), "modelo_recomendacion.pkl")
    with open(modelo_path, "wb") as f:
        pickle.dump({
            "svd": svd,
            "user_encoder": user_encoder,
            "item_encoder": item_encoder,
            "user_latent_matrix": user_latent_matrix,
        }, f)

    print(f" Modelo entrenado y guardado en {modelo_path}")

if __name__ == "__main__":
    train_model()
