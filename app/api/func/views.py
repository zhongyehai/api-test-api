#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

import importlib
import types
import traceback

from flask import current_app
from flask_login import current_user

from ...utils import restful
from ...utils.required import login_required
from ...utils.globalVariable import os, FUNC_ADDRESS
from ...utils.parse import parse_function, extract_functions
from .. import api
from ...baseModel import db
from ...baseView import BaseMethodView
from .models import Func
from .forms import HasFuncForm, SaveFuncForm, CreatFuncForm, DebuggerFuncForm, DeleteFuncForm, GetFuncFileForm


@api.route('/func/list', methods=['GET'])
@login_required
def func_list():
    """ 查找所有自定义函数文件 """
    form = GetFuncFileForm()
    if form.validate():
        return restful.success('获取成功', data=Func.make_pagination(form))
    return restful.error(form.get_error())


@api.route('/func/debug', methods=['POST'])
@login_required
def debug_func():
    """ 函数调试 """
    form = DebuggerFuncForm()
    if form.validate():
        func_file_name, debug_data = form.func.func_file_name, form.debug_data.data
        # 把自定义函数脚本内容写入到python脚本中
        with open(os.path.join(FUNC_ADDRESS, f'{func_file_name}.py'), 'w', encoding='utf8') as file:
            file.write(form.func.func_data)
        # 动态导入脚本
        try:
            import_path = f'func_list.{func_file_name}'
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                     isinstance(item, types.FunctionType)}
            ext_func = extract_functions(debug_data)
            func = parse_function(ext_func[0])
            result = module_functions_dict[func['func_name']](*func['args'], **func['kwargs'])
            return restful.success(msg='执行成功，请查看执行结果', result=result)
        except Exception as e:
            current_app.logger.info(str(e))
            error_data = '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
            return restful.fail(msg='语法错误，请检查', result=error_data)
    return restful.fail(msg=form.get_error())


class FuncView(BaseMethodView):

    def get(self):
        form = HasFuncForm()
        if form.validate():
            return restful.success(msg='获取成功', func_data=form.func.func_data)
        return restful.fail(form.get_error())

    def post(self):
        form = CreatFuncForm()
        form.create_user.data = current_user.id
        if form.validate():
            with db.auto_commit():
                func = Func(func_file_name=form.func_file_name.data, create_user=current_user.id)
                db.session.add(func)
            return restful.success(f'函数文件 {form.func_file_name.data} 创建成功')
        return restful.fail(form.get_error())

    def put(self):
        form = SaveFuncForm()
        if form.validate():
            with db.auto_commit():
                form.func.func_file_name, form.func.func_data = form.func_file_name.data, form.func_data.data
            return restful.success(f'函数文件 {form.func_file_name.data} 修改成功', data=form.func.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteFuncForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.func)
            return restful.success(f'函数文件 {form.func_file_name.data} 删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/func', view_func=FuncView.as_view('func'))
