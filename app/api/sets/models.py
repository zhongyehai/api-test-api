#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from ...baseModel import BaseModel, db


class Set(BaseModel):
    """ 用例集表 """
    __tablename__ = 'sets'

    name = db.Column(db.String(50), nullable=True, comment='用例集名称')
    num = db.Column(db.Integer(), nullable=True, comment='用例集在对应项目下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='用例集级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级用例集id')
    yapi_id = db.Column(db.Integer(), comment='当前用例集在yapi平台对应的项目id')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')

    project = db.relationship('Project', backref='sets')  # 一对多
    cases = db.relationship('Case', order_by='Case.num.asc()', lazy='dynamic')

    def to_dict(self):
        return self.base_to_dict()

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name == form.name.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
