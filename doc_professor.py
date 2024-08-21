# Author: Lintao
import json
import logging
import os
from utils.llm_api import get_model_answer
from utils.utils import get_doc_content


class DocProfessor:
    def __init__(self, user_dir='lintao/', model='gpt-4o'):
        self.model = model
        self.user_dir = user_dir
        self.user_doc_dir = self.user_dir + 'data/'
        self.categories_map_path = self.user_dir + 'config/category_map.json'
        self.categories_map = None
        logging.info(f'DOC_CLASSIFIER use model:{self.model}')

    def load_categories_map(self):
        with open(self.categories_map_path, 'r') as f:
            self.categories_map = json.load(f)

    def set_categories_map(self, categories_map):
        self.categories_map = categories_map

    def get_categories_map(self):
        return self.categories_map

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

    def add_candidate_category(self, category, description=''):
        self.categories_map['candidate_category'].append({category: description})
        self.save_categories_map()

    def add_candidate_keyword(self, keyword, description=''):
        self.categories_map['candidate_keyword'].append({keyword: description})
        self.save_categories_map()

    def update_candidate_category(self, category, description):
        self.categories_map['candidate_category'][category] = description
        self.save_categories_map()

    def save_categories_map(self):
        with open(self.categories_map_path, 'w') as f:
            json.dump(self.categories_map, f)
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
            dict_response = {'title': '解析回答时出错', 'candidate_category': [], 'candidate_keyword': []}
        return dict_response

    def classify_doc(self, doc_content):
        sys_instruction = (
                'Classify documents and give documents keywords based on given categories and keywords, provide correlation scores, reasons and original text. '
                'If the document does not fit any category, classify it as "其他".'
                'Create new keywords if the document does not fit any existing keywords. '
                'Score ranges from 60 to 100.'
                'You prioritizes clarity and accuracy, focusing on the abstract and the title of the document. '
                'The output should be a markdown code snippet formatted in JSON, such as '
                '```json {"title": "Cross-layer diagnosis of optical backbone failures", '
                '"candidate_category": [{"category": "研究论文", "score": 95, "reason": "这是一篇关于网络诊断的文章，张颖等人详细介绍了在光学主干网络中进行故障诊断的研究和系统"}], '
                '"candidate_keyword": [{"keyword": "Optical Network", "score": 95, "reason": "文章详细讨论了光学主干网络的结构、故障特性以及诊断方法", "original_text": "Optical backbone networks, the physical infrastructure inter-connecting data centers, are the cornerstones of Wide-Area Network (WAN) connectivity and resilience."}]} ```. '
                '用中文回答。'
                'The categories are as follows: ' +
                f'{self.categories_map}')
        prompt = [{"role": "system", "content": sys_instruction}, {"role": "user", "content": doc_content}]
        logging.debug(f'prompt: {prompt}')
        answer = get_model_answer(model_name=self.model, inputs_list=prompt, user_dir=self.user_dir)
        logging.debug(f'answer: {answer}')
        answer_dict = self.parse_response_json(answer)
        return answer_dict

    def get_category_and_keywords(self, answer_dict):
        candidate_category = answer_dict.get('candidate_category', [])
        candidate_keyword = answer_dict.get('candidate_keyword', [])
        category = []
        for item in candidate_category:
            category.append(item['category'])
        kewords = []
        for item in candidate_keyword:
            kewords.append(item['keyword'])
        if not category:
            category = ['others']
        return category, kewords

    def summarize_doc(self, doc_content):
        """此GPT旨在高效总结文档内容，重点是以Markdown格式提供简明摘要。它将提取并包含标题、基本信息（如作者、出版日期、来源和用途）、摘要以及导读，导读应当分点阐述各个部分的主要内容、观点等。目标是在保留原始上下文的同时，去除不必要的细节，确保关键信息得到清晰呈现。交流风格将是正式的，优先考虑清晰度和专业性。最后，输出以中文为主。"""
        sys_instruction = (
            '你是文档总结助手，任务是高效总结文档内容，重点是以Markdown格式提供简明摘要。'
            '你将提取并包含标题、基本信息（如作者、出版日期、来源和用途）、摘要以及导读，导读应当分点阐述各个部分的主要内容、观点等。目标是在保留原始上下文的同时，去除不必要的细节，确保关键信息得到清晰呈现。交流风格将是正式的，优先考虑清晰度和专业性。'
            '最后，回答以中文为主。')
        prompt = [{"role": "system", "content": sys_instruction}, {"role": "user", "content": doc_content}]
        logging.debug(f'prompt: {prompt}')
        answer = get_model_answer(model_name=self.model, inputs_list=prompt, user_dir=self.user_dir)
        logging.debug(f'answer: {answer}')
        return answer

    def get_new_doc_path_based_on_category(self, doc_path, category):
        doc_name = os.path.basename(doc_path)
        new_doc_dir = os.path.join(self.user_doc_dir, category)
        if not os.path.exists(new_doc_dir):
            os.makedirs(new_doc_dir)
        new_doc_path = os.path.join(new_doc_dir, doc_name)
        return new_doc_path

    def get_summary_path_based_on_category(self, doc_path, category):
        doc_name = os.path.basename(doc_path)
        summary_name = doc_name + '.md'
        summary_dir = os.path.join(self.user_doc_dir, category)
        if not os.path.exists(summary_dir):
            os.makedirs(summary_dir)
        summary_path = os.path.join(summary_dir, summary_name)
        return summary_path

    def move_doc(self, doc_path, new_doc_path):
        os.rename(doc_path, new_doc_path)
        logging.info(f"Document has been moved to {new_doc_path}")

    def dump_content_to_file(self, answer, output_path):
        with open(output_path, 'w') as f:
            f.write(answer)
            logging.info(f"Answer has been saved to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logging.info('Test for Doc Professor')
    docc = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
    logging.info('Load the categories map')
    docc.load_categories_map()
    logging.info('Read the document')
    doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
    doc_content = get_doc_content(doc_path)

    logging.info('Classify the document')
    classify_result = docc.classify_doc(doc_content[:1000])
    logging.info('Get the category and keywords')
    category, keywords = docc.get_category_and_keywords(classify_result)
    logging.info(f'Category: {category}, Keywords: {keywords}')

    for keyword in keywords:
        if keyword not in docc.get_candidate_keyword():
            logging.info('Add keywords if not exist')
            docc.add_candidate_keyword(keyword)

    logging.info('Get the new document path based on category')
    new_doc_path = docc.get_new_doc_path_based_on_category(doc_path, category[0])
    logging.info('Move the document')
    docc.move_doc(doc_path, new_doc_path)
    logging.info('Get the summary path based on category')
    summary_path = docc.get_summary_path_based_on_category(doc_path, category[0])
    logging.info('Summarize the document')
    summary = docc.summarize_doc(doc_content)
    logging.info('Dump the content to file')
    docc.dump_content_to_file(summary, summary_path)
    logging.info('Done')
