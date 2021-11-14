#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm
from sqlalchemy.orm import backref

from ...baseModel import BaseModel, db


class ApiMsg(BaseModel):
    """ 接口表 """
    __tablename__ = 'apis'
    num = db.Column(db.Integer(), nullable=True, comment='接口序号')
    name = db.Column(db.String(50), nullable=True, comment='接口名称')
    desc = db.Column(db.Text(), default='', nullable=True, comment='接口描述')
    up_func = db.Column(db.String(128), default='', comment='接口执行前的函数')
    down_func = db.Column(db.String(128), default='', comment='接口执行后的函数')

    method = db.Column(db.String(10), nullable=True, comment='请求方式')
    choice_host = db.Column(db.String(10), default='test', comment='选择的环境')
    addr = db.Column(db.Text(), nullable=True, comment='接口地址')
    headers = db.Column(db.Text(), default='[{"key": null, "remark": null, "value": null}]', comment='头部信息')
    params = db.Column(db.Text(), default='[{"key": null, "value": null}]', comment='url参数')
    data_type = db.Column(db.String(10), nullable=True, default='json', comment='参数类型，json、form-data、xml')
    data_form = db.Column(db.Text(),
                          default='[{"data_type": null, "key": null, "remark": null, "value": null}]',
                          comment='form-data参数')
    data_json = db.Column(db.Text(), default='{}', comment='json参数')
    data_xml = db.Column(db.Text(), default='', comment='xml参数')
    extracts = db.Column(db.Text(), default='[{"key": null, "value": null, "remark": null}]', comment='提取信息')
    validates = db.Column(db.Text(),
                          default='[{"key": null, "remark": null, "validate_type": null, "value": null}]',
                          comment='断言信息')

    module_id = db.Column(db.Integer(), db.ForeignKey('module.id'), comment='所属的接口模块id')
    project_id = db.Column(db.Integer(), nullable=True, comment='所属的项目id')
    yapi_id = db.Column(db.Integer(), comment='当前接口在yapi平台的id')

    module = db.relationship('Module', backref='apis')

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
