from sentence_transformers import SentenceTransformer

import time
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.models import PointStruct

# https://huggingface.co/sentence-transformers/msmarco-distilroberta-base-v2
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

model = SentenceTransformer(MODEL_NAME)
VECTOR_DIM_SIZE = model.get_sentence_embedding_dimension() # the size of msmarco-distilroberta-base-v2

qdrantClient = QdrantClient("localhost", port=6333)
qdrantClient.recreate_collection(
    collection_name="text_data",
    vectors_config=VectorParams(size=VECTOR_DIM_SIZE, distance=Distance.COSINE),
)

# Corpus with example sentences
corpus_list = [
          'Một người đàn ông đang ăn thức ăn.',
           'Một người đàn ông đang ăn một miếng bánh mì.',
           'Cô gái đang bế một đứa bé.',
           'Một người đàn ông đang cưỡi ngựa.',
           'Một người phụ nữ đang chơi violin.',
           'Hai người đàn ông đẩy xe xuyên rừng.',
           'Một người đàn ông đang cưỡi một con ngựa trắng trên một khu đất kín.',
           'Một con khỉ đang chơi trống.',
           'Một con báo đang chạy theo con mồi.',
           'Gia đình là tình yêu.',
           'Tình yêu ở mọi nơi.'
          ]

start = time.time()

enums = enumerate(corpus_list)
for id, corpus in enums:
    ids = str(id)
    print(ids + " = " + corpus)

    # 1.147646188735962
    corpus_embedding = model.encode(corpus, convert_to_tensor=True).tolist()
    #print(corpus_embedding)

    operation_info = qdrantClient.upsert(
        collection_name="text_data",
        wait=True,
        points=[PointStruct(id=id, vector=corpus_embedding, payload={"corpus": corpus})]
    )

end = time.time()
print("=> execute ",end - start)

# Query sentences:
queries = ['tình yêu ở khắp mọi nơi ?','Một người đàn ông đang ăn mì ống.', 'Ai đó trong trang phục khỉ đột đang chơi một bộ trống.', 'Báo là loài động vật trên nhanh nhất hành tinh.']

# Find the closest 5 sentences of the corpus_list for each query sentence based on cosine similarity
top_k = min(5, len(corpus_list))
for query in queries:
    query_embedding = model.encode(query, convert_to_tensor=True).tolist()

    print("\n\n======================\n\n")
    print("Query:", query)
    print("\nTop 5 most similar sentences in corpus_list:")

    # Alternatively, we can also use util.semantic_search to perform cosine similarty + topk
    search_result = qdrantClient.query_points(
        collection_name="text_data",
        query=query_embedding, 
        limit=3
    )
    
    for rs in search_result:
        print(rs)