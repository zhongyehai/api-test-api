#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/10/19 14:51
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm
import importlib
import os
import types

from sqlalchemy.dialects.mysql import LONGTEXT

from app.baseModel import BaseModel, db
from app.utils.globalVariable import FUNC_ADDRESS


class Func(BaseModel):
    """ 自定义函数 """
    __tablename__ = 'func'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='脚本名称')
    func_data = db.Column(LONGTEXT, default='', comment='脚本代码')

    @classmethod
    def create_func_file(cls):
        """ 创建所有自定义函数 py 文件 """
        for func in cls.get_all():
            with open(os.path.join(FUNC_ADDRESS, f'{func.name}.py'), 'w', encoding='utf8') as file:
                file.write(func.func_data)

    @classmethod
    def get_func_by_func_file_name(cls, func_file_name_list):
        """ 获取指定函数文件中的函数 """
        cls.create_func_file()  # 创建所有函数文件
        func_dict = {}
        for func_file_name in func_file_name_list:
            func_list = importlib.reload(importlib.import_module(f'func_list.{func_file_name}'))
            func_dict.update({
                name: item for name, item in vars(func_list).items() if isinstance(item, types.FunctionType)
            })
        return func_dict

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )
