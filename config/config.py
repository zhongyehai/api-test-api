#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : config.py
# @Software: PyCharm

import os
import time
import email
import six
import multiprocessing
import logging
from logging.handlers import TimedRotatingFileHandler

import urllib3.fields as f
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.utils.yamlUtil import load
from app.utils.httprunner import built_in as assert_func_file

# 从 httpRunner.built_in 中获取断言方式并映射为字典和列表，分别给前端和运行测试用例时反射断言
assert_mapping, assert_mapping_list = {}, []
for func in dir(assert_func_file):
    if func.startswith('_') and not func.startswith('__'):
        doc = getattr(assert_func_file, func).__doc__.strip()  # 函数注释
        assert_mapping.setdefault(doc, func)
        assert_mapping_list.append({'value': doc})

# 请求方法列表
method_mapping = [{'value': method} for method in ['GET', 'POST', 'PUT', 'DELETE']]

basedir, conf = os.path.abspath('.'), load(os.path.abspath('.') + '/config/config.yaml')


def my_format_header_param(name, value):
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    if not six.PY3 and isinstance(value, six.text_type):  # Python 2:
        value = value.encode('utf-8')
    value = email.utils.encode_rfc2231(value, 'utf-8')
    value = '%s*=%s' % (name, value)
    return value


# 猴子补丁，修复request上传文件时，不能传中文
f.format_header_param = my_format_header_param


class SafeLog(TimedRotatingFileHandler):
    """ 因为TimedRotatingFileHandler在多进程访问log文件时，切分log日志会报错文件被占用，所以修复这个问题 """

    def __init__(self, *args, **kwargs):
        super(SafeLog, self).__init__(*args, **kwargs)
        self.suffix_time = ""
        self.origin_basename = self.baseFilename

    def shouldRollover(self, record):
        time_tuple = time.localtime()
        return 1 if self.suffix_time != time.strftime(self.suffix, time_tuple) \
                    or not os.path.exists(self.origin_basename + '.' + self.suffix_time) else 0

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = self.origin_basename + '.' + self.suffix_time

        self.mode = 'a'

        with multiprocessing.Lock():
            if self.backupCount > 0:
                for s in self.getFilesToDelete():
                    os.remove(s)

        if not self.delay:
            self.stream = self._open()

    def getFilesToDelete(self):
        # 将源代码的 self.baseFilename 改为 self.origin_basename
        dir_name, base_name = os.path.split(self.origin_basename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = base_name + "."
        p_len = len(prefix)
        for fileName in file_names:
            if fileName[:p_len] == prefix:
                suffix = fileName[p_len:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dir_name, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result


def config_log():
    """ 日志配置 """
    handler = SafeLog(
        filename=os.path.abspath('../..') + r'/logs/' + 'logger',
        interval=1,
        backupCount=50,
        when="D",
        encoding='UTF-8')
    handler.setLevel(logging.DEBUG)  # 日志级别
    handler.suffix = "%Y-%m-%d.log"
    # handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(lineno)s - %(message)s'))
    return handler


class ProductionConfig:
    """ 生产环境数据库 """
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://' \
                              f'{conf["db"]["user"]}:' \
                              f'{conf["db"]["password"]}@' \
                              f'{conf["db"]["host"]}:' \
                              f'{conf["db"]["port"]}/' \
                              f'{conf["db"]["database"]}?charset=utf8mb4'
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI, engine_options={'pool_pre_ping': True})
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 1000
    SQLALCHEMY_POOL_RECYCLE = 1800

    SECRET_KEY = conf['SECRET_KEY']
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    CSRF_ENABLED = True
    UPLOAD_FOLDER = '/upload'
    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        pass


if __name__ == '__main__':
    pass
