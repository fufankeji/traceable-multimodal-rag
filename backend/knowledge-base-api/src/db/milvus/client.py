from pymilvus import Milvus, CollectionSchema, FieldSchema, DataType

class MilvusClient:
    def __init__(self, host: str, port: str):
        self.client = Milvus(host=host, port=port)

    def create_collection(self, collection_name: str, fields: list):
        schema = CollectionSchema(fields=fields, description="Collection for storing data")
        self.client.create_collection(collection_name, schema)

    def insert_data(self, collection_name: str, records: list):
        return self.client.insert(collection_name, records)

    def search(self, collection_name: str, query_vectors: list, top_k: int):
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        return self.client.search(collection_name, query_vectors, top_k, search_params)

    def delete_collection(self, collection_name: str):
        self.client.drop_collection(collection_name)

    def close(self):
        self.client.close()