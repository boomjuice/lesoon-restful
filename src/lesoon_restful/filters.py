import typing as t

from marshmallow import fields as ma_fields


class BaseFilter:
    """
    通用过滤基类
    Attributes：
        name: 过滤简称 e.g:'eq','gte','lte'...
        field: a :class:`marshmallow.fields.Field` instance
        attribute: 属性名字 e.g: 'id','title',...
        column: 操作对象

    """

    def __init__(self,
                 name: str,
                 field: ma_fields.Field,
                 attribute: str,
                 column: t.Any = None):
        self.name = name
        self.field = field
        self.attribute = attribute
        self.column = column

    def convert(self, value: t.Union[dict, str]):
        if self.name is not None and isinstance(value, dict):
            # 存在匹配则序列化值
            value = self.field._serialize(value[f'${self.name}'],
                                          self.attribute, None)
        return Condition(self, value, self.attribute)

    def op(self, value: t.Any):
        raise NotImplementedError()


class EqualFilter(BaseFilter):

    def op(self, value):
        return self.column == value


class NotEqualFilter(BaseFilter):

    def op(self, value):
        return self.column != value


class LessThanFilter(BaseFilter):

    def op(self, value):
        return self.column < value


class GreaterThanFilter(BaseFilter):

    def op(self, value):
        return self.column > value


class LessThanEqualFilter(BaseFilter):

    def op(self, value):
        return self.column <= value


class GreaterThanEqualFilter(BaseFilter):

    def op(self, value):
        return self.column >= value


class InFilter(BaseFilter):

    def op(self, value):
        return self.column in value


class ContainsFilter(BaseFilter):

    def op(self, value):
        return hasattr(self.column, '__iter__') and value in self.column


class StringContainsFilter(BaseFilter):

    def op(self, value):
        return self.column and value in self.column


class StringIContainsFilter(BaseFilter):

    def op(self, value):
        return self.column and value.lower() in self.column.lower()


class StartsWithFilter(BaseFilter):

    def op(self, value):
        return self.column.startswith(value)


class IStartsWithFilter(BaseFilter):

    def op(self, value):
        return self.column.lower().startswith(value.lower())


class EndsWithFilter(BaseFilter):

    def op(self, value):
        return self.column.endswith(value)


class IEndsWithFilter(BaseFilter):

    def op(self, value):
        return self.column.lower().endswith(value.lower())


class DateBetweenFilter(BaseFilter):

    def op(self, value):
        before, after = value
        return before <= self.column <= after


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
FILTERS_BY_TYPE = (
    (ma_fields.Boolean, CommonFilters),
    (ma_fields.Number, CommonFilters + NumberFilters),
    (ma_fields.Integer, CommonFilters + NumberFilters),
    (ma_fields.Float, CommonFilters + NumberFilters),
    (ma_fields.Decimal, CommonFilters + NumberFilters),
    (ma_fields.String, CommonFilters + StringFilters),
    (ma_fields.Date, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.DateTime, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.List, (ContainsFilter,)),
)


class Condition:

    def __init__(self, filter: BaseFilter, value: t.Any, attribute: str):
        self.filter = filter
        self.value = value
        self.attribute = attribute

    @property
    def column(self):
        return self.filter.column

    @column.setter
    def column(self, column: t.Any):
        self.filter.column = column

    def __call__(self):
        return self.filter.op(self.value)


def _get_names_for_filter(filter_cls: t.Type[BaseFilter],
                          filter_names: t.Tuple[tuple]) -> t.Iterator[str]:
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
    field_class: ma_fields.Field,
    filters_by_type: t.Tuple[t.Tuple[ma_fields.Field, tuple]]
) -> t.Tuple[t.Type[BaseFilter], ...]:
    """
    从最合适的基类中查找过滤器.
    Args:
        field_class: 字段类
        filters_by_type: 见上方定义 `FILTERS_BY_TYPE`

    Returns:
        字段元组
        e.g: (`Float`,`Number`)
    """
    field_class_filters: t.List[t.Type[BaseFilter]] = []
    filters_by_type: t.Dict[ma_fields.Field, tuple] = dict(filters_by_type)
    for cls in (field_class,) + field_class.__bases__:  # type:ignore
        if cls in filters_by_type:
            field_class_filters.extend(filters_by_type[cls])
    return tuple(field_class_filters)


def filters_for_fields(fields: dict,
                       filters_expression: t.Union[bool, dict],
                       filter_names=FILTER_NAMES,
                       filters_by_type=FILTERS_BY_TYPE):
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
        fields: 字段列表 {"name":int,...}
        filters_expression: 过滤器表达式
        filter_names: 见上方定义 `FILTER_NAMES`
        filters_by_type: 见上方定义 `FILTERS_BY_TYPE`

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
        # e.g: {'eq':EqualFilter,...}
        field_filters = {
            name: filter for filter in filters_for_field_class(
                field.__class__, filters_by_type)
            for name in _get_names_for_filter(filter, filter_names)
        }

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


def convert_filters(
        value: t.Any, field_filters: t.Dict[t.Optional[str],
                                            BaseFilter]) -> Condition:
    """
    匹配过滤器，调用过滤器转变值函数.

    Args:
        value: 值
        field_filters:  字段过滤器

    """
    if isinstance(value, dict) and len(value) == 1:
        filter_name = next(iter(value))

        # search for filters in the format {"$filter": condition}
        # like {"$eq": 111}
        if len(filter_name) > 1 and filter_name.startswith('$'):
            filter_name = filter_name[1:]

            for filter_ in field_filters.values():
                if filter_name == filter_.name:
                    return filter_.convert(value)

    filter_ = field_filters[None]
    return filter_.convert(value)
