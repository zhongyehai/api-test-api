#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


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


class YapiModule(BaseModel):
    """ yapi的模块表 """
    __tablename__ = 'yapi_module'

    yapi_project = db.Column(db.Integer(), comment='当前模块在yapi平台对应的项目id')
    yapi_name = db.Column(db.String(255), comment='当前模块在yapi平台的名字')
    yapi_id = db.Column(db.Integer(), comment='当前模块在yapi平台对应的模块id')
    yapi_data = db.Column(db.Text, comment='当前模块在yapi平台的数据')

    def to_dict(self):
        """ 转字典 """
        return self.base_to_dict()


class YapiApiMsg(BaseModel):
    """ yapi的接口表 """
    __tablename__ = 'yapi_apis'
    yapi_project = db.Column(db.Integer(), comment='当前接口在yapi平台对应的项目id')
    yapi_module = db.Column(db.Integer(), comment='当前接口在yapi平台对应的模块id')
    yapi_name = db.Column(db.String(255), comment='当前接口在yapi平台的名字')
    yapi_id = db.Column(db.Integer(), comment='当前接口在yapi平台对应的接口id')
    yapi_data = db.Column(db.Text, comment='当前接口在yapi平台的数据')

    def to_dict(self):
        """ 转字典 """
        return self.base_to_dict()


class YapiDiffRecord(BaseModel):
    """ 数据比对记录 """
    __tablename__ = 'yapi_diff_record'

    name = db.Column(db.String(255), comment='比对标识，全量比对，或者具体分组的比对')
    is_changed = db.Column(db.Integer, default=0, comment='对比结果，1有改变，0没有改变')
    diff_summary = db.Column(db.Text, comment='比对结果数据')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get('name'):
            filters.append(YapiDiffRecord.name.like(f'%{attr.get("name")}%'))
        if attr.get('create_user'):
            filters.append(YapiDiffRecord.create_user == attr.get('create_user'))
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            filters=filters,
            order_by=cls.created_time.desc())

    def to_dict(self):
        return self.base_to_dict()
