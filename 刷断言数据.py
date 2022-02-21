#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : dbMigration.py
# @Software: PyCharm
import json
import re

from app.baseModel import db
from app.api.api_test.step.models import Step
from app.api.api_test.apiMsg.models import ApiMsg
from app.utils.parse import extract_functions, parse_function, extract_variables
from main import app

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


def init_data():
    """ 刷数据，数据提取和断言 """
    step_list = Step.get_all()
    step_list.extend(ApiMsg.get_all())
    for step in step_list:
        print(f'开始处理{step.name}')
        # 刷断言数据
        new_validates = []
        validates = json.loads(step.validates)
        for validate in validates:
            if validate.get('key'):
                keys = validate.get('key').split('.')
                data_source = keys.pop(0)

                value = validate.get('value')
                data_type = re.findall("'(.+?)'", str(type(eval(value))))[0]
                if data_type == 'str':
                    try:
                        json.loads(value)
                        data_type = 'json'
                    except Exception as error:
                        pass

                new_validates.append({
                    'data_source': data_source,
                    'key': '.'.join(keys),
                    'validate_type': validate.get('validate_type'),
                    'data_type': data_type,
                    'value': value,
                })
                with db.auto_commit():
                    if new_validates:
                        step.validates = json.dumps(new_validates, ensure_ascii=False, indent=4)

        # 刷数据提取数据
        new_extracts = []
        extracts = json.loads(step.extracts)
        for extract in extracts:
            if extract.get('key'):
                extract_value = extract.get('value')
                ext_func = extract_functions(extract_value)
                if ext_func:  # 自定义函数
                    func = parse_function(ext_func[0])
                    func_name, args, kwargs = func['func_name'], func['args'], func['kwargs']

                    args_and_kwargs = []
                    data_source = None
                    # 处理args参数
                    for arg in args:
                        # 如果是自定义变量则不改变, 如果不是，则把数据源去掉
                        if extract_variables(arg).__len__() >= 1:
                            args_and_kwargs.append(arg)
                        else:
                            expression = arg.split('.')
                            data_source = expression.pop(0)
                            args_and_kwargs.append(f'{expression}')

                    # 处理kwargs参数
                    for kw_key, kw_value in kwargs.items():
                        # 如果是自定义变量则不改变, 如果不是，则把数据源加上
                        if extract_variables(kw_value).__len__() >= 1:
                            args_and_kwargs.append(f'{kw_key}={kw_value}')
                        else:
                            expression = kw_value.split('.')
                            data_source = expression.pop(0)
                            args_and_kwargs.append(f'{expression}')
                            args_and_kwargs.append(f'{kw_key}={data_source}.{kw_value}')

                    new_extracts.append({
                        "key": extract.get('key'),
                        "data_source": '.'.join(data_source),
                        "value": '${' + f'{func_name}({",".join(args_and_kwargs)})' + '}',
                        "remark": extract.get('remark')
                    })
                else:  # 不是自定义函数
                    expression = extract.get('value').split('.')
                    new_extracts.append({
                        "key": extract.get('key'),
                        "data_source": expression.pop(0),
                        "value": '.'.join(expression),
                        "remark": extract.get('remark')
                    })
                with db.auto_commit():
                    if new_extracts:
                        step.extracts = json.dumps(new_extracts, ensure_ascii=False, indent=4)
    print('数据修改完毕！')


if __name__ == '__main__':
    init_data()
