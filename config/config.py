#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : config.py
# @Software: PyCharm

import os
import email
import six

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
