# Author: Lintao
import json
import logging
from utils.llm_api import get_model_answer


class DocResolver:
    def __init__(self, user_dir, model='gpt-4o'):
        self.model = model
        self.user_dir = user_dir
        self.categories_map = None
        logging.info(f'DocResolver use model:{self.model}')

    def set_categories_map(self, categories_map):
        self.categories_map = categories_map

    def resolve_doc(self, doc_content):
        logging.info(f"Start resolve doc")
        # 获得文档分类和关键词
        categories_and_keywords = self.classify_doc(doc_content)
        if not categories_and_keywords:
            raise Exception("No category found")
        try:
            categories, keywords = self.get_category_and_keywords(categories_and_keywords)
            if not categories or not keywords:
                raise Exception("No category or keywords found")
        except Exception as e:
            logging.error(f"解析回答时出错：{e}")
            raise Exception("No category or keywords found")

        # 获得文档摘要
        summary = self.summarize_doc(doc_content)
        if not summary:
            raise Exception("No summary found")
        logging.info(f"Finish resolve doc")

        return categories, keywords, summary

    def classify_doc(self, doc_content):
        # parse the response to dict
        def parse_response_json(content):
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

        logging.debug(f'doc_content: {doc_content[:100]}')
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
        answer_dict = parse_response_json(answer)
        # if some error occurs, return None
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Test for DocResolver')
    resolver = DocResolver(user_dir='user_data/lintao')
    doc_content = """We present a longitudinal study of intercontinental long-haul links (LHLs) – links with latencies signicantly
        higher than that of all other links in a traceroute path. Our study is motivated by the recognition of these
        LHLs as a network-layer manifestation of critical transoceanic undersea cables. We present a methodology
        and associated processing system for identifying long-haul links in traceroute measurements. We apply
        this system to a large corpus of traceroute data and report on multiple aspects of long haul connectivity
        including country-level prevalence, routers as international gateways, preferred long-haul destinations, and
        the evolution of these characteristics over a 7 year period. We identify 85,620 layer-3 links (out of 2.7M links
        in a large traceroute dataset) that satisfy our denition for intercontinental long haul with many of them
        terminating in a relatively small number of nodes. An analysis of connected components shows a clearly
        dominant component with a relative size that remains stable despite a signicant growth of the long-haul
        infrastructure."""
    categories, keywords, summary = resolver.resolve_doc(doc_content)
    logging.info(f'categories: {categories}, keywords: {keywords}, summary: {summary}')
