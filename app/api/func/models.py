#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/10/19 14:51
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm
import os

from sqlalchemy.dialects.mysql import LONGTEXT

from ...baseModel import BaseModel, db


class Func(BaseModel):
    """ 自定义函数 """
    __tablename__ = 'func'

    name = db.Column(db.String(50), nullable=True, unique=True, comment='脚本名称')
    func_data = db.Column(LONGTEXT, default='', comment='脚本代码')

    @classmethod
    def create_func_file(cls, addr):
        """ 创建所有自定义函数 py 文件 """
        for func in cls.get_all():
            with open(os.path.join(addr, f'{func.name}.py'), 'w', encoding='utf8') as file:
                file.write(func.func_data)

    def to_dict(self):
        """ 返回字典 """
        return self.base_to_dict()

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
