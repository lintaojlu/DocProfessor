from flask import Flask, request, jsonify, Response, render_template
import logging
import json
import os

from doc_professor import DocProfessor
from werkzeug.utils import secure_filename

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize the DocProfessor instance
professor = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
professor.load_categories_map()


@app.route('/')
def index():
    return render_template('index.html')


"""
文档管理功能
"""


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
    # 参数: 文件名
    file_name = request.args.get('file_name')

    if not file_name:
        return jsonify({"error": "请提供文件名或ID"}), 400

    details = professor.get_resolve_result(file_name)

    return jsonify({"details": details})


@app.route('/delete_file', methods=['POST'])
def delete_file():
    # 功能: 删除文档
    # 参数: 文件名
    file_name = request.json.get('file_name')

    if not file_name:
        return jsonify({"error": "请提供文件名或ID"}), 400

    professor.delete_file(file_name)

    return jsonify({"message": "文件删除成功"})


@app.route('/get_doc_table', methods=['GET'])
def get_all_docs():
    # 功能: 获取所有的文档信息
    # 参数: 无
    # format [{'doc_name': '', 'category': '', 'keywords': '', 'doc_path': '', 'summary_path': '', 'info_path': ''}]
    doc_table = professor.get_all_docs()
    return jsonify(doc_table)


@app.route('/get_documents_by_category', methods=['GET'])
def get_documents_by_category():
    # 功能: 查看某分类下的全部文档
    # 参数: 分类名称
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
