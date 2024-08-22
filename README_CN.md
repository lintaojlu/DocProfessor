# DocProfessor

### 项目简介

**DocProfessor** 是一个智能文档处理和知识管理工具，旨在通过自然语言处理技术帮助用户自动化地解析、分类、提取关键字、生成摘要，并将文档内容添加到知识库中。项目由Lintao开发，联系方式为lint22@mails.tsinghua.edu.cn。

### 目录结构

以下是项目的主要目录和文件结构：

```
- .git/
- .idea/
- __pycache__/
- server/
- user_data/
- utils/
- doc_chat.py
- doc_professor.py
- doc_resolver.py
- doc_study.py
- knowledge.py
- requirements.txt
- README.md
```

### 安装

1. 克隆项目到本地：

```bash
git clone <项目地址>
cd DocProfessor
```

2. 创建并激活虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # 对于Windows用户，使用 `venv\Scripts\activate`
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

### 输出

根据不同的模块，输出位置和数据格式可能有所不同。具体的输出将在各个模块的使用示例中详细说明。

### 使用

以下是一些常见的使用示例：

#### 生成对话

```python
from doc_chat import DocAssistant

if __name__ == "__main__":
    user_dir = 'user_data/lintao'
    embedding_model = LocalEmbedding()  # 假设有一个 LocalEmbedding 类
    knowledge_db_path = f"{user_dir}/database/knowledge_db.pkl"
    vector_db_path = f"{user_dir}/database/vector_db.pkl"
    knowledge_retrieval = KnowledgeRetrieval(embedding_model, knowledge_db_path, vector_db_path)
    doc_chat = DocAssistant(model='gpt-4o-2024-05-13', user_dir=user_dir, knowledge_retrieval=knowledge_retrieval)

    for chunk in doc_chat.answer_question_with_knowledge("What is the Hop in traceroute"):
        print("Chunk:", chunk)
```

#### 解析文档

```python
from doc_professor import DocProfessor

if __name__ == "__main__":
    docc = DocProfessor(user_dir='user_data/lintao/', model='gpt-4o-2024-05-13')
    docc.load_categories_map()
    doc_path = 'user_data/lintao/data/研究论文/Carisimo 等 - 2023 - A Hop Away from Everywhere A View of the Intercon.pdf'
    docc.documents_to_be_resolved[doc_path] = 0
    documents_status = docc.resolve_docs()
    print(f"Documents status: {documents_status}")
```

### 配置

项目中涉及到一些配置文件和环境变量：

- `user_data/lintao/config/llm_config.json`：存储了不同语言模型和API服务的参数配置。
- `user_data/lintao/config/category_map.json`：定义了文档分类和关键字映射。

### 贡献

如果你想为该项目做出贡献，请遵循以下步骤：

1. Fork 此仓库。
2. 创建一个新的分支：`git checkout -b feature/your-feature`
3. 提交你的更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 创建一个Pull Request。

### 许可

该项目使用 [MIT 许可证](LICENSE)。

### 联系方式

如有任何问题或建议，请联系项目维护者 Lintao：lint22@mails.tsinghua.edu.cn。