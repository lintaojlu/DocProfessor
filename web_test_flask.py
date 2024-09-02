from flask import Flask, request, jsonify, Response, render_template
import logging
import json
import os

from doc_chat import DocAssistant
from doc_study import DocStudy
from utils.embedding import LocalEmbedding
from utils.llm_api import get_model_answer
from utils.utils import get_doc_content
from doc_professor import DocProfessor
from werkzeug.utils import secure_filename

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize the DocProfessor instance
professor = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
professor.load_categories_map()

#TODO 根据前端设计接口

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files[]')

    if not files:
        return jsonify({"error": "No selected files"}), 400

    uploaded_files = []

    for file in files:
        if file.filename == '':
            continue  # 跳过未选择文件的部分

        filename = file.filename
        file_path = os.path.join(professor.user_temp_dir, filename)
        file.save(file_path)
        # the value is the status of the document, 0 means not resolved
        professor.documents_to_be_resolved[file_path] = 0

        uploaded_files.append(file_path)

    if not uploaded_files:
        return jsonify({"error": "No valid files uploaded"}), 400

    return jsonify({"uploaded_files": uploaded_files})


@app.route('/resolve_files', methods=['POST'])
def resolve_files():
    file_status = professor.resolve_docs()
    return jsonify(file_status)


@app.route('/answer', methods=['POST'])
def generate_response_stream():
    input_text = request.json.get('input_text')

    def generate():
        title = professor.assistant.generate_conversation_title(input_text)
        # 先返回标题
        yield f"data: {json.dumps({'title': title})}\n\n"

        # 然后流式生成回答
        response_stream = professor.assistant.answer_question_with_knowledge(input_text)
        for chunk in response_stream:
            yield f"data: {json.dumps({'answer_chunk': chunk})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/get_categories', methods=['GET'])
def get_categories():
    categories = professor.get_candidate_category()
    return jsonify(categories)


@app.route('/get_keywords', methods=['GET'])
def get_keywords():
    keywords = professor.get_candidate_keyword()
    return jsonify(keywords)


@app.route('/add_category', methods=['POST'])
def add_category():
    data = request.json
    category = data.get('category')
    description = data.get('description', '')
    professor.add_candidate_category(category, description)
    return jsonify({"message": "Category added successfully"})


@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    data = request.json
    keyword = data.get('keyword')
    description = data.get('description', '')
    professor.add_candidate_keyword(keyword, description)
    return jsonify({"message": "Keyword added successfully"})


@app.route('/update_category', methods=['POST'])
def update_category():
    data = request.json
    category = data.get('category')
    description = data.get('description', '')
    professor.update_candidate_category_desc(category, description)
    return jsonify({"message": "Category updated successfully"})


@app.route('/view_file_details', methods=['GET'])
def view_file_details():
    # 功能: 查看文档解析细节
    # 参数: 文件名或ID
    pass


@app.route('/delete_file', methods=['POST'])
def delete_file():
    # 功能: 删除文档
    # 参数: 文件名或ID
    pass


@app.route('/edit_tag', methods=['POST'])
def edit_tag():
    # 功能: 编辑标签内容
    # 参数: 文件名或ID, 标签内容
    pass


@app.route('/get_page_content', methods=['GET'])
def get_page_content():
    # 功能: 访问相应页内容
    # 参数: 页码, 每页项目数量
    pass

@app.route('/get_documents_by_category', methods=['GET'])
def get_documents_by_category():
    # 功能: 查看某分类下的全部文档
    # 参数: 分类ID或名称
    pass


@app.route('/get_subcategories', methods=['GET'])
def get_subcategories():
    # 功能: 查看一级分类下的二级分类文件夹
    # 参数: 一级分类ID或名称
    pass


@app.route('/document_management', methods=['GET'])
def document_management():
    # 功能: 进入文档管理界面
    pass


@app.route('/knowledge_base_qa', methods=['GET'])
def knowledge_base_qa():
    # 功能: 进入知识库问答功能界面
    pass


@app.route('/knowledge_graph', methods=['GET'])
def knowledge_graph():
    # 功能: 进入知识图谱功能界面
    pass


@app.route('/view_conversation/<conversation_id>', methods=['GET'])
def view_conversation(conversation_id):
    # 功能: 查看历史问答的某个对话
    # 参数: conversation_id (会话ID)
    pass


@app.route('/create_conversation', methods=['POST'])
def create_conversation():
    # 功能: 新建会话
    pass


@app.route('/send_message', methods=['POST'])
def send_message():
    # 功能: 发送对话
    # 参数: 输入的对话内容
    pass


@app.route('/view_related_document/<message_id>', methods=['GET'])
def view_related_document(message_id):
    # 功能: 查看与回答相关联的文档
    # 参数: message_id (消息ID)
    pass


@app.route('/highlight_related_articles', methods=['POST'])
def highlight_related_articles():
    # 功能: 知识图谱中高亮显示与某圆圈直接关联的文章
    # 参数: 节点ID或文章ID
    pass


@app.route('/login', methods=['POST'])
def login():
    # 功能: 用户登录
    pass


if __name__ == '__main__':
    app.run(debug=True)
