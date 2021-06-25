#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm

from ...baseModel import BaseModel, db


class ApiMsg(BaseModel):
    """ 接口表 """
    __tablename__ = 'apis'
    num = db.Column(db.Integer(), nullable=True, comment='接口序号')
    name = db.Column(db.String(128), nullable=True, comment='接口名称')
    desc = db.Column(db.String(256), nullable=True, comment='接口描述')
    up_func = db.Column(db.String(128), comment='接口执行前的函数')
    down_func = db.Column(db.String(128), comment='接口执行后的函数')

    method = db.Column(db.String(32), nullable=True, comment='请求方式')
    host_index = db.Column(db.Integer, nullable=True, comment='从项目选择的host索引')
    addr = db.Column(db.Text(), nullable=True, comment='接口地址')
    headers = db.Column(db.String(2048), comment='头部信息')
    params = db.Column(db.Text(), comment='url参数')
    data_type = db.Column(db.String(32), nullable=True, default='json', comment='参数类型')
    data_form = db.Column(db.Text(), comment='form-data参数')
    data_json = db.Column(db.Text(), comment='json参数')
    extracts = db.Column(db.String(2048), comment='提取信息')
    validates = db.Column(db.String(2048), comment='断言信息')

    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), comment='所属的接口模块id')
    project_id = db.Column(db.Integer, nullable=True, comment='所属的项目id')

    def to_dict(self):
        """ 转为字典 """
        return self.base_to_dict(
            json_to_dict_list=['headers', 'params', 'data_form', 'data_json', 'extracts', 'validates']
        )

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(ApiMsg.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(ApiMsg.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=ApiMsg.num.asc()
        )
