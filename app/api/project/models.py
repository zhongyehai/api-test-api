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

    name = db.Column(db.String(255), nullable=True, comment='项目名称')
    manager = db.Column(db.Integer(), nullable=True, default=1, comment='项目管理员id，默认为admin')
    variables = db.Column(db.Text(), default='[{"key": null, "value": null, "remark": null}]', comment='项目的公共变量')
    headers = db.Column(db.Text(), default='[{"key": null, "value": null, "remark": null}]', comment='项目的公共头部信息')
    func_files = db.Column(db.Text(), nullable=True, default='[]', comment='引用的函数文件')
    dev = db.Column(db.String(255), default='', comment='开发环境域名')
    test = db.Column(db.String(255), default='', comment='测试环境域名')
    uat = db.Column(db.String(255), default='', comment='uat环境域名')
    production = db.Column(db.String(255), default='', comment='生产环境域名')
    yapi_id = db.Column(db.Integer(), default=None, comment='对应YapiProject表里面的原始数据在yapi平台的id')

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
        return self.base_to_dict(to_dict=["hosts", "variables", "headers", "func_files"])


class YapiProject(BaseModel):
    """ yapi的项目表 """
    __tablename__ = 'yapi_project'

    yapi_group = db.Column(db.Integer(), comment='当前项目归属于yapi平台分组的id')
    yapi_name = db.Column(db.String(255), comment='当前项目在yapi平台的名字')
    yapi_id = db.Column(db.Integer(), comment='当前项目在yapi平台的id')
    yapi_data = db.Column(db.Text, comment='当前项目在yapi平台的数据')

    def to_dict(self):
        """ 转字典 """
        return self.base_to_dict()
