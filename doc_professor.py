# Author: Lintao
import json
import logging
import os

from doc_chat import DocAssistant
from doc_study import DocStudy
from utils.llm_api import get_model_answer
from utils.utils import get_doc_content, get_files_in_directory, move_doc, dump_content_to_file
from doc_resolver import DocResolver


class DocProfessor:
    def __init__(self, user_dir='lintao/', model='gpt-4o'):
        self.model = model
        self.user_dir = user_dir
        self.user_doc_dir = self.user_dir + 'data/'
        self.user_temp_dir = self.user_dir + 'temp/'
        self.categories_map_path = self.user_dir + 'config/category_map.json'
        self.categories_map = None
        self.documents_local = []
        # e.g. {'doc_path': 'status'}
        self.documents_to_be_resolved = {}
        logging.info(f'DOC_CLASSIFIER use model:{self.model}')

        # initialize
        os.makedirs(self.user_doc_dir, exist_ok=True)
        os.makedirs(self.user_temp_dir, exist_ok=True)
        self.documents_local = self.get_all_document_paths()
        # the main modules
        self.resolver = DocResolver(user_dir=self.user_dir, model=self.model)
        self.learner = DocStudy(tokenizer_dir=self.user_dir + 'models/nltk_data',
                                knowledge_db_path=self.user_dir + 'database/knowledge_db.pkl',
                                vector_db_path=self.user_dir + 'database/vector_db.pkl')
        self.knowledge_retrieval = self.learner.knowledge_retrieval
        self.assistant = DocAssistant(model=self.model, user_dir=self.user_dir,
                                      knowledge_retrieval=self.knowledge_retrieval)

    def get_all_document_paths(self):
        self.documents_local = get_files_in_directory(self.user_doc_dir)
        return self.documents_local

    def load_categories_map(self):
        with open(self.categories_map_path, 'r') as f:
            self.categories_map = json.load(f)

    def get_categories_map(self):
        return self.categories_map

    def add_candidate_category(self, category, description=''):
        self.categories_map['candidate_category'].append({category: description})
        self.save_categories_map()

    def add_candidate_keyword(self, keyword, description=''):
        self.categories_map['candidate_keyword'].append({keyword: description})
        self.save_categories_map()

    def update_candidate_category_desc(self, category, description):
        self.categories_map['candidate_category'][category] = description
        self.save_categories_map()

    def update_candidate_keyword_desc(self, keyword, description):
        self.categories_map['candidate_keyword'][keyword] = description
        self.save_categories_map()

    def update_keywords(self, keywords: dict):
        for keyword, description in keywords.items():
            self.categories_map['candidate_keyword'][keyword] = description
        self.save_categories_map()

    def update_categories(self, categories: dict):
        for category, description in categories.items():
            self.categories_map['candidate_category'][category] = description
        self.save_categories_map()

    def get_candidate_category(self):
        try:
            candidate_category = list(self.categories_map['candidate_category'].keys())
        except:
            candidate_category = []
        return candidate_category

    def get_candidate_keyword(self):
        try:
            candidate_keyword = list(self.categories_map['candidate_keyword'].keys())
        except:
            candidate_keyword = []
        return candidate_keyword

    def save_categories_map(self):
        with open(self.categories_map_path, 'w') as f:
            # why the Chines characters are not displayed correctly? The reason is that the default encoding is ASCII. How to solve it? Add ensure_ascii=False
            json.dump(self.categories_map, f, ensure_ascii=False, indent=4)
            logging.debug(f"Save categories map to {self.categories_map_path}")

    def make_dirs_based_on_categories(self):
        candidate_category = self.categories_map['candidate_category']
        for category in candidate_category:
            category_dir = os.path.join(self.user_doc_dir, category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
                logging.info(f"Create directory: {category_dir}")

    def parse_response_json(self, content):
        # remove ```json from the beginning and ``` from end
        content = content.lstrip("```json").rstrip("```")
        try:
            dict_response = json.loads(content)
            if 'title' not in dict_response.keys() or 'candidate_category' not in dict_response.keys() or 'candidate_keyword' not in dict_response.keys():
                raise Exception("Wrong Json Format")
        except Exception as e:
            logging.debug(f"解析回答时出错：{e}, {content}")
            dict_response = None
        return dict_response

    def resolve_docs(self):
        logging.info("Start to resolve all documents")
        for doc_path, status in self.documents_to_be_resolved.items():
            # if status is 1, means the document has been resolved
            if status == 1:
                continue
            try:
                # 读取文档
                doc_content = get_doc_content(doc_path)
            except Exception as e:
                logging.error(f"Error when read doc: {doc_path}, {e}")

            try:
                # 解析文档
                # example format:
                # {"title": "",
                # "candidate_category": [{"category": "研究论文", "score": 95, "reason": ""}],
                # "candidate_keyword": [{"keyword": "k1", "score": 95, "reason": "", "original_text": ""}]}
                categories_and_keywords = self.resolver.classify_doc(doc_content)
                if not categories_and_keywords:
                    raise Exception("Resolve doc failed: No category or keyword found")

                # 进行文档分类和关键词提取
                categories, keywords = self.resolver.get_category_and_keywords(categories_and_keywords)

                # 生成文档摘要
                summary = self.resolver.summarize_doc(doc_content)
            except Exception as e:
                logging.error(f"Error when resolve doc: {doc_path}, {e}")
                continue

            # 更新分类和关键词
            # TODO categories和keywords都是list，需要获得的是dict
            categories_dict = {category: '' for category in categories}
            keywords_dict = {keyword: '' for keyword in keywords}
            self.update_categories(categories_dict)
            self.update_keywords(keywords_dict)

            # 移动文档到新的目录
            new_doc_path = self.get_new_doc_path_based_on_category(doc_path, categories[0])
            move_doc(doc_path, new_doc_path)

            # 保存文档解析信息
            new_doc_info_path = self.get_new_doc_info_path_based_on_category(doc_path, categories[0])
            with open(new_doc_info_path, 'w') as f:
                json.dump(categories_and_keywords, f, ensure_ascii=False, indent=4)

            # 获取新的摘要路径
            summary_path = self.get_summary_path_based_on_category(doc_path, categories[0])
            dump_content_to_file(summary, summary_path)

            # 学习文档
            self.learner.study_doc(doc_content)

            # 文档解析完毕
            self.documents_to_be_resolved[doc_path] = 1
        logging.info("Finish resolve all documents")
        return self.documents_to_be_resolved



    def get_new_doc_path_based_on_category(self, doc_path, category):
        try:
            doc_name = os.path.basename(doc_path)
            new_doc_dir = os.path.join(self.user_doc_dir, category)
            if not os.path.exists(new_doc_dir):
                os.makedirs(new_doc_dir)
            new_doc_path = os.path.join(new_doc_dir, doc_name)
            return new_doc_path
        except Exception as e:
            logging.error(f"Error when get new doc path: {doc_path}, {e}")

    def get_new_doc_info_path_based_on_category(self, doc_path, category):
        try:
            doc_name = os.path.basename(doc_path)
            doc_info_name = doc_name + '.json'
            doc_info_dir = os.path.join(self.user_doc_dir, category)
            if not os.path.exists(doc_info_dir):
                os.makedirs(doc_info_dir)
            doc_info_path = os.path.join(doc_info_dir, doc_info_name)
            return doc_info_path
        except Exception as e:
            logging.error(f"Error when get new doc info path: {doc_path}, {e}")

    def get_summary_path_based_on_category(self, doc_path, category):
        try:
            doc_name = os.path.basename(doc_path)
            summary_name = doc_name + '.md'
            summary_dir = os.path.join(self.user_doc_dir, category)
            if not os.path.exists(summary_dir):
                os.makedirs(summary_dir)
            summary_path = os.path.join(summary_dir, summary_name)
            return summary_path
        except Exception as e:
            logging.error(f"Error when get summary path: {doc_path}, {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Test for Doc Professor')
    docc = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
    logging.info('Load the categories map')
    docc.load_categories_map()
    logging.info('Read the document')
    doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
    docc.documents_to_be_resolved[doc_path] = 0
    logging.info('Resolve the document')
    documents_status = docc.resolve_docs()
    logging.info(f"Documents status: {documents_status}")
