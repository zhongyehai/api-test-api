""" 修改排序工具 """


def auto_num(num, model, **kwargs):
    """
    自动返回 model表中**kwargs筛选条件下的模块编号num的最大值+1，用于插入数据时排序
    如：用例集表中，某project_id对应的用例集编号
    num     数据名     project_id
    1       name        6
    2       name        2
    2       name        6
    返回3
    """
    if not num:
        if not model.query.filter_by(**kwargs).all():
            return 1
        else:
            return model.query.filter_by(**kwargs).order_by(model.num.desc()).first().num + 1
    return num


def num_sort(new_num, old_num, list_data, old_data):
    """ 修改排序, 自动按新旧序号重新排列 用于修改数据存库时 """
    if old_data not in list_data:
        old_data.num = len(list_data) + 1
    else:
        _temp_data = list_data.pop(list_data.index(old_data))
        list_data.insert(new_num - 1, _temp_data)
        if old_num == new_num:
            pass
        elif old_num > new_num:
            for n, m in enumerate(list_data[new_num - 1:old_num + 1]):
                m.num = new_num + n

        elif old_data.num < new_num:
            for n, m in enumerate(list_data[old_num - 1:new_num + 1]):
                m.num = old_num + n
