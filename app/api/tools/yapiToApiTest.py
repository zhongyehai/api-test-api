""" yapi 的数据同步到 api-test """

import re

import requests
from flask import request

from .. import api
from ..project.models import Project
from ...baseModel import db
from ..module.models import Module
from ..apiMsg.models import ApiMsg
from ...utils import restful
from config.config import conf
from ...utils.required import login_required

host = conf['yapi']['host']
account = conf['yapi']['account']
password = conf['yapi']['password']


def get_yapi_header():
    """ 登录yapi，获取set-cookie """
    login_res = requests.post(
        f'{host}/api/user/login',
        json={"email": "yehai.zhong@xintech.cn", "password": "Sc123456"}
    ).headers['Set-Cookie']
    return {
        'Cookie': '_yapi_token=' + re.findall('_yapi_token=(.+?); ', login_res)[0] + '; ' +
                  '_yapi_uid=' + re.findall('_yapi_uid=(.+?); ', login_res)[0],
    }


def get_group_list(headers):
    """ 获取分组列表
    yapi接口响应关键数据
    {
        "data": [
            {
                "_id": 119
            }
        ]
    }
    """
    group_list = requests.get(f'{host}/api/group/list', headers=headers).json()['data']
    return [group['_id'] for group in group_list]


def get_project_list(group_id, headers):
    """ 获取指定分组下的项目列表
    yapi接口响应
    {
        "data": {
            "list": [
                {
                    "_id": 74,
                    "name": "XXX项目",
                    "group_id": 41
                }
            ]
        }
    }
    """
    project_list = requests.get(
        f'{host}/api/project/list?group_id={group_id}&page=1&limit=100',
        headers=headers,
    ).json()['data']['list']
    return [{'id': project['_id'], 'name': project['name']} for project in project_list]


def get_module_list(project_id, headers):
    """ 获取模块id
    yapi 接口响应
    {
        "_id": 74,
        "name": "OCR重构",
        "cat": [
            {
                "_id": 419,
                "name": "公共分类",
                "project_id": 74,
            }
        ],
    }
    """
    module_list = requests.get(
        f'{host}/api/project/get?id={project_id}', headers=headers
    ).json().get('data', {}).get('cat', [])
    return [{'id': module['_id'], 'project_id': module['project_id'], 'name': module['name']} for module in module_list]


def get_module_and_api(project_id, headers):
    """ 导出项目下的模块和接口
    yapi 接口返回
    [
      {
        "list": [
          {
            "_id": 2406,
            "method": "POST",
            "catid": 427,
            "title": "识别二维码/条形码",
            "path": "/api/v1/ocr/codeOcr/findBarCodeResult",
            "project_id": 74,
            "req_query": [
              {
                "name": "fileId",
                "example": "850970",
                "desc": ""
              }
            ],
            "req_headers": [
              {
                "name": "Content-Type",
                "value": "application/x-www-form-urlencoded"
              }
            ],
            "desc": "",
            "req_body_type": "form",
            "req_body_form": [],
            "req_body_other": ""
          }
        ]
      }
    ]
    """
    return requests.get(
        f'{host}/api/plugin/export?type=json&pid={project_id}&status=all&isWiki=false',
        headers=headers
    ).json()


def update_project(yapi_project):
    """ 更新项目 """
    with db.auto_commit():
        project = Project.get_first(yapi_id=yapi_project['id']) or Project()
    project.yapi_id = yapi_project['id']
    project.name = yapi_project['name']
    if not project.id:
        db.session.add(project)
    return project


def update_module(project, yapi_module):
    """ 更新模块 """
    module = Module.get_first(project_id=project.id, yapi_id=yapi_module['id']) or Module()
    module.project_id = project.id
    module.yapi_id = yapi_module['id']
    module.name = yapi_module['name']
    module.num = module.get_new_num(None, project_id=project.id)
    if not module.id:
        db.session.add(module)


def update_api(project, module_and_api):
    """ 更新接口 """
    module_id = ''
    for yapi_api in module_and_api.get('list', []):
        print(yapi_api)
        module_id = module_id or Module.get_first(yapi_id=yapi_api['catid']).id
        # 更新接口信息
        api_msg = ApiMsg.get_first(module_id=module_id, yapi_id=yapi_api['_id']) or ApiMsg()
        api_msg.num = api_msg.get_new_num(None, module_id=module_id)
        api_msg.name = yapi_api.get('title')
        api_msg.desc = yapi_api.get('desc')
        api_msg.method = yapi_api.get('method')
        api_msg.addr = yapi_api.get('path')
        api_msg.data_type = yapi_api.get('req_body_type')
        api_msg.module_id = module_id
        api_msg.project_id = project.id
        api_msg.yapi_id = yapi_api.get('_id')
        if not api_msg.id:
            db.session.add(api_msg)


@api.route('/project/pull', methods=['POST'])
@login_required
def yapi_to_api_test():
    """ 同步yapi的项目、模块、接口到测试平台 """
    headers = get_yapi_header()  # 获取头部信息

    if request.json and request.json.get('id'):  # 有项目id，则只更新对应项目下的信息
        project = Project.get_first(id=request.json.get('id'))

        for yapi_module in get_module_list(project.yapi_id, headers):  # 遍历模块列表
            print(yapi_module)
            update_module(project, yapi_module)  # 更新模块信息

        for module_and_api in get_module_and_api(project.yapi_id, headers):  # 遍历接口列表
            print(f'\n\n  {project.yapi_id}  \n\n')
            update_api(project, module_and_api)  # 更新接口信息
    else:  # 没有项目id，则更新所有
        for group_id in get_group_list(headers):  # 遍历分组列表
            for yapi_project in get_project_list(group_id, headers):
                print(yapi_project)
                project = update_project(yapi_project)  # 更新项目信息

                for yapi_module in get_module_list(yapi_project['id'], headers):  # 遍历模块列表
                    print(yapi_module)
                    update_module(project, yapi_module)  # 更新模块信息

                for module_and_api in get_module_and_api(yapi_project['id'], headers):  # 遍历接口列表
                    print(f'\n\n  {yapi_project}  \n\n')
                    update_api(project, module_and_api)  # 更新接口信息

    return restful.success('数据更新完成')
