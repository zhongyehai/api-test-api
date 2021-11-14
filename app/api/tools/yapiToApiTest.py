""" yapi 的数据同步到 api-test """

import re

import requests
from flask import request

from .. import api
from ..project.models import Project
from ...baseModel import db
from ..module.models import Module
from ..sets.models import Set
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
    return [{'id': group['_id'], 'name': group['group_name']} for group in group_list if group['group_name'] != '个人空间']


def get_group(group_id, headers):
    """ 根据 yapi 的分组id，获取分组信息 """
    group = requests.get(f'{host}/api/group/get?id={group_id}', headers=headers).json()['data']
    return {'id': group['_id'], 'name': group['group_name']}


def get_yapi_project_list(group_id, headers):
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
    data = [{'id': project['_id'], 'name': project['name']} for project in project_list]
    print(data)
    return data


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


def update_group_to_project(yapi_project):
    """ yapi 的分组更新到测试平台的项目 """
    with db.auto_commit():
        project = Project.get_first(yapi_id=yapi_project['id']) or Project()
    project.yapi_id = yapi_project['id']
    project.name = yapi_project['name']
    if not project.id:
        db.session.add(project)
    return project


def update_project_to_module(project, yapi_module):
    """ yapi 的项目更新到测试平台的模块 """
    module = Module.get_first(project_id=project.id, yapi_id=yapi_module['id']) or Module()
    module.project_id = project.id
    module.yapi_id = yapi_module['id']
    module.name = yapi_module['name']
    module.num = module.get_new_num(None, project_id=project.id)
    if not module.id:
        db.session.add(module)
    return module


def update_project_to_case_set(project, yapi_module):
    """ yapi 的项目更新到测试平台的用例集 """
    case_set = Set.get_first(project_id=project.id, yapi_id=yapi_module['id']) or Set()
    case_set.project_id = project.id
    case_set.yapi_id = yapi_module['id']
    case_set.name = yapi_module['name']
    case_set.num = case_set.get_new_num(None, project_id=project.id)
    if not case_set.id:
        db.session.add(case_set)
    return case_set


def update_module_to_module(project, parent, yapi_module):
    """ yapi 的模块更新到测试平台的模块 """
    module = Module.get_first(project_id=project.id, yapi_id=yapi_module['id']) or Module()
    module.project_id = project.id
    module.yapi_id = yapi_module['id']
    module.name = yapi_module['name']
    module.parent = parent.id
    module.num = module.get_new_num(None, project_id=project.id)
    if not module.id:
        db.session.add(module)
    return module


def update_api_to_api(project, module_and_api):
    """ 更新接口 """
    module_id = ''
    for yapi_api in module_and_api.get('list', []):
        print(
            f'接口：{ {"id": yapi_api["_id"], "name": yapi_api["title"], "path": yapi_api["path"], "method": yapi_api["method"]} }')
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
        group_list = [get_group(Project.get_first(id=request.json.get('id')).yapi_id, headers)]
    else:
        # group_list = [get_group_list(headers)[1]]
        group_list = get_group_list(headers)

    # 把yapi的分组信息更新到测试平台的项目
    for yapi_group in group_list:
        print(f'分组：{yapi_group}')
        api_test_project = update_group_to_project(yapi_group)

        # 把yapi的项目更新到测试平台的一级模块、一级用例集
        # for yapi_project in [get_yapi_project_list(yapi_group['id'], headers)[-2]]:
        for yapi_project in get_yapi_project_list(yapi_group['id'], headers):
            print(f'项目：{yapi_project}')
            api_test_module = update_project_to_module(api_test_project, yapi_project)
            update_project_to_case_set(api_test_project, yapi_project)

            # 把yapi的模块更新到测试平台的二级模块
            for yapi_module in get_module_list(yapi_project['id'], headers):
                print(f'模块：{yapi_module}')
                update_module_to_module(api_test_project, api_test_module, yapi_module)

            for module_and_api in get_module_and_api(yapi_project['id'], headers):  # 遍历接口列表
                update_api_to_api(api_test_project, module_and_api)  # 更新接口信息
    return restful.success('数据更新完成')

    #
    # if request.json and request.json.get('id'):  # 有项目id，则只更新对应项目下的信息
    #     current_project = Project.get_first(id=request.json.get('id'))
    #     # 更新项目
    #     group = get_group(current_project.yapi_id, headers)
    #     api_test_project = update_group_to_project(group)
    #
    #     # 把yapi的项目更新到测试平台的一级模块、一级用例集
    #     for yapi_project in get_yapi_project_list(group['id'], headers):
    #         print(f'项目：\n{yapi_project}')
    #         api_test_module = update_project_to_module(api_test_project, yapi_project)
    #         update_project_to_case_set(api_test_project, yapi_project)
    #
    #         # 把yapi的模块更新到测试平台的二级模块
    #         for yapi_module in get_module_list(yapi_project['id'], headers):
    #             print(f'模块：\n{yapi_module}')
    #             update_module_to_module(api_test_project, api_test_module, yapi_module)
    #
    #         for module_and_api in get_module_and_api(yapi_project['id'], headers):  # 遍历接口列表
    #             print(f'接口：\n{yapi_project} ')
    #             update_api_to_api(api_test_project, module_and_api)  # 更新接口信息
    #
    # else:  # 没有项目id，则更新所有
    #
    #     # 把yapi的分组信息更新到测试平台的项目
    #     for yapi_group in get_group_list(headers):
    #         print(f'分组：\n{yapi_group}')
    #         api_test_project = update_group_to_project(yapi_group)
    #
    #         # 把yapi的项目更新到测试平台的一级模块、一级用例集
    #         for yapi_project in get_yapi_project_list(yapi_group['id'], headers):
    #             print(f'项目：\n{yapi_project}')
    #             api_test_module = update_project_to_module(api_test_project, yapi_project)
    #             update_project_to_case_set(api_test_project, yapi_project)
    #
    #             # 把yapi的模块更新到测试平台的二级模块
    #             for yapi_module in get_module_list(yapi_project['id'], headers):
    #                 print(f'模块：\n{yapi_module}')
    #                 update_module_to_module(api_test_project, api_test_module, yapi_module)
    #
    #             for module_and_api in get_module_and_api(yapi_project['id'], headers):  # 遍历接口列表
    #                 print(f'接口：\n{yapi_project} ')
    #                 update_api_to_api(api_test_project, module_and_api)  # 更新接口信息
    #
    # return restful.success('数据更新完成')
