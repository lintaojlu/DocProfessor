# Author: Lintao
import os
import PyPDF2


def get_files_in_directory(directory_path):
    """
    获取指定目录下所有文件的路径。
w
    :param directory_path: 文件夹路径或文件路径
    :return: 包含所有文件路径的列表
    """
    files_list = []

    # 判断是文件还是文件夹
    if os.path.isfile(directory_path):
        files_list.append(directory_path)
    elif os.path.isdir(directory_path):
        # 遍历文件夹中的所有文件
        for root, _, files in os.walk(directory_path):
            for file in files:
                files_list.append(os.path.join(root, file))
    else:
        raise ValueError("路径无效：不是文件或文件夹")

    return files_list


def get_doc_content(doc_path):
    # Open the PDF file
    with open(doc_path, 'rb') as file:
        # Create a PDF reader object
        reader = PyPDF2.PdfReader(file)

        # Initialize a variable to hold the text content
        text_content = ""

        # Iterate through all the pages and extract text
        for page in reader.pages:
            text_content += page.extract_text()

    return text_content
