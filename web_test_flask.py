from flask import Flask, request, jsonify, Response, render_template
import logging
import json
import os

from doc_professor import DocProfessor
from werkzeug.utils import secure_filename

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# 初始化 DocProfessor 实例
professor = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
professor.load_categories_map()


@app.route('/')
def index():
    """
    渲染首页。
    """
    return render_template('index.html')


"""
文档管理功能
"""


@app.route('/upload_files', methods=['POST'])
def upload_files():
    """
    上传多个文件到服务器。

    请求:
        - files[]: 要上传的文件列表。

    响应:
        - 包含上传文件路径的 JSON 对象或错误信息。
    """
    if 'files[]' not in request.files:
        return jsonify({"error": "请求中没有文件部分"}), 400

    files = request.files.getlist('files[]')

    if not files:
        return jsonify({"error": "没有选择文件"}), 400

    uploaded_files = []

    for file in files:
        if file.filename == '':
            continue  # 跳过未选择文件的部分

        filename = file.filename
        file_path = os.path.join(professor.user_temp_dir, filename)
        file.save(file_path)
        # 值表示文档的状态，0 表示未解析
        professor.documents_to_be_resolved[file_path] = 0

        uploaded_files.append(file_path)

    if not uploaded_files:
        return jsonify({"error": "没有有效的文件上传"}), 400

    return jsonify({"uploaded_files": uploaded_files})


@app.route('/resolve_files', methods=['POST'])
def resolve_files():
    """
    解析已上传的文档。

    请求:
        - 无参数。

    响应:
        - 包含每个文档状态的 JSON 对象。
    """
    file_status = professor.resolve_docs()
    return jsonify(file_status)


@app.route('/get_categories', methods=['GET'])
def get_categories():
    """
    获取候选分类列表。

    请求:
        - 无参数。

    响应:
        - 包含分类列表的 JSON 对象。
    """
    categories = professor.get_candidate_category()
    return jsonify(categories)


@app.route('/get_keywords', methods=['GET'])
def get_keywords():
    """
    获取候选关键词列表。

    请求:
        - 无参数。

    响应:
        - 包含关键词列表的 JSON 对象。
    """
    keywords = professor.get_candidate_keyword()
    return jsonify(keywords)


@app.route('/add_category', methods=['POST'])
def add_category():
    """
    添加新分类。

    请求:
        - 包含 'category' 和可选 'description' 的 JSON 对象。

    响应:
        - 包含成功消息的 JSON 对象。
    """
    data = request.json
    category = data.get('category')
    description = data.get('description', '')
    professor.add_candidate_category(category, description)
    return jsonify({"message": "分类添加成功"})


@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    """
    添加新关键词。

    请求:
        - 包含 'keyword' 和可选 'description' 的 JSON 对象。

    响应:
        - 包含成功消息的 JSON 对象。
    """
    data = request.json
    keyword = data.get('keyword')
    description = data.get('description', '')
    professor.add_candidate_keyword(keyword, description)
    return jsonify({"message": "关键词添加成功"})


@app.route('/update_category', methods=['POST'])
def update_category():
    """
    更新现有分类的描述。

    请求:
        - 包含 'category' 和 'description' 的 JSON 对象。

    响应:
        - 包含成功消息的 JSON 对象。
    """
    data = request.json
    category = data.get('category')
    description = data.get('description', '')
    professor.update_candidate_category_desc(category, description)
    return jsonify({"message": "分类更新成功"})


@app.route('/view_file_details', methods=['GET'])
def view_file_details():
    """
    查看解析文档的细节。

    请求:
        - 查询参数 'file_name': 要查看细节的文件名。

    响应:
        - 包含文档细节的 JSON 对象或错误信息。
    """
    file_name = request.args.get('file_name')

    if not file_name:
        return jsonify({"error": "请提供文件名或ID"}), 400

    details = professor.get_resolve_result(file_name)

    return jsonify({"details": details})


@app.route('/delete_file', methods=['POST'])
def delete_file():
    """
    删除文档。

    请求:
        - 包含 'file_name' 的 JSON 对象: 要删除的文件名。

    响应:
        - 包含成功消息或错误信息的 JSON 对象。
    """
    file_name = request.json.get('file_name')

    if not file_name:
        return jsonify({"error": "请提供文件名或ID"}), 400

    professor.delete_file(file_name)

    return jsonify({"message": "文件删除成功"})


@app.route('/get_doc_table', methods=['GET'])
def get_all_docs():
    """
    获取所有文档的信息。

    请求:
        - 无参数。

    响应:
        - 包含文档及其详细信息的 JSON 对象。
    """
    doc_table = professor.get_all_docs()
    return jsonify(doc_table)


@app.route('/get_documents_by_category', methods=['GET'])
def get_documents_by_category():
    """
    根据分类获取文档。

    请求:
        - 查询参数 'category': 分类名称。

    响应:
        - 包含指定分类下文档列表的 JSON 对象或错误信息。
    """
    category = request.args.get('category')
    if not category:
        return jsonify({"error": "请提供分类名称"}), 400

    doc_table = professor.get_docs_by_category(category)
    return jsonify(doc_table)


"""
知识库问答功能
"""


@app.route('/answer', methods=['POST'])
def generate_response_stream():
    """
    为给定的输入文本生成响应流。

    请求:
        - 包含 'input_text' 的 JSON 对象: 要生成响应的文本。

    响应:
        - 包含对话标题、相关知识和回答块的服务器发送事件（SSE）流。
    """
    input_text = request.json.get('input_text')

    def generate():
        title = professor.assistant.generate_conversation_title(input_text)
        # 返回标题
        yield f"data: {json.dumps({'title': title})}\n\n"

        # 检索相关知识
        knowledge = professor.assistant.get_related_knowledge(input_text)
        yield f"data: {json.dumps({'related_knowledge': knowledge})}\n\n"

        # 流式生成回答
        response_stream = professor.assistant.generate_response_stream(input_text, knowledge)
        for chunk in response_stream:
            yield f"data: {json.dumps({'answer_chunk': chunk})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)