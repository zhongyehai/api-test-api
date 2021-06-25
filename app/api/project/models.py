#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from flask_login import current_user

from ...baseModel import BaseModel, db


class Project(BaseModel):
    """ 项目表 """
    __tablename__ = 'project'

    name = db.Column(db.String(63), nullable=True, unique=True, comment='项目名称')
    manager = db.Column(db.Integer(), nullable=True, comment='项目管理员id')
    hosts = db.Column(db.String(1024), nullable=True, comment='环境地址，可多个')
    variables = db.Column(db.String(2048), comment='项目的公共变量')
    headers = db.Column(db.String(1024), comment='项目的公共头部信息')
    func_files = db.Column(db.String(64), nullable=True, comment='引用的函数文件')

    modules = db.relationship('Module', order_by='Module.num.asc()', lazy='dynamic')
    case_sets = db.relationship('Set', order_by='Set.num.asc()', lazy='dynamic')

    @property
    def headers_boj(self):
        return self.loads(self.headers)

    @property
    def variables_boj(self):
        return self.loads(self.variables)

    def is_not_manager(self):
        """ 判断用户非项目负责人 """
        return current_user.id != self.manager

    @classmethod
    def is_not_manager_id(cls, project_id):
        """ 判断当前用户非当前数据的负责人 """
        return cls.get_first(id=project_id).manager != current_user.id

    @classmethod
    def is_manager_id(cls, project_id):
        """ 判断当前用户为当前数据的负责人 """
        return cls.get_first(id=project_id).manager == current_user.id

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(Project.name.like(f'%{form.name.data}%'))
        if form.manager.data:
            filters.append(Project.manager == form.manager.data)
        if form.create_user.data:
            filters.append(Project.create_user == form.create_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())

    def to_dict(self):
        """ 自定义序列化器，把模型的每个字段转为字典，方便返回给前端 """
        return self.base_to_dict(json_to_dict_list=["hosts", "variables", "headers", "func_files"])
