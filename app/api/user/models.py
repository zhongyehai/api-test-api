#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask_login import UserMixin, current_user
from flask import current_app

from ... import login_manager
from ...baseModel import BaseModel, db
from config.config import conf

# 角色 与 权限映射表
roles_permissions = db.Table(
    'roles_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')))


class Role(BaseModel):
    """ 角色表 """
    __tablename__ = 'role'
    name = db.Column(db.String(30), unique=True, comment='角色名称')
    users = db.relationship('User', back_populates='role')
    permission = db.relationship('Permission', secondary=roles_permissions, back_populates='role')


class Permission(BaseModel):
    """ 角色对应的权限 """
    __tablename__ = 'permission'
    name = db.Column(db.String(30), unique=True, comment='权限名称')
    role = db.relationship('Role', secondary=roles_permissions, back_populates='permission')


class User(UserMixin, BaseModel):
    """ 用户表 """
    __tablename__ = 'users'
    account = db.Column(db.String(50), unique=True, index=True, comment='账号')
    password_hash = db.Column(db.String(255), comment='密码')
    name = db.Column(db.String(12), comment='姓名')
    status = db.Column(db.Integer, default=1, comment='状态，1为启用，2为冻结')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), comment='所属的角色id')
    role = db.relationship('Role', back_populates='users')

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, _password):
        """ 设置加密密码 """
        self.password_hash = generate_password_hash(_password)

    def verify_password(self, password):
        """ 校验密码 """
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=conf['token_time_out']):
        """ 生成token，默认有效期一个小时 """
        return Serializer(current_app.config['SECRET_KEY'], expiration).dumps({'id': self.id, 'name': self.name}).decode('utf-8')

    @staticmethod
    def parse_token(token):
        """ 校验token是否过期，或者是否合法 """
        try:
            data = Serializer(current_app.config['SECRET_KEY']).loads(token.encode('utf-8'))
            return data
        except:
            return False

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(User.name.like(f'%{form.name.data}%'))
        if form.account.data:
            filters.append(User.account.like(f'%{form.account.data}%'))
        if form.status.data:
            filters.append(User.status == form.status.data)
        if form.role_id.data:
            filters.append(User.role_id == form.role_id.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())

    def to_dict(self, *args, **kwargs):
        return super(User, self).to_dict(pop_list=['password_hash'])

    def can(self, permission_name):
        """ 判断当前用户是否有当前请求的权限 """
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permission


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
