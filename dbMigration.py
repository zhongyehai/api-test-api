#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : dbMigration.py
# @Software: PyCharm
import json
from collections import OrderedDict

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app.baseModel import db
from app.api.user.models import User, Permission, Role
from app.api.config.models import Config, ConfigType
from main import app

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)

make_user_info_mapping = {
    "姓名": "name",
    "身份证号": "ssn",
    "手机号": "phone_number",
    "银行卡": "credit_card_number",
    "地址": "address",
    "公司名": "company",
    "统一社会信用代码": "credit_code",
    "邮箱": "company_email",
    "工作": "job",
    "ipv4": "ipv4",
    "ipv6": "ipv6"
}

kym_keword = [
    {
        "topic": "使用群体",
        "children": [
            {"topic": "产品使用群体是哪些？"},
            {"topic": "用户与用户之间有什么关联？"},
            {"topic": "用户为什么提这个需求？"},
            {"topic": "用户为什么提这个需求？"},
            {"topic": "用户最关心的是什么？"},
            {"topic": "用户的实际使用环境是什么？"}
        ]
    },
    {
        "topic": "里程碑",
        "children": [
            {"topic": "需求评审时间？"},
            {"topic": "开发提测时间？"},
            {"topic": "测试周期测试时间多长？"},
            {"topic": "轮次安排进行几轮测试？"},
            {"topic": "UAT验收时间？"},
            {"topic": "上线时间？"}
        ]
    },
    {
        "topic": "涉及人员",
        "children": [
            {"topic": "负责迭代的产品是谁？"},
            {"topic": "后端开发是谁经验如何？"},
            {"topic": "前端开发是谁经验如何？"},
            {"topic": "测试人员是谁？"}
        ]
    },
    {
        "topic": "涉及模块",
        "children": [
            {"topic": "项目中涉及哪些模块，对应的开发责任人是谁？"}
        ]
    },
    {
        "topic": "项目信息",
        "children": [
            {"topic": "项目背景是什么？"},
            {"topic": "这个项目由什么需要特别注意的地方？"},
            {"topic": "可以向谁进一步了解项目信息？"},
            {"topic": "有没有文档、手册、材料等可供参考？"},
            {"topic": "这是全新的产品还是维护升级的？"},
            {"topic": "有没有竞品分析结果或同类产品可供参考？"},
            {"topic": "历史版本曾今发生过那些重大故障？"}
        ]
    },
    {
        "topic": "测试信息",
        "children": [
            {"topic": "会使用到的测试账号有哪些？"},
            {"topic": "会用到的测试地址？"},
            {"topic": "有没有不太熟悉、掌握的流程？"}
        ]
    },
    {
        "topic": "设备工具",
        "children": [
            {"topic": "测试过程中是否会用到其他测试设备资源是否够（Ukey、手机、平板）？"},
            {"topic": "会用到什么测试工具会不会使用？"}
        ]
    },
    {
        "topic": "测试团队",
        "children": [
            {"topic": "有几个测试团队负责测试？"},
            {"topic": "负责测试的人员组成情况？"},
            {"topic": "测试人员的经验如何？"},
            {"topic": "测试人员对被测对象的熟悉程度如何？"},
            {"topic": "测试人员是专职的还是兼职的？"},
            {"topic": "测试人手是否充足？"}
        ]
    },
    {
        "topic": "测试项",
        "children": [
            {"topic": "主要的测试内容有哪些？"},
            {"topic": "哪部分可以降低优先级或者先不测试？"},
            {"topic": "哪些内容是新增或修改？"},
            {"topic": "是否涉及历史数据迁移测试？"},
            {"topic": "是否涉及与外系统联调测试？"},
            {"topic": "是否需要进行性能、兼容性、安全测试？"}
        ]
    }
]

# 响应数据源
response_data_source_mapping = [
    {"label": "响应体", "value": "content"},
    {"label": "响应头部信息", "value": "headers"},
    {"label": "响应cookies", "value": "cookies"},
    {"label": "正则表达式（从响应体提取）", "value": "regexp"}
]

# python数据类型
data_type_mapping = [
    {"label": "普通字符串", "value": "str"},
    {"label": "json字符串", "value": "json"},
    {"label": "整数", "value": "int"},
    {"label": "小数", "value": "float"},
    {"label": "列表", "value": "list"},
    {"label": "字典", "value": "dict"},
    {"label": "自定义函数", "value": "func"},
    {"label": "自定义变量", "value": "variable"},
]


