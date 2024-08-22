# Author: Lintao
import json
import logging
import os
from pathlib import Path
from utils.llm_api import get_model_answer
from knowledge import KnowledgeRetrieval
from utils.embedding import LocalEmbedding

INSTRUCT = f"""
        你是一个智能助手，你的任务是根据用户的输入和相关记忆来生成回答。
        你需要根据用户的输入和检索到的相关知识来回答用户的问题。
        用中文回答。
        """
INITIAL_CONVERSATION = [{"role": "system", "content": INSTRUCT}]


class DocAssistant:
    def __init__(self, model, user_dir, knowledge_retrieval):
        self.related_knowledge = None
        self.logger = logging.getLogger("DocAssistant")
        self.answer_model = model
        self.user_dir = user_dir
        self.conversation_dir = os.path.join(user_dir, 'conversation')
        os.makedirs(self.conversation_dir, exist_ok=True)
        self.knowledge_retrieval = knowledge_retrieval

        self.conversation_title = ''
        self.conversation = INITIAL_CONVERSATION
        self.response = ""

    def generate_response(self, input_text):
        """
        生成回答
        """
        self.conversation.append({"role": "user", "content": input_text})

        # 知识检索
        related_knowledge = self.knowledge_retrieval.search_knowledge(input_text, k=5)
        related_knowledge_texts = [item.text for item in related_knowledge]
        knowledge_prompt = "相关知识包括：" + "；".join(related_knowledge_texts)

        # 添加到历史记录
        self.conversation.append({"role": "system", "content": knowledge_prompt})

        # 调用模型生成答案
        answer = get_model_answer(model_name=self.answer_model, inputs_list=self.conversation,
                                  user_dir=self.user_dir)

        self.conversation.append({"role": "assistant", "content": answer})
        self.logger.debug(f"""
                    <DocChat>
                    <对话列表>:{self.conversation}
                            """)
        self.response = answer
        return answer

    def generate_response_stream(self, input_text, knowledge):
        """
        流式生成回答
        """
        print(f"knowledge_prompt: {knowledge}")
        self.conversation.append({"role": "user", "content": input_text})
        self.logger.info(f'generate_response_stream, conversation_history before: {self.conversation}')

        # 添加到历史记录
        self.conversation.append({"role": "system", "content": knowledge})

        response = get_model_answer(model_name=self.answer_model, inputs_list=self.conversation,
                                    user_dir=self.user_dir, stream=True)
        output = ""
        for chunk in response:
            if 'choices' in chunk:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']
                    output += delta['content']

        self.conversation.append({"role": "assistant", "content": output})
        self.logger.info(f'generate_response_stream, conversation_history after: {self.conversation}')

    def answer_question_with_knowledge(self, input_text):
        knowledge = self.get_related_knowledge(input_text)
        """
        流式生成回答
        """
        self.conversation.append({"role": "user", "content": input_text})
        self.logger.info(f'generate_response_stream, conversation_history before: {self.conversation}')

        # 添加到历史记录
        self.conversation.append({"role": "system", "content": knowledge})

        response = get_model_answer(model_name=self.answer_model, inputs_list=self.conversation,
                                    user_dir=self.user_dir, stream=True)
        output = ""
        for chunk in response:
            if 'choices' in chunk:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']
                    output += delta['content']

    def get_related_knowledge(self, input_text, k=5):
        # 知识检索
        related_knowledge = self.knowledge_retrieval.search_knowledge(input_text, k=k)
        related_knowledge_texts = [item.text for item in related_knowledge]
        logging.debug(f"检索问题为: {input_text}")
        for item in related_knowledge:
            logging.debug(f"相关知识得分: {item.score}")
            logging.debug(f"相关知识: {item.text}")
        knowledge_prompt = "相关知识包括：" + "；".join(related_knowledge_texts)
        return knowledge_prompt

    def generate_conversation_title(self, input_text):
        logging.info(f"生成标题: {input_text}")
        instruction = "根据以下问题，生成一个简洁、准确的标题"
        prompts = [{"role": "system", "content": instruction}, {"role": "user", "content": input_text}]
        title = get_model_answer(model_name=self.answer_model, inputs_list=prompts, user_dir=self.user_dir)
        self.conversation_title = title
        return title

    def save_history(self):
        self.logger.info(f"保存对话历史: {self.conversation}")
        conversation_file = self.conversation_dir / f"{self.conversation_title}.json"
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation, f, ensure_ascii=False, indent=4)

    def clear_history(self):
        self.conversation = INITIAL_CONVERSATION

    def load_history(self, title):
        conversation_file = self.conversation_dir / f"{title}.json"
        with open(conversation_file, 'r', encoding='utf-8') as f:
            self.conversation = json.load(f)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    user_dir = Path(__file__).resolve().parents[0] / 'user_data/lintao'
    embedding_model = LocalEmbedding()  # 假设有一个 LocalEmbedding 类
    knowledge_db_path = user_dir / "database/knowledge_db.pkl"
    vector_db_path = user_dir / "database/vector_db.pkl"
    knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)
    doc_chat = DocAssistant(model='gpt-4o-2024-05-13', user_dir=user_dir, knowledge_retrieval=knowledge_retrieval)

    # # 测试生成回答
    # response = doc_chat.generate_response("What is the Hop in traceroute")
    # print("Response:", response)

    # # 测试流式生成回答
    # related_content = doc_chat.get_related_knowledge("Hop in traceroute")
    # for chunk in doc_chat.generate_response_stream("What is the Hop in traceroute", related_content):
    #     print("Chunk:", chunk)

    # 测试生成回答
    for chunk in doc_chat.answer_question_with_knowledge("What is the Hop in traceroute"):
        print("Chunk:", chunk)
