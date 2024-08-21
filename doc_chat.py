# Author: Lintao
import logging
from pathlib import Path
from utils.llm_api import get_model_answer
from knowledge import KnowledgeRetrieval
from utils.embedding import LocalEmbedding


class DocChat:
    def __init__(self, model, user_root_path, knowledge_retrieval):
        self.related_knowledge = None
        self.logger = logging.getLogger("DocChat")
        self.history = []
        self.response = ""
        self.answer_model = model
        self.USER_ROOT_PATH = user_root_path
        self.knowledge_retrieval = knowledge_retrieval

        instruct = f"""
                你是一个智能助手，你的任务是根据用户的输入和相关记忆来生成回答。
                你需要根据用户的输入和检索到的相关知识来回答用户的问题。
                用中文回答。
                """
        instruct = '\n'.join([line.strip() for line in instruct.strip().split('\n')])
        print(instruct)
        self.history.append({"role": "system", "content": instruct})

    def generate_response(self, input_text):
        """
        生成回答
        """
        self.history.append({"role": "user", "content": input_text})

        # 知识检索
        related_knowledge = self.knowledge_retrieval.search_knowledge(input_text, k=5)
        related_knowledge_texts = [item.text for item in related_knowledge]
        knowledge_prompt = "相关知识包括：" + "；".join(related_knowledge_texts)

        # 添加到历史记录
        self.history.append({"role": "system", "content": knowledge_prompt})

        # 调用模型生成答案
        answer = get_model_answer(model_name=self.answer_model, inputs_list=self.history,
                                  user_dir=self.USER_ROOT_PATH)

        self.history.append({"role": "assistant", "content": answer})
        self.logger.debug(f"""
                    <DocChat>
                    <对话列表>:{self.history}
                            """)
        self.response = answer
        return answer

    def get_related_knowledge(self, input_text):
        # 知识检索
        related_knowledge = self.knowledge_retrieval.search_knowledge(input_text, k=5)
        related_knowledge_texts = [item.text for item in related_knowledge]
        logging.debug(f"检索问题为: {input_text}")
        for item in related_knowledge:
            logging.debug(f"相关知识得分: {item.score}")
            logging.debug(f"相关知识: {item.text}")
        knowledge_prompt = "相关知识包括：" + "；".join(related_knowledge_texts)
        return knowledge_prompt

    def generate_response_stream(self, input_text, knowledge):
        """
        流式生成回答
        """
        print(f"knowledge_prompt: {knowledge}")
        self.history.append({"role": "user", "content": input_text})
        self.logger.info(f'generate_response_stream, conversation_history before: {self.history}')

        # 添加到历史记录
        self.history.append({"role": "system", "content": knowledge})

        response = get_model_answer(model_name=self.answer_model, inputs_list=self.history,
                                    user_dir=self.USER_ROOT_PATH, stream=True)
        output = ""
        for chunk in response:
            if 'choices' in chunk:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']
                    output += delta['content']

        self.history.append({"role": "assistant", "content": output})
        self.logger.info(f'generate_response_stream, conversation_history after: {self.history}')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    user_dir = Path(__file__).resolve().parents[0] / 'lintao'
    embedding_model = LocalEmbedding()  # 假设有一个 LocalEmbedding 类
    knowledge_db_path = user_dir / "database/knowledge_db.pkl"
    vector_db_path = user_dir / "database/vector_db.pkl"
    knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)
    doc_chat = DocChat(model='gpt-4o-2024-05-13', user_root_path=user_dir, knowledge_retrieval=knowledge_retrieval)

    # # 测试生成回答
    # response = doc_chat.generate_response("What is the Hop in traceroute")
    # print("Response:", response)

    # 测试流式生成回答
    related_content = doc_chat.get_related_knowledge("Hop in traceroute")
    # for chunk in doc_chat.generate_response_stream("What is the Hop in traceroute", related_content):
    #     print("Chunk:", chunk)