@manager.command
def init_role():
    """ 初始化权限、角色 """
    print(f'{"=" * 15} 开始创建角色 {"=" * 15}')
    roles_permissions_map = OrderedDict()
    roles_permissions_map[u'测试人员'] = ['COMMON']
    roles_permissions_map[u'管理员'] = ['COMMON', 'ADMINISTER']
    for role_name in roles_permissions_map:
        role = Role.get_first(name=role_name)
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)
            role.permission = []
        for permission_name in roles_permissions_map[role_name]:
            permission = Permission.get_first(name=permission_name)
            if permission is None:
                permission = Permission(name=permission_name)
                db.session.add(permission)
            role.permission.append(permission)
            db.session.commit()
    print(f'{"=" * 15} 角色创建成功 {"=" * 15}')


@manager.command
def init_user():
    """ 初始化用户 """
    print(f'{"=" * 15} 开始创建管理员用户 {"=" * 15}')
    user_list = [
        {'account': 'admin', 'password': '123456', 'name': '管理员', 'status': 1, 'role_id': 2},
        {'account': 'common', 'password': 'common', 'name': '公用账号', 'status': 1, 'role_id': 1}
    ]
    for user_info in user_list:
        if User.get_first(account=user_info['account']) is None:
            User().create(user_info)
            print(f'{"=" * 15} 用户 {user_info["name"]} 创建成功 {"=" * 15}')
    print(f'{"=" * 15} 用户创建完成 {"=" * 15}')


@manager.command
def init_config_type():
    """ 初始化配置类型 """
    print(f'{"=" * 15} 开始创建配置类型 {"=" * 15}')
    config_type_list = [
        {'name': '系统配置', 'desc': '全局配置'},
        {'name': '邮箱', 'desc': '邮箱服务器'}
    ]
    for data in config_type_list:
        if ConfigType.get_first(name=data["name"]) is None:
            ConfigType().create(data)
            print(f'{"=" * 15} 配置类型 {data["name"]} 创建成功 {"=" * 15}')
    print(f'{"=" * 15} 配置类型创建完成 {"=" * 15}')


@manager.command
def init_config():
    """ 初始化配置 """
    print(f'{"=" * 15} 开始创建配置 {"=" * 15}')
    conf_list = [
        {'name': 'QQ邮箱', 'value': 'smtp.qq.com', 'type': '邮箱', 'desc': 'QQ邮箱服务器'},
        {'name': 'http_methods', 'value': 'GET,POST,PUT,DELETE', 'type': '系统配置', 'desc': 'http请求方式，以英文的 "," 隔开'},
        {'name': 'make_user_info_mapping', 'value': json.dumps(make_user_info_mapping, ensure_ascii=False),
         'type': '系统配置', 'desc': '生成用户信息的可选项，映射faker的模块（不了解faker模块勿改）'},
        {'name': 'response_data_source_mapping', 'value': json.dumps(response_data_source_mapping, ensure_ascii=False),
         'type': '系统配置', 'desc': '响应对象数据源映射'},
        {'name': 'data_type_mapping', 'value': json.dumps(data_type_mapping, ensure_ascii=False),
         'type': '系统配置', 'desc': 'python数据类型映射'},
        {'name': 'yapi_host', 'value': '', 'type': '系统配置', 'desc': 'yapi域名'},
        {'name': 'yapi_account', 'value': '', 'type': '系统配置', 'desc': 'yapi账号'},
        {'name': 'yapi_password', 'value': '', 'type': '系统配置', 'desc': 'yapi密码'},
        {'name': 'ignore_keyword_for_group', 'value': '[]', 'type': '系统配置', 'desc': '不需要从yapi同步的分组关键字'},
        {'name': 'ignore_keyword_for_project', 'value': '[]', 'type': '系统配置', 'desc': '不需要从yapi同步的服务关键字'},
        {'name': 'kym', 'value': json.dumps(kym_keword, ensure_ascii=False, indent=4), 'type': '系统配置',
         'desc': 'KYM分析项'},
        {'name': 'default_diff_message_send_addr', 'value': '', 'type': '系统配置', 'desc': 'yapi接口监控报告默认发送钉钉机器人地址'},
        {'name': 'run_time_error_message_send_addr', 'value': '', 'type': '系统配置', 'desc': '运行测试用例时，有错误信息实时通知地址'},
    ]
    for data in conf_list:
        if Config.get_first(name=data["name"]) is None:
            Config().create(data)
            print(f'{"=" * 15} 配置 {data["name"]} 创建成功 {"=" * 15}')
    print(f'{"=" * 15} 配置创建完成 {"=" * 15}')


@manager.command
def init():
    """ 初始化 权限、角色、管理员 """
    print(f'{"=" * 15} 正在初始化数据 {"=" * 15}')
    init_role()
    init_user()
    init_config_type()
    init_config()
    print(f'{"=" * 15} 数据初始化完毕 {"=" * 15}')


"""
初始化数据库
python dbMigration.py db init
python dbMigration.py db migrate
python dbMigration.py db upgrade

初始化数据
python dbMigration.py init
"""

if __name__ == '__main__':
    manager.run()
