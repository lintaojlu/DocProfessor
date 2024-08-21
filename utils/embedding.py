# Author: Lintao

"""
用来向量化文本的组件，按照config，加载本地的huggingface权重并进行推理
"""
import os
import logging
import requests
from sentence_transformers import SentenceTransformer
from typing import Any, Dict, List
from pathlib import Path

MODEL_BASE_PATH = Path(__file__).resolve().parents[1] / 'lintao' / "models"
HF_TOKEN = "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"
HF_EMBEDDING_MULTIMINILM = {
    # https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    "headers": {"Authorization": f"Bearer {HF_TOKEN}"},
    "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "dim": 384,
    "url": "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}


class SingletonEmbeddingModel(type):
    """
    用来实现单例模式的基类
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonEmbeddingModel, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseEmbeddingModel(metaclass=SingletonEmbeddingModel):
    """
    所有向量化模型的基类，必须实现embed_text方法
    """
    # 必须实现的一个属性:model_name
    model_name: str = None

    def embed_text(self, input_string: str) -> List[float]:
        pass


class LocalEmbedding(BaseEmbeddingModel):
    """
    用来向量化文本的组件，按照config，加载本地的huggingface权重并进行推理
    """

    def __init__(self, model_name: str = "uer/sbert-base-chinese-nli", vector_width: int = 768):
        # 初始化EMBEDDING模块 LOGGER配置
        self.logger = logging.getLogger("EMBEDDING")
        #####################################
        # 转化model_name为huggingface的本地文件夹,
        # 例: uer/sbert-base-chinese-nli  ==> uer_sbert-base-chinese-nli
        #####################################
        self.model_path_hf = MODEL_BASE_PATH / "embedding" / model_name.replace("/", "_")
        self.model_name = model_name
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # 加载模型到本地
        if not os.path.exists(self.model_path_hf):
            self.logger.info(f"模型{model_name}的权重不存在，正在下载... 目标路径：{self.model_path_hf}")
            model = SentenceTransformer(model_name)
            model.save(str(self.model_path_hf))
            self.model = model
        else:
            self.logger.info(f"模型{model_name}的权重已存在，加载本地权重... 路径：{self.model_path_hf}")
            self.model = SentenceTransformer(self.model_path_hf)

        # 获取并检查向量宽度
        vector_width_from_weights: int = self.model.get_sentence_embedding_dimension()  # e.g: 768
        assert vector_width == vector_width_from_weights, f"模型{model_name}的向量宽度为{vector_width_from_weights}，与用户指定的{vector_width}不符"
        self.vector_width = vector_width

        self.logger.info(f"模型{model_name}的权重已加载，向量宽度为{vector_width_from_weights}")

    def embed_text(self, input_string: str):
        try:
            vector = self.model.encode(input_string).tolist()
        except Exception as e:
            self.logger.error(f"向量化文本时出现错误：{e}")
            vector = [0.0] * self.vector_width
        return vector


class HuggingFaceEmbedding(BaseEmbeddingModel):
    """
    用来向量化文本的组件，按照config，向Web API请求huggingface嵌入向量
    """

    def __init__(self, model_name: str = "uer/sbert-base-chinese-nli", vector_width: int = 768):
        """embedding model设置"""
        self.logger = logging.getLogger("EMBEDDING")
        # huggingface embedding model
        self.hf_api_url = HF_EMBEDDING_MULTIMINILM["url"]
        self.hf_headers = HF_EMBEDDING_MULTIMINILM["headers"]
        self.hf_dim = HF_EMBEDDING_MULTIMINILM["dim"]

        self.vector_width = vector_width
        self.model_name = model_name
        self.logger.info(f"模型{model_name}WEB EMBED API 已经初始化")

    def embed_text(self, text: str) -> list:
        """使用Hugging Face模型对文本进行嵌入"""
        try:
            response = requests.post(
                self.hf_api_url,
                headers=self.hf_headers,
                json={"inputs": text, "options": {"wait_for_model": True}},
                timeout=10,
            )
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        except requests.Timeout:
            self.logger.info(f"The embedding request of {text} timed out")
            return [0.0] * self.hf_dim
        except requests.HTTPError as http_err:
            self.logger.error(f"The embedding of {text} HTTP error occurred: {http_err}")
            return [0.0] * self.hf_dim
        except Exception as err:
            self.logger.error(f"The embedding of {text} other error occurred: {err}")
            return [0.0] * self.hf_dim
        vector: List[float] = response.json()
        assert (
                len(vector) == self.hf_dim
        ), f"len(vector)={len(vector)} != self.hf_dim={self.hf_dim}"
        return vector


if __name__ == "__main__":
    # config logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # local embedding
    embedding = LocalEmbedding(model_name=HF_EMBEDDING_MULTIMINILM["model_id"],
                               vector_width=HF_EMBEDDING_MULTIMINILM["dim"])
    print(embedding.embed_text("你好"))
    # hugingface embedding
    embedding = HuggingFaceEmbedding(model_name=HF_EMBEDDING_MULTIMINILM["model_id"],
                                     vector_width=HF_EMBEDDING_MULTIMINILM["dim"])
    print(embedding.embed_text("你好"))
