# DocProfessor

## Description
DocProfessor is an intelligent assistant application designed to help users interact with and manage their document collections. It integrates a knowledge retrieval system and a user interface built with Gradio, providing functionalities such as document classification, summarization, and intelligent responses to user queries.

## Installation
To install and set up DocProfessor, follow these steps:

1. **Clone the repository:**
    ```sh
    git clone <repository_url>
    cd doc_professor
    ```

2. **Create and activate a virtual environment (optional but recommended):**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Output
The expected output of the project includes:
- **Related knowledge** retrieved from a local knowledge base.
- **Generated responses** from the GPT-4 model displayed in a chatbot interface.
- **Classified documents** with associated categories and keywords.
- **Document summaries** in Markdown format.

## Usage
### Running the Gradio Interface
To start the Gradio interface, run the following command:
```sh
python web_test.py
```
This will launch a web interface where you can input queries and interact with the assistant.

### Example Code Snippets
#### Generating a Response
```python
from doc_chat import DocChat
from pathlib import Path

user_dir = Path('user_data/lintao')
embedding_model = LocalEmbedding()
knowledge_db_path = user_dir / "database/knowledge_db.pkl"
vector_db_path = user_dir / "database/vector_db.pkl"
knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)
doc_chat = DocChat(model='gpt-4o-2024-05-13', user_root_path=user_dir, knowledge_retrieval=knowledge_retrieval)

response = doc_chat.generate_response("What is the Hop in traceroute")
print("Response:", response)
```

### Document Classification and Summarization
```python
from doc_professor import DocProfessor
from utils.utils import get_doc_content

docc = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
docc.load_categories_map()
doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
doc_content = get_doc_content(doc_path)

classify_result = docc.classify_doc(doc_content[:1000])
category, keywords = docc.get_category_and_keywords(classify_result)
summary = docc.summarize_doc(doc_content)
docc.dump_content_to_file(summary, docc.get_summary_path_based_on_category(doc_path, category[0]))
```

## Configuration
### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key.
- `HF_TOKEN`: Your Hugging Face API token.

### Configuration Files
- `llm_config.json`: Contains settings for language models and API keys.
- `category_map.json`: Defines categories and keywords for document classification.

## Contributing
### Guidelines
1. **Fork the repository** and create your branch from `main`.
2. **Ensure your code adheres to the coding standards** and includes appropriate tests.
3. **Submit a pull request** with a clear description of your changes and the problem they solve.

### Coding Standards
- Follow PEP 8 guidelines for Python code.
- Write meaningful commit messages.
- Include docstrings and type annotations.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Contact Information
For support or inquiries, please contact Lintao at <email@example.com>.