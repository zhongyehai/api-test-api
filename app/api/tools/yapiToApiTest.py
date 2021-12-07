""" yapi 的数据同步到 api-test """
import json
import re

import requests
from flask import request

from .. import api
from ..config.models import Config
from ..project.models import Project
from ...baseModel import db
from ..module.models import Module
from ..apiMsg.models import ApiMsg
from ...utils import restful
from ...utils.required import login_required


def pop_ignore(data_list, ignore_list, key):
    """ 过滤要排除的项 """
    for index, project in enumerate(data_list):
        for ignore in ignore_list:
            if ignore and ignore in project[key]:
                data_list.pop(index)
    return data_list


def update_project(yapi_project):
    """ yapi 的项目信息更新到测试平台的项目 """
    with db.auto_commit():
        project = Project.get_first(yapi_id=yapi_project['_id']) or Project()
        project.yapi_id = yapi_project['_id']
        project.name = yapi_project['name']
        if not project.id:
            db.session.add(project)
    api.logger.info('update_project_project: ', project.to_dict())
    return project


def update_module(project, yapi_module):
    """ yapi 的模块更新到测试平台的模块 """
    with db.auto_commit():
        module = Module.get_first(yapi_id=yapi_module['id'])
        if not module:
            module = Module()
            module.num = module.get_new_num(None, project_id=project.id)
        module.project_id = project.id
        module.yapi_id = yapi_module['id']
        module.name = yapi_module['name']
        if not module.id:
            db.session.add(module)
    return module


def update_api(project, module_and_api):
    """ 更新接口 """
    module_id = ''
    with db.auto_commit():
        for api_index, yapi_api in enumerate(module_and_api.get('list', [])):
            api.logger.info(
                f'接口：{ {"id": yapi_api["_id"], "name": yapi_api["title"], "path": yapi_api["path"], "method": yapi_api["method"]} }')
            module_id = module_id or Module.get_first(yapi_id=yapi_api['catid']).id

            # 更新接口信息
            api_msg = ApiMsg.get_first(addr=yapi_api['path'], yapi_id=yapi_api['_id'])
            if not api_msg:
                api_msg = ApiMsg()
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


def get_yapi_header(host, account, password):
    """ 登录yapi，获取set-cookie """
    login_res = requests.post(
        f'{host}/api/user/login',
        json={"email": account, "password": password}
    ).headers['Set-Cookie']
    return {
        'Cookie': '_yapi_token=' + re.findall('_yapi_token=(.+?); ', login_res)[0] + '; ' +
                  '_yapi_uid=' + re.findall('_yapi_uid=(.+?); ', login_res)[0],
    }


def get_group_list(host, headers, ignore_group):
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
    return pop_ignore(group_list, ignore_group, 'group_name')


def get_group(host, group_id, headers):
    """ 根据 yapi 的分组id，获取分组信息 """
    group = requests.get(f'{host}/api/group/get?id={group_id}', headers=headers).json()['data']
    return {'id': group['_id'], 'name': group['group_name']}


def get_yapi_project_list(host, group_id, headers, ignore_project):
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
        f'{host}/api/project/list?group_id={group_id}&page=1&limit=1000',
        headers=headers,
    ).json()['data']['list']
    return pop_ignore(project_list, ignore_project, 'name')


def get_module_list(host, project_id, headers):
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


def get_module_and_api(host, project_id, headers):
    """ 导出项目下的模块和接口
    yapi 接口返回
    [
      {
        "list": [
          {
            "_id": 2406,
            "method": "POST",
            "catid": 427,  # yapi的模块id
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


@api.route('/project/pull', methods=['POST'])
@login_required
def yapi_to_api_test():
    """ 同步yapi的项目、模块、接口到测试平台 """

    # 获取yapi平台的配置信息
    conf_list = Config.query.filter(Config.name.in_([
        'yapi_host', 'yapi_account', 'yapi_password', 'ignore_keyword_for_group', 'ignore_keyword_for_project'
    ])).all()
    conf = {conf.name: conf.value for conf in conf_list}
    yapi_host, yapi_account, yapi_password = conf.get('yapi_host'), conf.get('yapi_account'), conf.get('yapi_password')
    ignore_group = json.loads(conf.get('ignore_keyword_for_group', '[]'))
    ignore_project = json.loads(conf.get('ignore_keyword_for_project', '[]'))

    headers = get_yapi_header(yapi_host, yapi_account, yapi_password)  # 获取头部信息
    group_list = get_group_list(yapi_host, headers, ignore_group)  # 所有分组列表
    project_list = []

    # 传了指定的项目id，则只更新对应项目下的信息
    if request.json and request.json.get('id'):
        yapi_id = Project.get_first(id=request.json.get('id')).yapi_id
        for group in group_list:
            for project in get_yapi_project_list(yapi_host, group['_id'], headers, ignore_project):
                if project['_id'] == yapi_id:
                    project_list = [project]
                    break
    else:  # 没有指定项目id，则全量更新
        for group in group_list:
            project_list += get_yapi_project_list(yapi_host, group['_id'], headers, ignore_project)

    for yapi_project in project_list:

        # 更新项目
        api.logger.info(f'项目：{yapi_project}')
        api_test_project = update_project(yapi_project)

        # 更新模块
        for yapi_module in get_module_list(yapi_host, yapi_project['_id'], headers):
            api.logger.info(f'模块：{yapi_module}')
            update_module(api_test_project, yapi_module)

        # 更新接口信息
        for module_and_api in get_module_and_api(yapi_host, yapi_project['_id'], headers):
            update_api(api_test_project, module_and_api)

    return restful.success('数据更新完成')
