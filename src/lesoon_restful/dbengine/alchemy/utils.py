""" Sqlalchemy解析模块.
将python对象解析成sqlalchemy对象以供查询
"""
import typing as t

from flask_sqlalchemy import Model
from lesoon_common import LesoonQuery
from lesoon_common.utils.str import udlcase
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.util import _ORMJoin
from sqlalchemy.sql import expression as SqlaExp
from sqlalchemy.sql.annotation import Annotated
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.selectable import Alias
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.selectable import Subquery

from lesoon_restful.exceptions import FilterInvalid

SqlaExp = SqlaExp.BinaryExpression
SqlaExpList = t.List[SqlaExp]
TableType = t.Union[Table, Alias, t.Type[Model]]


def parse_columns(data: dict,
                  model: TableType) -> t.List[t.Tuple[Column, t.Any]]:
    """
    通过查询参数字典解析出对应的Model中的字段.

    Args:
        data: 查询参数   {"id":"1"},{"a.id":{"eq":"2"}},...
        model: sqlalchemy.Model

    Returns:
        columns: [(Column(name='id),1), ...]
    """
    columns: t.List[t.Tuple[Column, t.Any]] = []
    if len(data) == 0:
        return columns

    for key, value in list(data.items()):
        name = udlcase(key)
        column_name = parse_prefix_alias(name, model)
        if not column_name:
            continue
        column = parse_model_attribute(name=column_name, model=model)
        if column is None:
            continue
        columns.append((column, value))
        del data[key]

    return columns


def parse_prefix_alias(name: str, model: TableType) -> t.Optional[str]:
    """
        通过查询参数前缀别名匹配表对象.
    Args:
        name: 表别名
        model:  sqlalchemy.Model

    Returns:

    """
    name_split = name.split('.')
    if len(name_split) > 2:
        raise FilterInvalid(msg=f'过滤列名不合法: {name}')
    elif len(name_split) == 2:
        if isinstance(model, (Alias, Annotated, Subquery)):
            model_alias = model.name
        else:
            model_alias = None
        alias, column = name_split
        if alias == model_alias:  # noqa
            # 过滤参数别名与model别名匹配
            return column
        else:
            # 不匹配
            return None
    else:
        # 非别名过滤
        return name


def parse_model_attribute(
        name: str,
        model: t.Union[TableType,
                       Model]) -> t.Union[Column, InstrumentedAttribute]:
    """
    根据 model,name获取模型的字段对象.

    Args:
        model: sqlalchemy.Model
        name: 字段名
    Returns:
         attr: 字段名对应的Column实例对象
    """
    if isinstance(model, (Alias, Table, Annotated, Subquery)):
        attr = getattr(model.columns, name, None)
    else:
        attr = getattr(model, name, None)
    return attr


def parse_query_related_models(query: LesoonQuery) -> t.List[TableType]:
    """获取Query对象查询涉及的所有表"""
    related_models: t.List[TableType] = list()

    # 递归查找涉及表实体
    # 注意: 未包含子查询以及with语句涉及的表情况

    def recur_related_models(_froms: t.List[t.Any],
                             _related_models: t.List[TableType]):
        for _from in _froms:
            if isinstance(_from, (Table, Alias, Subquery)):
                # 表实体
                _related_models.append(_from)
                if hasattr(_from, 'element') and isinstance(
                        _from.element, (Subquery, Select)):
                    recur_related_models([_from.element], _related_models)
            elif isinstance(_from, _ORMJoin):
                # join实体
                recur_related_models([_from.left, _from.right], _related_models)
            elif isinstance(_from, Subquery):
                # 子查询
                recur_related_models([_from.element], _related_models)
            elif isinstance(_from, Select):
                recur_related_models(_from.froms, _related_models)
            else:
                raise TypeError(f'type:{_from} = {type(_from)}')

    recur_related_models(_froms=query.statement.froms,
                         _related_models=related_models)
    return related_models
