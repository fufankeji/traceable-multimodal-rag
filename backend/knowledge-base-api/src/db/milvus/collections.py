from pymilvus import Collection, CollectionSchema, FieldSchema, DataType

def create_collection(collection_name: str):
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="file_name", dtype=DataType.STRING),
        FieldSchema(name="unique_id", dtype=DataType.STRING),
        FieldSchema(name="upload_status", dtype=DataType.STRING),
    ]
    
    schema = CollectionSchema(fields=fields, description="Collection for storing file metadata")
    
    collection = Collection(name=collection_name, schema=schema)
    return collection

def drop_collection(collection_name: str):
    Collection(name=collection_name).drop()