#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from sqlalchemy.dialects.mysql import TEXT

from ...baseModel import BaseModel, db


class Report(BaseModel):
    """ 测试报告表 """
    __tablename__ = 'report'
    name = db.Column(TEXT, nullable=True, comment='用例的名称集合')
    status = db.Column(db.String(10), nullable=True, comment='阅读状态，已读、未读')
    is_passed = db.Column(db.Integer, default=1, comment='是否全部通过，1全部通过，0有报错')
    performer = db.Column(db.String(16), nullable=True, comment='执行者')
    run_type = db.Column(db.String(10), default='task', nullable=True, comment='报告类型，task/case')

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')
    project = db.relationship('Project', backref='reports')

    def to_dict(self):
        return self.base_to_dict()

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )
