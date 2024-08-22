# Author: Lintao
import json
import logging
import nltk
import os
import re
from knowledge import KnowledgeRetrieval
from utils.embedding import LocalEmbedding
from utils.utils import get_doc_content


class DocStudy:
    def __init__(self, tokenizer_dir, knowledge_db_path, vector_db_path):
        # Make sure to download the Punkt tokenizer data if not already downloaded.
        nltk.download('punkt', download_dir=tokenizer_dir)
        embedding_model = LocalEmbedding()
        self.knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)

    import nltk
    import logging

    def study_doc(self, doc_content, window_size=2000):
        """
        将文档按照句子进行文本分割，按照window_size组合成文本块，添加到知识库中
        :param doc_content: 文档内容
        :param window_size: 窗口大小
        """
        # 使用nltk将文档内容分割成句子
        sentences = nltk.sent_tokenize(doc_content)
        logging.debug(f'Sentences: {sentences}')

        current_chunk = ""
        for sentence in sentences:
            # 处理句子，去除首尾空格，将句子中的换行符替换为空格
            clean_sentence = sentence.strip().replace('\n', ' ')
            logging.debug(f'Sentence: {clean_sentence}')

            if len(current_chunk) + len(clean_sentence) <= window_size:
                current_chunk += " " + clean_sentence
            else:
                if current_chunk.strip():
                    logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
                    self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())
                current_chunk = clean_sentence

        # 最后处理剩余的块
        if current_chunk.strip():
            logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
            self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())

    def clear_local_knowledge(self):
        self.knowledge_retrieval.clear_knowledge_db()
        self.knowledge_retrieval.clear_vector_db()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Test for DodStudy')

    tokenizer_dir = "user_data/lintao/models/nltk_data"
    knowledge_db_path = "user_data/lintao/database/knowledge_db.pkl"
    vector_db_path = "user_data/lintao/database/vector_db.pkl"

    logging.info('Read the document')
    doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
    doc_content = get_doc_content(doc_path)
    logging.debug(f"The length of the document content is {len(doc_content)}")

    docc_study = DocStudy(tokenizer_dir, knowledge_db_path, vector_db_path)
    docc_study.study_doc(doc_content)
    logging.info('Done')
