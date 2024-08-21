# Author: Lintao
import os

from utils.database import KnowledgeDB
from utils.embedding import LocalEmbedding
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import json
import logging


# doc按照最大子词拆分，每块进行embedding，按照hash->embedding的方式将embedding存储在向量数据库，需要搜索的时候按照embedding在向量数据库中搜索，用余弦相似度的方式计算相关性，返回最相关的k条，作为prompt的一部分进行rag


class KnowledgeItem:
    def __init__(self, text: str, score: float = 0.0, md5_hash: str = None):
        self.text = text
        self.md5_hash = md5_hash or hashlib.md5(text.encode('utf-8')).hexdigest()
        self.score = score

    def __str__(self):
        return f"KnowledgeItem(text={self.text}, score={self.score}, md5_hash={self.md5_hash})"

    def __repr__(self):
        return self.__str__()

    def to_json_str(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json_str(cls, json_str):
        # 函数作用：将json字符串转换为KnowledgeItem对象，@classmethod表示这是一个类方法，可以直接通过类调用，cls表示类本身
        json_dict = json.loads(json_str)
        return cls(**json_dict)


class KnowledgeRetrieval:
    def __init__(self, embedding_model, knowledge_db_path, vector_db_path):
        self.embedding_model = embedding_model
        self.knowledge_db_path = knowledge_db_path
        self.vector_db_path = vector_db_path
        self.knowledge_db = KnowledgeDB(knowledge_db_path)
        # TODO 为了实现更好的效果，可以考虑使用faiss库来实现向量数据库
        self.vector_db = KnowledgeDB(vector_db_path)

    def add_knowledge_item(self, text: str, score: float = 0.0):
        item = KnowledgeItem(text, score)
        embedding = self.embedding_model.embed_text(text)
        self.vector_db.set(item.md5_hash, embedding)
        self.knowledge_db.set(item.md5_hash, item.to_json_str())

    def delete_knowledge_item(self, md5_hash: str):
        self.knowledge_db.delete(md5_hash)
        self.vector_db.delete(md5_hash)

    def update_knowledge_item(self, md5_hash: str, text: str, score: float = 0.0):
        self.delete_knowledge_item(md5_hash)
        self.add_knowledge_item(text, score)

    def get_knowledge_item(self, md5_hash: str):
        return KnowledgeItem.from_json_str(self.knowledge_db.get(md5_hash))

    def clear_knowledge_db(self):
        # 清空知识库
        self.knowledge_db.clear()
        # 删除本地文件
        if os.path.exists(self.knowledge_db_path):
            os.remove(self.knowledge_db_path)

    def clear_vector_db(self):
        # 清空向量数据库
        self.vector_db.clear()
        # 删除本地文件
        if os.path.exists(self.vector_db_path):
            os.remove(self.vector_db_path)

    def search_knowledge(self, query: str, k: int):
        query_embedding = np.array(self.embedding_model.embed_text(query)).reshape(1, -1)
        keys = self.vector_db.db.getall()
        similarities = []
        for key in keys:
            embedding = np.array(self.vector_db.get(key)).reshape(1, -1)
            similarity = cosine_similarity(query_embedding, embedding)[0][0]
            similarities.append((key, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_k_keys = [key for key, _ in similarities[:k]]
        results = [self.get_knowledge_item(key) for key in top_k_keys]
        logging.info(f"top k knowledge items: {results}")
        return results


HF_EMBEDDING_MULTIMINILM = {
    # https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "dim": 384,
    "hf_url": "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}
# 示例用法
if __name__ == "__main__":
    # config logging
    logging.basicConfig(level=logging.DEBUG)
    embedding = LocalEmbedding(model_name=HF_EMBEDDING_MULTIMINILM["model_id"],
                               vector_width=HF_EMBEDDING_MULTIMINILM["dim"])
    knowledge_db_path = "user_data/lintao/knowledge_db.pkl"
    vector_db_path = "user_data/lintao/vector_db.pkl"

    knowledge_retrieval = KnowledgeRetrieval(embedding, knowledge_db_path, vector_db_path)

    # 添加知识项
    knowledge_retrieval.add_knowledge_item("人工智能是计算机科学的一个分支", 0.9)
    knowledge_retrieval.add_knowledge_item("机器学习是人工智能的一个子集", 0.8)

    # 搜索知识项
    results = knowledge_retrieval.search_knowledge("什么是人工智能", 2)
    for result in results:
        print(result)
