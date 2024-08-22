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


if __name__ == '__main__':
    app.run(debug=True)
