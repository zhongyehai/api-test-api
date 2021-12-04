#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/6/21 9:28
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
from flask import request
from flask_login import current_user

from ...utils import restful
from ...utils.required import login_required

from .models import Config, ConfigType, db
from .forms import (
    GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, GetConfigTypeListForm,
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from ...baseView import BaseMethodView
from .. import api


@api.route('/configType/list', methods=['GET'])
@login_required
def conf_type_list():
    form = GetConfigTypeListForm()
    if form.validate():
        return restful.success(data=ConfigType.make_pagination(form))
    return restful.error(form.get_error())


class ConfigTypeView(BaseMethodView):

    def get(self):
        form = GetConfigTypeForm()
        if form.validate():
            return restful.success('获取成功', data=form.conf.to_dict())
        return restful.error(form.get_error())

    def post(self):
        form = PostConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                config_type = ConfigType()
                config_type.create(form.data)
                db.session.add(config_type)
            return restful.success('新增成功', data=config_type.to_dict())
        return restful.error(form.get_error())

    def put(self):
        form = PutConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                delattr(form.data, 'name')
                form.config_type.update(form.data, spike_list=['key'])
            return restful.success('修改成功', data=form.conf.to_dict())
        return restful.error(form.get_error())

    def delete(self):
        form = DeleteConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.config_type)
            return restful.success('删除成功')
        return restful.error(form.get_error())


@api.route('/config/list', methods=['GET'])
@login_required
def conf_list():
    form = GetConfigListForm()
    if form.validate():
        return restful.success(data=Config.make_pagination(form))
    return restful.error(form.get_error())


@api.route('/config/configByName', methods=['GET'])
@login_required
def get_conf_by_name():
    """ 根据配置名获取配置 """
    return restful.success(data=Config.get_first(name=request.args.get('name')).to_dict())


class ConfigView(BaseMethodView):

    def get(self):
        form = GetConfigForm()
        if form.validate():
            return restful.success('获取成功', data=form.conf.to_dict())
        return restful.error(form.get_error())

    def post(self):
        form = PostConfigForm()
        if form.validate():
            form.create_user.data = current_user.id
            with db.auto_commit():
                config = Config()
                config.create(form.data)
                db.session.add(config)
            return restful.success('新增成功', data=config.to_dict())
        return restful.error(form.get_error())

    def put(self):
        form = PutConfigForm()
        if form.validate():
            with db.auto_commit():
                form.conf.update(form.data)
            return restful.success('修改成功', data=form.conf.to_dict())
        return restful.error(form.get_error())

    def delete(self):
        form = DeleteConfigForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.conf)
            return restful.success('删除成功')
        return restful.error(form.get_error())


api.add_url_rule('/config', view_func=ConfigView.as_view('config'))
api.add_url_rule('/configType', view_func=ConfigTypeView.as_view('configType'))
