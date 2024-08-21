# DocProfessor

## Description
**DocProfessor** is an intelligent document processing system designed to classify, summarize, and interact with documents using advanced language models. The system integrates knowledge retrieval, classification, and summarization functionalities to provide comprehensive insights into document content.

## Installation
To install and set up DocProfessor, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd doc_professor
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download necessary models and data:**
   - Ensure you have the required models in the `user_data/lintao/models` directory. If not, download them using the provided scripts or manually.

## Output
The expected output includes categorized documents, summaries in Markdown format, and interactive chatbot responses. The data formats are usually plain text, JSON, and Markdown.

## Usage
### Example: Classify and Summarize a Document
```python
from doc_professor import DocProfessor
import logging

logging.basicConfig(level=logging.DEBUG)

docc = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
docc.load_categories_map()

doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
doc_content = get_doc_content(doc_path)

classify_result = docc.classify_doc(doc_content[:1000])
category, keywords = docc.get_category_and_keywords(classify_result)

new_doc_path = docc.get_new_doc_path_based_on_category(doc_path, category[0])
docc.move_doc(doc_path, new_doc_path)

summary_path = docc.get_summary_path_based_on_category(doc_path, category[0])
summary = docc.summarize_doc(doc_content)
docc.dump_content_to_file(summary, summary_path)
```

### Example: Interactive Chatbot
```python
from doc_chat import DocChat
from pathlib import Path
from utils.embedding import LocalEmbedding
from knowledge import KnowledgeRetrieval

user_dir = Path(__file__).resolve().parents[0] / 'lintao'
embedding_model = LocalEmbedding()
knowledge_db_path = user_dir / "database/knowledge_db.pkl"
vector_db_path = user_dir / "database/vector_db.pkl"
knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)
doc_chat = DocChat(model='gpt-4o-2024-05-13', user_root_path=user_dir, knowledge_retrieval=knowledge_retrieval)

response = doc_chat.generate_response("What is the Hop in traceroute")
print("Response:", response)
```

## Configuration
### Environment Variables
- `HF_TOKEN`: Hugging Face API token for embedding models.

### Configuration Files
- `category_map.json`: Maps document categories to keywords.
- `llm_config.json`: Configuration for language models.

## Contributing
### Guidelines
1. Fork the repository and create a new branch for your feature or bugfix.
2. Ensure your code adheres to the existing coding standards and passes all tests.
3. Submit a pull request with a detailed description of your changes.

### Coding Standards
- Follow PEP 8 for Python code.
- Write clear and concise commit messages.
- Include docstrings for all functions and classes.

## License
This project is licensed under the [MIT License](LICENSE).

## Contact Information
For support or inquiries, please contact:
- **Lintao**: lint22@mails.tsinghua.edu.cn

Thank you for using DocProfessor!