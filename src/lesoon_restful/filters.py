import typing as t
from datetime import datetime

import marshmallow as ma

from lesoon_restful import exceptions


class BaseFilter:
    """
    通用过滤基类
    Attributes：
        name: 过滤简称 e.g:'eq','gte','lte'...
        field: a :class:`marshmallow.fields.Field` instance
        attribute: 属性名字 e.g: 'id_','title',...
        column: 操作对象

    """

    def __init__(self,
                 name: str,
                 field: ma.fields.Field,
                 attribute: str,
                 column: t.Any = None):
        self.name = name
        self.field = field
        self.attribute = attribute

        # 某些类型无法直接转换成bool类型判断
        if column is not None:
            self.column = column
        else:
            self.column = attribute

    def convert(self, value: t.Union[dict, str]):
        if self.name is not None and isinstance(value, dict):
            value = value[f'${self.name}']
            # 存在匹配则序列化值
            if isinstance(value, list):
                value = [
                    self.field.deserialize(v, self.attribute, None)
                    for v in value
                ]
            else:
                value = self.field.deserialize(value, self.attribute, None)

        return Condition(self, value, self.column)

    def op(self, column: t.Any, value: t.Any):
        raise NotImplementedError()


class EqualFilter(BaseFilter):

    def op(self, column, value):
        return column == value


class NotEqualFilter(BaseFilter):

    def op(self, column, value):
        return column != value


class LessThanFilter(BaseFilter):

    def op(self, column, value):
        return column < value


class GreaterThanFilter(BaseFilter):

    def op(self, column, value):
        return column > value


class LessThanEqualFilter(BaseFilter):

    def op(self, column, value):
        return column <= value


class GreaterThanEqualFilter(BaseFilter):

    def op(self, column, value):
        return column >= value


class InFilter(BaseFilter):

    def op(self, column, value):
        return column in value


class ContainsFilter(BaseFilter):

    def op(self, column, value):
        return hasattr(column, '__iter__') and value in column


class StringContainsFilter(BaseFilter):

    def op(self, column, value):
        return column and value in column


class StringIContainsFilter(BaseFilter):

    def op(self, column, value):
        return column and value.lower() in column.lower()


class StartsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.startswith(value)


class IStartsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.lower().startswith(value.lower())


class EndsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.endswith(value)


class IEndsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.lower().endswith(value.lower())


class DateBetweenFilter(BaseFilter):

    def op(self, column, value):
        before, after = value
        return before <= column <= after


# 通用过滤器集合
CommonFilters = (EqualFilter, NotEqualFilter, InFilter)
# 数字过滤器集合
NumberFilters = (LessThanFilter, LessThanEqualFilter, GreaterThanFilter,
                 GreaterThanEqualFilter)
# 字符串过滤器集合
StringFilters = (StringContainsFilter, StringIContainsFilter, StartsWithFilter,
                 IStartsWithFilter, EndsWithFilter, IEndsWithFilter)
# 时间类过滤器集合
DateTypeFilters = (DateBetweenFilter,)

FN_TYPE = t.Tuple[t.Type[BaseFilter], str]
FBF_TYPE = t.Any

# 过滤简称映射
FILTER_NAMES = (
    (EqualFilter, None),
    (EqualFilter, 'eq'),
    (NotEqualFilter, 'ne'),
    (LessThanFilter, 'lt'),
    (LessThanEqualFilter, 'lte'),
    (GreaterThanFilter, 'gt'),
    (GreaterThanEqualFilter, 'gte'),
    (InFilter, 'in'),
    (ContainsFilter, 'contains'),
    (StringContainsFilter, 'contains'),
    (StringIContainsFilter, 'icontains'),
    (StartsWithFilter, 'startswith'),
    (IStartsWithFilter, 'istartswith'),
    (EndsWithFilter, 'endswith'),
    (IEndsWithFilter, 'iendswith'),
    (DateBetweenFilter, 'between'),
)

# 字段类型与过滤器集合映射
FILTERS_BY_FIELD = (
    (ma.fields.Boolean, CommonFilters),
    (ma.fields.Number, CommonFilters + NumberFilters),
    (ma.fields.Integer, CommonFilters + NumberFilters),
    (ma.fields.Float, CommonFilters + NumberFilters),
    (ma.fields.Decimal, CommonFilters + NumberFilters),
    (ma.fields.String, CommonFilters + StringFilters),
    (ma.fields.Date, CommonFilters + NumberFilters + DateTypeFilters),
    (ma.fields.DateTime, CommonFilters + NumberFilters + DateTypeFilters),
    (ma.fields.List, ContainsFilter),
)


class Condition:

    def __init__(self, filter: BaseFilter, value: t.Any, column: t.Any = None):
        self.filter = filter
        self.value = value
        self.column = column

    def __call__(self, column: t.Any = None):
        column = column or self.column
        return self.filter.op(column, self.value)


def _get_names_for_filter(
        filter_cls: t.Type[BaseFilter],
        filter_names: t.Tuple[FN_TYPE, ...]) -> t.Iterator[str]:
    """
    通过过滤类获取过滤名.
    Args:
        filter_cls: 过滤器类
        filter_names: 见上方定义 `FILTER_NAMES`

    Returns:
        见上方定义 `FILTER_NAMES`
    """
    for fc, name in filter_names:
        if fc == filter_cls:
            yield name


