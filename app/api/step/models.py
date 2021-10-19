#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/4/16 9:42
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm

from ...baseModel import BaseModel, db


class Step(BaseModel):
    """ 用例数据表 """
    __tablename__ = 'step'
    num = db.Column(db.Integer(), nullable=True, comment='步骤序号，执行顺序按序号来')
    is_run = db.Column(db.Boolean(), default=True, comment='是否执行此步骤，True执行，False不执行，默认执行')
    run_times = db.Column(db.Integer(), default=1, comment='执行次数，默认执行1次')

    name = db.Column(db.String(50), comment='步骤名称')
    up_func = db.Column(db.String(128), comment='步骤执行前的函数')
    down_func = db.Column(db.String(128), comment='步骤执行后的函数')
    headers = db.Column(db.Text(), comment='头部信息')
    params = db.Column(db.Text(), comment='url参数', default=u'[]')
    data_form = db.Column(db.Text(), comment='form-data参数')
    data_json = db.Column(db.Text(), comment='json参数')
    extracts = db.Column(db.Text(), comment='提取信息')
    validates = db.Column(db.Text(), comment='断言信息')
    data_driver = db.Column(db.Text(), default='{}', comment='数据驱动，若此字段有值，则走数据驱动的解析')

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', backref='steps')

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))

    api_id = db.Column(db.Integer, db.ForeignKey('apis.id'))
    api = db.relationship('ApiMsg', backref='apis')

    @classmethod
    def sort_num_by_list(cls, step_list):
        """ 重新排序列表，索引为num值 """
        with db.auto_commit():
            for index, step in enumerate(step_list):
                if step['num'] != index:
                    cls.get_first(id=step.get('id')).num = index

    def to_dict(self):
        """ 转为字典输出 """
        return self.base_to_dict(
            json_to_dict_list=["headers", "params", "data_form", "data_json", "extracts", "validates", "data_driver"]
        )
