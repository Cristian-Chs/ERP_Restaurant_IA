from sentence_transformers import SentenceTransformer, util
import torch

#  Cargar modelo solo una vez (rápido y eficiente)
model = SentenceTransformer("all-MiniLM-L6-v2")

#  Función para generar embeddings
def embed_text(text):
    return model.encode(text, convert_to_tensor=True)

#  Calcular similitud entre un plato y todos los demás
def recomendar_similares(plato_objetivo, lista_platos, top_n=5):
    if not lista_platos:
        return []

    # Embedding del plato objetivo
    emb_objetivo = embed_text(plato_objetivo)

    # Embeddings de todos los platos
    emb_lista = model.encode(lista_platos, convert_to_tensor=True)

    #  Calcular similitud coseno
    similitudes = util.cos_sim(emb_objetivo, emb_lista)[0]

    #  Ordenar por similitud
    top_indices = torch.topk(similitudes, k=min(top_n, len(lista_platos))).indices

    #  Devolver platos similares
    return [lista_platos[i] for i in top_indices]