def filters_for_field_class(
        field_class: t.Type[ma.fields.Field],
        filters_by_field: t.Tuple[FBF_TYPE, ...]) -> t.Set[t.Type[BaseFilter]]:
    """
    从最合适的基类中查找过滤器.
    Args:
        field_class: 字段Field类型
        filters_by_field: 见上方定义 `FILTERS_BY_FIELD`

    Returns:
        Filter集合
        e.g: {`EqualFilter`,`NotEqualFilter`,...}
    """
    field_class_filters: t.Set[t.Type[BaseFilter]] = set()
    filters_by_field = dict(filters_by_field)
    for cls in {field_class, *field_class.__bases__}:
        if cls in filters_by_field:
            field_class_filters.update(filters_by_field[cls])
    return field_class_filters


def filters_for_field(field_cls: t.Type[ma.fields.Field],
                      filter_names: t.Tuple[FN_TYPE, ...] = FILTER_NAMES,
                      filters_by_field: t.Tuple[FBF_TYPE,
                                                ...] = FILTERS_BY_FIELD):
    """
    根据schema字段的类型生成匹配的Filter类.
    Args:
        field_cls: 字段Field类型

    Returns:
        field_filters :{'eq':EqualFilter,...}
        filter_names: 见上方定义 `FILTER_NAMES`
        filters_by_field: 见上方定义 `FILTERS_BY_FIELD`

    """
    field_filters = {
        name: filter
        for filter in filters_for_field_class(field_cls, filters_by_field)
        for name in _get_names_for_filter(filter, filter_names)
    }

    return field_filters


def filters_for_fields(fields: dict,
                       filters_expression: t.Union[bool, dict],
                       filter_names: t.Tuple[FN_TYPE, ...] = FILTER_NAMES,
                       filters_by_field: t.Tuple[FBF_TYPE,
                                                 ...] = FILTERS_BY_FIELD):
    """
    For example, the following allows all filters:
    ::
        filters_expression = True

    The following allows filtering on the ``"name"`` field:
    ::
        filters_expression = {
            "name": True
        }

    The following allows filtering by equals and not equals on the ``"name"`` field:
    ::
        filters_expression = {
            "name": ['eq', 'ne']
        }

    In addition it is also possible to specify custom filters this way:
    ::

        filters_expression = {
            "name": {
                'text': MyTextFilter
            },
            "*": True
        }
    Args:
        fields: 字段列表 {"name":fields.Str(),...}
        filters_expression: 过滤器表达式
        filter_names: 见上方定义 `FILTER_NAMES`
        filters_by_field: 见上方定义 `FILTERS_BY_FIELD`

    Returns:
            filters = {
                "name":{
                    "eq":EqualFilter,
                    "ne":NotEqualFilter
                }
            }

    """
    filters = {}

    for field_name, field in fields.items():
        field_filters = filters_for_field(field_cls=field.__class__,
                                          filter_names=filter_names,
                                          filters_by_field=filters_by_field)

        if isinstance(filters_expression, dict):
            try:
                field_expression = filters_expression[field_name]
            except KeyError:
                try:
                    field_expression = filters_expression['*']
                except KeyError:
                    continue

            if isinstance(field_expression, dict):
                field_filters = field_expression
            elif isinstance(field_expression, (list, tuple)):
                # e.g: field_expression = ["eq","ne",...]
                field_filters = {
                    name: filter
                    for name, filter in field_filters.items()
                    if name in field_expression
                }
            elif field_expression is not True:
                continue
        elif filters_expression is not True:
            continue

        if field_filters:
            filters[field_name] = field_filters

    return filters


def legitimize_where(where: t.Dict[str, t.Any]):
    """
    将查询参数转换成标准过滤条件.
    Args:
        where: {'a__eq':1}

    Returns:
        new_where: {'a':{'$eq': 1}}
    """
    new_where = {}
    for name, value in list(where.items()):
        if '__' in name:
            column, condition = name.split('__', 1)
            new_where[column] = {f'${condition}': value}
        else:
            new_where[name] = value
    return new_where


def convert_filters(
        value: t.Any, field_filters: t.Dict[t.Optional[str],
                                            BaseFilter]) -> Condition:
    """
    匹配过滤器，调用过滤器转变值函数.

    Args:
        value: 过滤值  1,{'$eq':1}, ...
        field_filters:  字段过滤器 {'eq':EqualFilter,...}

    """
    _f = field_filters[None]
    if isinstance(value, dict):
        if len(value) != 1:
            raise exceptions.FilterInvalid(
                msg=
                f'字段 <{_f.field.__class__.__name__}:{_f.attribute}> 过滤值不合法:{value}'
            )
        filter_name = next(iter(value))

        # search for filters in the format {"$filter": condition}
        # like {"$eq": 111}
        if len(filter_name) > 1 and filter_name.startswith('$'):
            filter_name = filter_name[1:]

            for filter_ in field_filters.values():
                if filter_name == filter_.name:
                    return filter_.convert(value)
            else:
                raise exceptions.FilterNotAllow(
                    msg=
                    f'字段 <{_f.field.__class__.__name__}:{_f.attribute}> 不支持{filter_name}过滤'
                )
    return _f.convert(value)
