import logging

import pandas as pd


class MyDatabase:
    def __init__(self, user_dir):
        self.user_dir = user_dir
        self.db_df = None
        self.load_db()

    def load_db(self):
        if self.db_df is None:
            # 创建数据库
            self.db_df = pd.DataFrame(
                columns=['doc_name', 'category', 'keywords', 'doc_path', 'summary_path', 'info_path'])
            self.db_df.to_csv(self.user_dir + '/database/database.csv', index=False)
            logging.info(f'Created database at {self.user_dir}/database/database.csv')
        else:
            self.db_df = pd.read_csv(self.user_dir + '/database/database.csv')
            logging.info(f'Loaded database from {self.user_dir}/database/database.csv')

    def update_doc_info(self, doc_name, category, keywords, doc_path, summary_path, info_path):
        # Update the database with the doc info
        new_row = pd.DataFrame([[doc_name, category, keywords, doc_path, summary_path, info_path]],
                               columns=['doc_name', 'category', 'keywords', 'doc_path', 'summary_path', 'info_path'])
        self.db_df = pd.concat([self.db_df, new_row], ignore_index=True)
        self.db_df.to_csv(self.user_dir + '/database/database.csv', index=False)
        logging.info(f'Updated database with doc {doc_name}')

    def get_info_path(self, file_name):
        # Get the info path of the file
        return self.db_df[self.db_df['doc_name'] == file_name]['info_path'].values[0]

    def get_summary_path(self, file_name):
        # Get the summary path of the file
        return self.db_df[self.db_df['doc_name'] == file_name]['summary_path'].values[0]

    def delete_doc_info(self, file_name):
        # Delete the doc info from the database
        self.db_df = self.db_df[self.db_df['doc_name'] != file_name]
        self.db_df.to_csv(self.user_dir + '/database/database.csv', index=False)
        logging.info(f'Deleted doc {file_name} from the database')
