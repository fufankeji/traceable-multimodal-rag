from pymilvus import Milvus, CollectionSchema, FieldSchema, DataType

class MilvusClient:
    def __init__(self, host: str, port: str, collection_name: str):
        self.client = Milvus(host=host, port=port)
        self.collection_name = collection_name
        self.collection = None

    def create_collection(self):
        if not self.client.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="chunk_text", dtype=DataType.STRING),
                FieldSchema(name="file_name", dtype=DataType.STRING),
                FieldSchema(name="unique_id", dtype=DataType.STRING),
                FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=128),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]
            schema = CollectionSchema(fields=fields, description="Document chunks collection")
            self.client.create_collection(self.collection_name, schema)
            self.collection = self.collection_name

    def insert_vectors(self, vectors: list, chunk_texts: list, file_names: list, unique_ids: list, metadata: list):
        entities = [
            {"name": "chunk_text", "values": chunk_texts},
            {"name": "file_name", "values": file_names},
            {"name": "unique_id", "values": unique_ids},
            {"name": "dense_vector", "values": vectors},
            {"name": "metadata", "values": metadata}
        ]
        self.client.insert(collection_name=self.collection_name, entities=entities)

    def search_vectors(self, query_vectors: list, top_k: int):
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.client.search(collection_name=self.collection_name, query_records=query_vectors, top_k=top_k, params=search_params)
        return results

    def close(self):
        self.client.close()