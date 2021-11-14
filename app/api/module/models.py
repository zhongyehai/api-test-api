#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from ...baseModel import BaseModel, db


class Module(BaseModel):
    """ 模块表 """
    __tablename__ = 'module'
    name = db.Column(db.String(50), nullable=True, comment='模块名')
    num = db.Column(db.Integer(), nullable=True, comment='模块在对应项目下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='模块级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级模块id')
    yapi_id = db.Column(db.Integer(), comment='当前模块在yapi平台对应的项目/模块id')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')

    project = db.relationship('Project', backref='modules')  # 一对多

    def to_dict(self):
        """ 转字典 """
        return self.base_to_dict()

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
