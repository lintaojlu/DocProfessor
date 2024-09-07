# Author: Lintao
import pickledb
import os
import logging


class KnowledgeDB:
    _instances = {}

    def __new__(cls, db_path, auto_dump=True):
        if db_path not in cls._instances:
            instance = super(KnowledgeDB, cls).__new__(cls)
            instance.__init__(db_path, auto_dump)
            cls._instances[db_path] = instance
        return cls._instances[db_path]

    def __init__(self, db_path, auto_dump=True):
        self.logger = logging.getLogger("DATABASE")
        self.db_path = db_path
        self.auto_dump = auto_dump
        if not hasattr(self, 'db'):
            self.db = self.load_db()

    def load_db(self):
        if os.path.exists(self.db_path):
            self.logger.info(f"使用已有数据库：{self.db_path}")
        else:
            self.logger.info(f"不存在数据库：{self.db_path}，创建新数据库")
        result = pickledb.load(self.db_path, self.auto_dump, sig=False)
        self.logger.info(f"数据库已加载：{self.db_path}")
        return result

    def get(self, key):
        return self.db.get(key)

    def set(self, key, value):
        return self.db.set(key, value)

    def delete(self, key):
        try:
            result: bool = self.db.rem(key)
        except KeyError:
            return False
        self.logger.debug(f"键{key}已删除")
        return result

    def dump(self):
        result = self.db.dump()
        self.logger.debug(f"database {self.db_path} 已持久化到{self.db_path}")
        return result

    def clear(self):
        result = self.db.deldb()
        self.logger.debug(f"database {self.db_path} 已清空")
        return result
