#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from ....baseModel import BaseModel, db


class Case(BaseModel):
    """ 用例表 """
    __tablename__ = 'case'
    num = db.Column(db.Integer(), nullable=True, comment='用例序号')
    name = db.Column(db.String(255), nullable=True, comment='用例名称')
    desc = db.Column(db.Text(), comment='用例描述')
    is_run = db.Column(db.Boolean(), default=True, comment='是否执行此用例，True执行，False不执行，默认执行')
    run_times = db.Column(db.Integer(), default=1, comment='执行次数，默认执行1次')
    choice_host = db.Column(db.String(10), default='test', comment='运行环境')
    func_files = db.Column(db.Text(), comment='用例需要引用的函数list')
    variables = db.Column(db.Text(), comment='用例级的公共参数')
    headers = db.Column(db.Text(), comment='用例级的头部信息')
    before_case = db.Column(db.Text(), default='[]', comment='当前用例引用的前置用例')
    after_case = db.Column(db.Text(), default='[]', comment='当前用例引用的后置用例')

    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), comment='所属的用例集id')

    def to_dict(self):
        return self.base_to_dict(to_dict=['func_files', 'variables', 'headers', 'before_case', 'after_case'])

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.setId.data:
            filters.append(cls.set_id == form.setId.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
