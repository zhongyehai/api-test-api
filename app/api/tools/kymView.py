# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:02
# @Author : ZhongYeHai
# @Site :
# @File : accountView.py
# @Software: PyCharm
import json

from flask import request
from flask_login import current_user

from .. import api
from .models import KYMModule, db
from ..config.models import Config
from ...utils import restful
from ...baseView import BaseMethodView
from ...utils.required import login_required


@api.route('/kym/project', methods=['POST'])
@login_required
def add_kym_project():
    """ kym添加项目 """
    if KYMModule.get_first(project=request.json['project']):
        return restful.fail(f"项目 {request.json['project']} 已存在")
    with db.auto_commit():
        kym_data = {"nodeData": {"topic": request.json['project'], "root": True, "children": []}}
        kym_data['nodeData']['children'] = json.loads(Config.get_first(name='kym').value)
        kym = KYMModule()
        kym.project = request.json['project']
        kym.kym = json.dumps(kym_data, ensure_ascii=False, indent=4)
        kym.create_user = current_user.id
        db.session.add(kym)
    return restful.success('新增成功', data=kym.to_dict())


@api.route('/kym/project/list')
@login_required
def get_kym_project_list():
    """ kym项目列表 """
    project_list = KYMModule.query.with_entities(KYMModule.project).distinct().all()
    return restful.success('获取成功', data=[{'key': project[0], 'value': project[0]} for project in project_list])


class KYMView(BaseMethodView):
    """ KYM管理 """

    def get(self):
        """ 获取KYM """
        return restful.success('获取成功', data=KYMModule.get_first(project=request.args.get('project')).to_dict())

    def put(self):
        """ 修改KYM号 """
        kym = KYMModule.get_first(project=request.json['project'])
        with db.auto_commit():
            kym.kym = json.dumps(request.json['kym'], ensure_ascii=False, indent=4)
        return restful.success('修改成功', data=kym.to_dict())


api.add_url_rule('/kym', view_func=KYMView.as_view('kym'))
