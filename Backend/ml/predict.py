import os
import sys
import django
import pickle
import numpy as np
from typing import List, Tuple, Dict, Any

# --- Configuración de Entorno y Django ---

# 👇 Añade la carpeta raíz del proyecto (la que contiene 'backend' y 'ml') al PYTHONPATH.
# Si 'predict.py' está en 'ml/predict.py', esta ruta sube dos niveles (..).
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT_DIR)

# 👇 Configura Django correctamente (Corregido: 'backend.settings' sin el espacio extra)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from bot.models import Order

# ----------------------------------------------------------------------
# Funciones de Soporte
# ----------------------------------------------------------------------

def cargar_modelo() -> Dict[str, Any] | None:
    """Carga el modelo de recomendación y los encoders."""
    modelo_path = os.path.join(os.path.dirname(__file__), "..", "modelo_recomendacion.pkl")
    if not os.path.exists(modelo_path):
        print("⚠️ No se encontró el archivo modelo_recomendacion.pkl")
        return None
    try:
        with open(modelo_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"⚠️ Error al cargar el modelo: {e}")
        return None

def recomendar_popularidad(top_n: int = 5) -> List[str]:
    """Recomendación de fallback: devuelve los platos más populares."""
    pedidos = Order.objects.all()
    conteo = {}
    for pedido in pedidos:
        # Usar .item para obtener el nombre del plato
        conteo[pedido.item] = conteo.get(pedido.item, 0) + 1
        
    # Ordenar por conteo y devolver los nombres de los platos
    return [
        plato for plato, _ in 
        sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:top_n]
    ]

# ----------------------------------------------------------------------
# Función Principal de Recomendación (ML)
# ----------------------------------------------------------------------

def recomendar_ml(telegram_id: int, top_n: int = 5) -> List[str]:
    """
    Genera recomendaciones personalizadas usando Factorización Matricial (SVD).
    
    Requiere que 'user_latent_matrix' esté guardado en el archivo .pkl.
    """
    modelo_data = cargar_modelo()
    if modelo_data is None:
        print("Usando recomendación por popularidad debido a que el modelo no está disponible.")
        return recomendar_popularidad(top_n)

    svd = modelo_data["svd"]
    user_encoder = modelo_data["user_encoder"]
    item_encoder = modelo_data["item_encoder"]
    
    # Nuevo: Cargar la matriz de usuarios latentes
    user_latent_matrix = modelo_data.get("user_latent_matrix")
    if user_latent_matrix is None:
        print("⚠️ 'user_latent_matrix' no se encontró en el modelo. Usando popularidad.")
        return recomendar_popularidad(top_n)

    # 1. Validar si el usuario está en el modelo
    if telegram_id not in user_encoder.classes_:
        print(f"Usuario {telegram_id} nuevo o no registrado. Usando popularidad.")
        return recomendar_popularidad(top_n)

    user_id = user_encoder.transform([telegram_id])[0]
    
    # Si el user_id está fuera del rango de la matriz latente (error al entrenar/guardar)
    if user_id >= user_latent_matrix.shape[0]:
        print("⚠️ Error de índice: user_id fuera del rango de la matriz latente.")
        return recomendar_popularidad(top_n)

    # Obtener el vector latente del usuario (P_u)
    # user_vector es de forma (1, k)
    user_vector = user_latent_matrix[user_id].reshape(1, -1)

    # Obtener todos los platos únicos que el modelo conoce
    platos_modelo = item_encoder.classes_
    recomendaciones: List[Tuple[str, float]] = []

    # 2. Iterar sobre todos los ítems y calcular la puntuación
    for plato in platos_modelo:
        try:
            item_id = item_encoder.transform([plato])[0]
            
            # Obtener el vector latente del ítem (Q_i)
            # svd.components_ es (k, N_ITEMS). item_vector es de forma (k, 1)
            item_vector = svd.components_[:, item_id].reshape(-1, 1)
            
            # Calcular la puntuación: P_u * Q_i^T
            # np.dot( (1, k), (k, 1) ) = (1, 1)
            score = np.dot(user_vector, item_vector)[0][0]
            
            recomendaciones.append((plato, float(score)))
        except Exception as e:
            # Esto puede ocurrir si un plato está en el encoder pero no tiene vector latente
            # o si hay un error en el cálculo, es mejor omitir el plato.
            print(f"Error al procesar el plato {plato}: {e}")
            continue

    # 3. Eliminar los platos que el usuario ya pidió (Opcional, pero recomendado)
    pedidos_usuario = Order.objects.filter(telegram_id=telegram_id).values_list("item", flat=True)
    platos_excluir = set(pedidos_usuario)
    
    recomendaciones_filtradas = [
        (plato, score) for plato, score in recomendaciones 
        if plato not in platos_excluir
    ]

    # 4. Ordenar y devolver el top N
    recomendaciones_filtradas.sort(key=lambda x: x[1], reverse=True)
    return [plato for plato, _ in recomendaciones_filtradas[:top_n]]

# ----------------------------------------------------------------------
# Ejecución (Para Pruebas)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Test de Recomendaciones (predict.py) ---")
    
    # 🔄 Obtener todos los clientes automáticamente para probar
    clientes = Order.objects.values_list("telegram_id", flat=True).distinct()
    
    if not clientes:
        print("No hay clientes en la base de datos para probar la recomendación.")
        # Ejemplo de popularidad si no hay clientes
        print("\nRecomendación por Popularidad (Fallback):")
        print(recomendar_popularidad(5))
        sys.exit(0)

    for telegram_id in clientes:
        print(f"\n--- Probando cliente ID: {telegram_id} ---")
        try:
            recomendaciones = recomendar_ml(telegram_id, top_n=3)
            if recomendaciones:
                print(f"✨ Recomendaciones ML:")
                for plato in recomendaciones:
                    print(f"🍽️ {plato}")
            else:
                print(f"⚠️ No se pudieron generar recomendaciones ML para cliente {telegram_id}.")
                print("Usando Fallback...")
                rec_pop = recomendar_popularidad(3)
                print(f"✨ Recomendaciones Popularidad:")
                for plato in rec_pop:
                    print(f"🍽️ {plato}")

        except Exception as e:
            print(f"❌ Un error inesperado ocurrió para el cliente {telegram_id}: {e}")