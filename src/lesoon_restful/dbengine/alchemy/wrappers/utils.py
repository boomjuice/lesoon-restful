import datetime as dt
import decimal
import typing as t

from flask_sqlalchemy import Model
from lesoon_common.exceptions import ServiceError
from lesoon_common.globals import current_app
from lesoon_common.response import ResponseCode
from lesoon_common.utils.str import udlcase
from marshmallow.utils import from_iso_datetime

from lesoon_restful.dbengine.alchemy.utils import parse_valid_model_attribute
from lesoon_restful.dbengine.alchemy.wrappers.dataclass import ImportParam
from lesoon_restful.dbengine.alchemy.wrappers.dataclass import ImportParseResult


def parse_import_data(import_data: ImportParam,
                      model: t.Type[Model]) -> ImportParseResult:
    """
    解析导入数据,将其转换为对应的模型, 并记录转换过程中的异常
    :param import_data:  导入数据类
    :param model: 数据导入的表对应的模型
    :return:
    """
    # 初始化数据
    union_key_set: t.Set[str] = {udlcase(uk) for uk in import_data.union_key}
    union_key_value_set: t.Set[str] = set()
    obj_list: t.List[Model] = list()
    parse_err_list: t.List[str] = list()
    insert_err_list: t.List[str] = list()
    col_attrs = list()

    try:
        for col_name in import_data.col_names:
            attr = parse_valid_model_attribute(col_name, model)
            col_attrs.append(attr)

        flag = True
        for rid, row in enumerate(import_data.data_list):
            # 唯一约束键对应的值
            union_key_value = ''
            # 表对应的model对象
            obj = model()
            for cid, attr in enumerate(col_attrs):
                if cid >= len(row):
                    raise AttributeError(f'列[{attr.name}]在数据集中不存在')
                col_value = row[cid]

                # Excel中的位置
                # chr(65) = A
                # chr(65+cid) = Excel中的列
                obj.excel_row_pos = rid + import_data.import_start_index
                obj.excel_col_pos = chr(65 + cid)
                excel_position = (
                    f'Excel [{obj.excel_row_pos}行,{obj.excel_col_pos}列]'
                    f'{attr.name}:{col_value}')

                # 值为空
                if not bool(col_value):
                    # 不允许为空
                    if import_data.must_array[cid]:
                        parse_err_list.append(excel_position + '不能为空')
                        flag = False
                        break
                    # 允许为空
                    else:
                        continue

                # 类型检测
                if attr.type.python_type is int:
                    if not col_value.lstrip('-').isdigit():
                        parse_err_list.append(excel_position + '必须为整数')
                        flag = False
                        break

                if attr.type.python_type in (decimal.Decimal, float):
                    if not col_value.lstrip('-').replace(',', '', 1).isdigit():
                        parse_err_list.append(excel_position + '必须为数值')
                        flag = False
                        break

                if attr.type.python_type is dt.datetime:
                    try:
                        col_value = from_iso_datetime(col_value)
                    except ValueError:
                        parse_err_list.append(excel_position +
                                              '日期格式无法解析,需遵循ISO8601标准')
                        flag = False
                        break

                # 约束赋值
                if attr.name in union_key_set:
                    union_key_value += col_value

                # 设置对象值
                setattr(obj, attr.name, col_value)

            if union_key_value:
                # excel中是否已存在当前数据
                if union_key_value in union_key_value_set:
                    parse_err_list.append(
                        f'Excel [{rid + import_data.import_start_index}行,] '
                        f'违反唯一约束[{import_data.union_key_name}]')
                    flag = False
                    continue
                else:
                    union_key_value_set.add(union_key_value)

            if flag:
                obj_list.append(obj)

    except Exception as e:
        raise ServiceError(ResponseCode.Error, f'导入数据异常:{str(e)}')

    current_app.logger.info(f'解析成功的行数为:{len(obj_list)}')
    import_parse_result = ImportParseResult(obj_list, parse_err_list,
                                            insert_err_list)
    return import_parse_result
