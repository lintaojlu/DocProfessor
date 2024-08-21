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
    def __init__(self, embedding_model, knowledge_db_path, vector_db_path):
        # Make sure to download the Punkt tokenizer data if not already downloaded.
        nltk.download('punkt')
        self.knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)

    def study_doc(self, doc_content, window_size=500):
        """
        使用滑动窗口，将文档进行文本分割，并添加到知识库中
        :param doc_content: 文档内容
        :param window_size: 窗口大小
        """
        # 使用单个换行符分割段落
        paragraphs = doc_content.split('\n')

        current_chunk = ""
        for paragraph in paragraphs:
            clean_paragraph = paragraph.strip()

            if not clean_paragraph:  # 跳过空白段落
                continue

            sentences = nltk.sent_tokenize(clean_paragraph)

            if len(sentences) < 2:
                # 段落太短，将其合并到当前块
                if len(current_chunk) + len(clean_paragraph) <= window_size:
                    current_chunk += " " + clean_paragraph
                else:
                    if current_chunk.strip():
                        logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
                        self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())
                    current_chunk = clean_paragraph
            else:
                # 段落太长，按句子分割处理
                if len(clean_paragraph) >= window_size:
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= window_size:
                            current_chunk += " " + sentence
                        else:
                            if current_chunk.strip():
                                logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
                                self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())
                            current_chunk = sentence
                else:
                    # 如果段落长度合适，直接添加
                    if current_chunk.strip():
                        logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
                        self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())
                    current_chunk = clean_paragraph

        # 最后处理剩余的块
        if current_chunk.strip():
            logging.debug(f"Adding knowledge item: {current_chunk.strip()}")
        self.knowledge_retrieval.add_knowledge_item(current_chunk.strip())

    def clear_local_knowledge(self):
        self.knowledge_retrieval.clear_knowledge_db()
        self.knowledge_retrieval.clear_vector_db()


if __name__ == '__main__':
    logging.info('Test for DodStudy')
    embedding_model = LocalEmbedding()
    knowledge_db_path = "user_data/lintao/database/knowledge_db.pkl"
    vector_db_path = "user_data/lintao/database/vector_db.pkl"
    logging.info('Read the document')
    doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
    doc_content = get_doc_content(doc_path)
    docc_study = DocStudy(embedding_model, knowledge_db_path, vector_db_path)
    docc_study.study_doc(doc_content[1000])

    files = os.listdir('user_data/lintao/data')
    for file in files:
        if re.match(r'.*\.pdf', file):
            doc_path = 'lintao/data/' + file

    logging.info('Done')
