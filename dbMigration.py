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
from app.api.apiMsg.models import ApiMsg
from app.api.case.models import Case
from app.api.step.models import Step
from app.api.sets.models import Set
from app.api.func.models import Func
from app.api.module.models import Module
from app.api.project.models import Project
from app.api.report.models import Report
from app.api.task.models import Task, ApschedulerJobs
from app.api.user.models import User, Permission, Role
from app.api.config.models import Config, ConfigType
from main import app

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def init_admin():
    """ 初始化管理员用户 """
    if User.query.filter_by(name='管理员').first():
        print(f'{"=" * 15} 已存在管理员用户，可直接登录 {"=" * 15}')
        return
    else:
        print(f'{"=" * 15} 开始创建管理员用户 {"=" * 15}')
        with db.auto_commit():
            user = User()
            user.account = 'admin'
            user.password = '123456'
            user.name = '管理员'
            user.status = 1
            user.role_id = 2
            user.create_user = 1
            db.session.add(user)
        print(f'{"=" * 15} 创建管理员用户成功 {"=" * 15}')


@manager.command
def init_role():
    """ 初始化角色 """
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
def init_config_type():
    """ 初始化配置类型 """
    print(f'{"=" * 15} 开始创建配置类型 {"=" * 15}')
    config_type_list = [
        {'name': '系统配置', 'desc': '全局配置'},
        {'name': '邮箱', 'desc': '邮箱服务器'}
    ]
    for data in config_type_list:
        if ConfigType.get_first(name=data["name"]) is None:
            data['create_user'] = 1
            with db.auto_commit():
                config_type = ConfigType()
                config_type.create(data)
                db.session.add(config_type)
            print(f'{"=" * 15} 配置类型 {data["name"]} 创建成功 {"=" * 15}')
    print(f'{"=" * 15} 配置类型创建完成 {"=" * 15}')


@manager.command
def init_config():
    """ 初始化配置 """
    print(f'{"=" * 15} 开始创建配置 {"=" * 15}')
    conf_list = [
        {'name': 'QQ邮箱', 'value': 'smtp.qq.com', 'type': '邮箱', 'desc': 'QQ邮箱服务器'},
        {'name': 'make_user_info_mapping', 'value': json.dumps({
            "姓名": "name",
            "身份证号": "ssn",
            "手机号": "phone_number",
            "银行卡": "credit_card_number",
            "地址": "address",
            "公司名": "company",
            "邮箱": "company_email",
            "工作": "job",
            "ipv4": "ipv4",
            "ipv6": "ipv6"
        }, ensure_ascii=False), 'type': '系统配置', 'desc': '生成用户信息的可选项，映射faker的模块（不了解faker模块勿改）'}
    ]
    for data in conf_list:
        if Config.get_first(name=data["name"]) is None:
            data['create_user'] = 1
            with db.auto_commit():
                config = Config()
                config.create(data)
                db.session.add(config)
            print(f'{"=" * 15} 配置 {data["name"]} 创建成功 {"=" * 15}')
    print(f'{"=" * 15} 配置创建完成 {"=" * 15}')


@manager.command
def init():
    """ 初始化 权限、角色、管理员 """
    print(f'{"=" * 15} 正在初始化数据 {"=" * 15}')
    init_role()
    init_admin()
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
