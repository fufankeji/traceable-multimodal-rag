from typing import List
import numpy as np

def generate_dense_vector(data: List[float]) -> np.ndarray:
    """
    生成稠密向量
    :param data: 输入数据列表
    :return: 返回生成的稠密向量
    """
    return np.array(data, dtype=np.float32)

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    归一化稠密向量
    :param vector: 输入的稠密向量
    :return: 返回归一化后的稠密向量
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    计算两个稠密向量之间的余弦相似度
    :param vec_a: 第一个稠密向量
    :param vec_b: 第二个稠密向量
    :return: 返回余弦相似度
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)