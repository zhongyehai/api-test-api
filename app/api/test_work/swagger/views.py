#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/12/31 11:32
# @Author : ZhongYeHai
# @Site : 
# @File : swagger.py
# @Software: PyCharm
import json

import requests
from flask import request

from app.api import api
from app.api.api_test.project.models import Project
from app.api.api_test.module.models import Module
from app.api.api_test.apiMsg.models import ApiMsg
from app.utils import restful
from app.utils.required import login_required


def get_swagger_data(swagger_addr):
    """ 获取swagger数据 """
    return requests.get(swagger_addr).json()


def get_parsed_module(module_list, project_id, module_name):
    """ 获取已解析的模块 """

    # 已获取，则直接返回
    if module_name in module_list:
        return module_list.get(module_name)

    # 已解析，则直接获取
    module = Module.get_first(project_id=project_id, name=module_name)
    if module:
        module_list[module.name] = module
        return module

    # 未解析，则先解析并保存，再返回
    module = Module().create({'project_id': project_id, 'name': module_name})
    module_list[module.name] = module
    return module


@api.route('/swagger/pull', methods=['POST'])
@login_required
def swagger_pull():
    """ 根据指定服务的swagger拉取所有数据 """
    project = Project.get_first(id=request.json.get('id'))  # 项目数据
    swagger_data = get_swagger_data(project.swagger)  # swagger数据
    module_list = {}
    for api_addr, api_data in swagger_data['paths'].items():
        for api_method, api_detail in api_data.items():
            module = get_parsed_module(module_list, project.id, api_detail['tags'][0])

            # 请求数据类型
            if swagger_data.get('swagger'):  # swagger2
                content_type = api_detail.get('consumes', ['json'])[0]
            else:  # swagger3
                content_type = api_detail.get('requestBody', {}).get('content', {}).get('content', 'application/json')

            format_data = {
                'project_id': project.id,
                'module_id': module.id,
                'name': api_detail['summary'],
                'method': api_method.upper(),
                'addr': api_addr,
                'data_type': 'json' if 'json' in content_type else 'form' if 'data' in content_type else 'xml'
            }

            # URL中可能有参数化"/XxXx/xx/{batchNo}"
            api_msg = ApiMsg.get_first(addr=api_addr, module_id=module.id)

            # 可能是参数化导致没查到，可能是数据库中本来就没有
            if not api_msg:
                if '{' in api_addr:
                    split_swagger_addr = api_addr.split('{')[0]
                    api_msg = ApiMsg.query.filter(ApiMsg.addr.like('%' + split_swagger_addr + '$%'), ApiMsg.module_id==module.id).first()
                    if api_msg:  # 参数化导致没查到，则更新
                        format_data['addr'] = split_swagger_addr + '$' + api_msg.addr.split('$')[1]
                        api_msg.update(format_data)
                    else:  # 新增
                        format_data['num'] = ApiMsg.get_insert_num(module_id=module.id)
                        ApiMsg().create(format_data)
                else:  # 新增
                    format_data['num'] = ApiMsg.get_insert_num(module_id=module.id)
                    ApiMsg().create(format_data)
            else:  # 有就更新
                api_msg.update(format_data)

    return restful.success('数据更新完成')
