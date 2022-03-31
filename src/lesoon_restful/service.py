import typing as t

from lesoon_common import request as current_request
from lesoon_common.dataclass.req import PageParam
from lesoon_common.utils.str import udlcase
from lesoon_common.wrappers import LesoonRequest
from marshmallow import fields as ma_fields
from marshmallow import Schema
from werkzeug.utils import cached_property

from lesoon_restful.exceptions import ItemNotFound
from lesoon_restful.exceptions import RestfulException
from lesoon_restful.filters import BaseFilter
from lesoon_restful.filters import Condition
from lesoon_restful.filters import convert_filters
from lesoon_restful.filters import FILTER_NAMES
from lesoon_restful.filters import FILTERS_BY_FIELD
from lesoon_restful.filters import filters_for_fields
from lesoon_restful.filters import legitimize_sort
from lesoon_restful.filters import legitimize_where
from lesoon_restful.resource import ModelResource
from lesoon_restful.utils.base import AttributeDict

if t.TYPE_CHECKING:
    from lesoon_restful.filters import FN_TYPE
    from lesoon_restful.filters import FBF_TYPE


class ServiceMeta(type):

    def __new__(mcs, name: str, bases: t.Tuple[t.Type, ...], members: dict):
        class_ = super().__new__(mcs, name, bases, members)

        class_.meta = meta = AttributeDict(  # type:ignore
            getattr(class_, 'meta') or {})

        for base in bases:
            if hasattr(base, 'meta'):
                meta.update(base.meta)

        # 更新meta
        if 'Meta' in members:
            changes = dir(members['Meta'])
            for change in changes:
                if not change.startswith('__'):
                    meta[change] = getattr(members['Meta'], change)

        return class_


class Service(metaclass=ServiceMeta):
    """
    数据控制层.

    Attributes:
        meta: 元数据定义

    """
    meta: AttributeDict = None
    FILTER_NAMES: t.Tuple['FN_TYPE', ...] = FILTER_NAMES
    FILTERS_BY_FIELD: t.Tuple['FBF_TYPE', ...] = FILTERS_BY_FIELD

    class Meta:
        id_attribute: str = 'id'
        id_converter: str = 'int'
        schema: t.Type[Schema] = None
        model: t.Any = None
        filters: t.Union[bool, dict] = True
        sortable: bool = True

    def __init__(self,
                 meta: AttributeDict = None,
                 resource: t.Type[ModelResource] = None):
        self.meta = meta or self.__class__.meta
        self.schema = self.meta.schema() if self.meta.schema else None
        self.filters: t.Dict[str, dict] = {}

        self._init_model()
        self._init_filters()

        if resource:
            self.set_resource_name(resource=resource)

    def _init_model(self):
        """ 模型初始化"""
        self.model = self.meta.model
        self.id_attribute = self.meta.id_attribute

    def _init_filter(self, filter_class: t.Type[BaseFilter], name: str,
                     field: ma_fields.Field, attribute: str):
        # 此时初始化的过滤器实例中的column = None
        return filter_class(name, field=field, attribute=attribute)

    def _init_filters(self):
        """ 初始化过滤条件字典."""
        if self.schema:
            fields = self.schema.fields

            field_filters = filters_for_fields(
                self.schema.dump_fields,
                self.meta.filters,
                filter_names=self.FILTER_NAMES,
                filters_by_field=self.FILTERS_BY_FIELD)
            # e.g：field_filters = {"name":{ "eq":EqualFilter, "ne":NotEqualFilter }}
            self.filters = {
                field_name: {
                    name: self._init_filter(filter_cls, name,
                                            fields[field_name], field_name)
                    for name, filter_cls in field_filters.items()
                } for field_name, field_filters in field_filters.items()
            }

    @cached_property
    def _sort_fields(self):
        """ 初始化排序条件字典."""
        return {
            name: field
            for name, field in self.schema.dump_fields.items()
            if name in self.filters and self._is_sortable_field(field)
        }

    def _convert_filters(self, where: t.Dict[str, str]):
        """
        解析过滤条件.
        e.g: where = {"id_": 1}
                     {"id_": {"$gt": 1} }
        Args:
            where: 过滤字典

        Returns:

        """
        for name, value in where.items():
            yield convert_filters(value, self.filters[udlcase(name)])

    def _convert_sort(self, sort: t.Dict[str, bool]):
        """
        解析排序条件.
        e.g： sort = {"id_":true,"name":false}
        Args:
            sort: 排序字典

        """
        for name, reverse in sort.items():
            field = self._sort_fields[name]
            yield field, field.attribute or name, reverse

    def _is_sortable_field(self, field: ma_fields.Field):
        return isinstance(
            field, (ma_fields.String, ma_fields.Boolean, ma_fields.Number,
                    ma_fields.Integer, ma_fields.Float, ma_fields.Decimal,
                    ma_fields.Date, ma_fields.DateTime))

    def set_resource_name(self, resource: t.Type[ModelResource]):
        """ 反向设置资源名称 """
        pass

    def parse_request(self,
                      request: LesoonRequest = current_request) -> PageParam:
        """
        解析请求中的分页参数.
        目前包括： page - 页号
                  page_size - 页大小
                  where - 过滤条件
                  sort -排序条件

        """
        where_dict = legitimize_where(request.where)
        sort_dict = legitimize_sort(request.sort)

        where = tuple(self._convert_filters(where_dict))
        sort = tuple(self._convert_sort(sort_dict))
        return PageParam(page=request.page,
                         page_size=request.page_size,
                         if_page=request.if_page,
                         where=where,
                         sort=sort)

    def paginated_instances(self, page_param: PageParam = None):
        """
        分页查询数据模型实例.

        Args:
            page_param: 分页查询参数

        Returns:
            Pagination()

        """
        pass

    def instances(self,
                  where: t.Tuple[Condition, ...] = None,
                  sort: t.Tuple[ma_fields.Field, str, bool] = None):
        """
        获取数据模型实例.

        Args:
            where: 过滤条件
            sort: 排序条件

        :return:
            a list of :class:`self.meta.model` instance

        """
        pass

    def read_or_raise(self, id_: t.Any) -> t.Any:
        """
        通过id获取单个数据模型实例.
        不存在则抛异常
        Args:
            id_: 标识字段,通常为id

        """
        raise NotImplemented

    def read(self, id_: t.Any) -> t.Any:
        """
        通过id获取单个数据模型实例.
        Args:
            id_: 标识字段,通常为id

        """
        raise NotImplemented

    def first(self,
              where: t.Tuple[Condition, ...] = None,
              sort: t.Tuple[ma_fields.Field, str, bool] = None) -> t.Any:
        """
        获取查询的第一个数据模型实例.

        Args:
            where: 过滤条件
            sort: 排序条件

        Raises:

        """
        try:
            return self.instances(where, sort)[0]  # noqa
        except IndexError:
            raise ItemNotFound()

    def before_create(self, items: t.Union[t.Any, t.List[t.Any]]):
        pass

    def after_create(self, items: t.Union[t.Any, t.List[t.Any]]):
        pass

    def before_update(self, items: t.Union[t.Any, t.List[t.Any]],
                      changes: t.Union[dict, t.List[dict]]):
        pass

    def after_update(self, items: t.Union[t.Any, t.List[t.Any]],
                     changes: t.Union[dict, t.List[dict]]):
        pass

    def before_delete(self, ids: t.Union[int, t.List[int]]):
        pass

    def after_delete(self, ids: t.Union[int, t.List[int]]):
        pass

    def create(self, properties: t.Union[dict, t.List[dict]]):
        """
        新增入口.
        properties:
            `type: dict`  单条写入
            `type: list`  批量写入
        Args:
            properties: 数据模型json

        Returns:
            写入的数据模型实例

        """
        if isinstance(properties, dict):
            item = self.schema.load(properties)
            return self.create_one(item=item)
        else:
            items = self.schema.load(properties, many=True)
            return self.create_many(items=items)

    def create_one(self, item: t.Any):
        self.before_create(items=item)
        item = self._create_one(item)
        self.after_create(items=item)
        return item

    def create_many(self, items: t.List[t.Any]):
        self.before_create(items=items)
        items = self._create_many(items)
        self.after_create(items=items)
        return items

    def _create_one(self, item: t.Any):
        raise NotImplemented

    def _create_many(self, items: t.List[t.Any]):
        raise NotImplemented

    def update(self, properties: t.Union[dict, t.List[dict]]):
        """
        更新入口.

        properties:
            `type: dict`  单条更新
            `type: list`  批量更新
        Args:
            properties: 数据模型json

        Returns:
            更新后的数据模型实例
        """
        if isinstance(properties, dict):
            item = self.read_or_raise(properties.get(self.id_attribute))
            return self.update_one(item=item, changes=properties)
        else:
            items = [
                self.read_or_raise(p.get(self.id_attribute)) for p in properties
            ]
            return self.update_many(items=items, changes=properties)

    def update_one(self, item: t.Any, changes: dict):
        self.before_update(items=item, changes=changes)
        item = self._update_one(item, changes)
        self.after_update(items=item, changes=changes)
        return item

    def update_many(self, items: t.List[t.Any], changes: t.List[dict]):
        self.before_update(items=items, changes=changes)
        items = self._update_many(items, changes)
        self.after_update(items=items, changes=changes)
        return items

    def _update_one(self, item: t.Any, changes: dict):
        raise NotImplemented

    def _update_many(self, items: t.List[t.Any], changes: t.List[dict]):
        raise NotImplemented

    def delete(self, ids: t.Union[t.Any, t.List[t.Any]]):
        """
        删除入口
        Args:
            ids:
                `type: int`   单条删除
                `type: list`  批量删除

        """
        if not isinstance(ids, list):
            self.delete_one(ids)
        else:
            self.delete_many(ids)

    def delete_one(self, id_: t.Any):
        self.read_or_raise(id_)
        self.before_delete(ids=id_)
        self._delete_one(id_)
        self.after_delete(ids=id_)

    def delete_many(self, ids: t.List[t.Any]):
        self.before_delete(ids=ids)
        self._delete_many(ids)
        self.after_delete(ids=ids)

    def _delete_one(self, id_: t.Any):
        raise NotImplemented

    def _delete_many(self, ids: t.List[t.Any]):
        raise NotImplemented


class QueryService(Service):

    def _or_expression(self, expressions: list):
        """ or条件合并."""
        raise NotImplementedError()

    def _and_expression(self, expressions: list):
        """ and条件合并."""
        raise NotImplementedError()

    def _query(self):
        """ query查询对象."""
        raise NotImplementedError()

    def _page_query(self):
        return self._query()

    def _query_filter(self, query, expression: t.Any):
        """ query注入过滤条件."""
        raise NotImplementedError()

    def _query_filter_by_id(self, query, id_):
        raise NotImplementedError()

    def _query_order_by(self, query, sort):
        """ query注入排序条件."""
        raise NotImplementedError()

    def _query_get_first(self, query):
        raise NotImplementedError()

    def _query_get_paginated_items(self, query, page: int, page_size: int,
                                   if_page: bool):
        """ query分页获取."""
        raise NotImplementedError()

    def paginated_instances(self, page_param: PageParam = None):
        page_param = page_param or self.parse_request()
        instances = self.instances(where=page_param.where, sort=page_param.sort)
        return self._query_get_paginated_items(instances,
                                               page=page_param.page,
                                               page_size=page_param.page_size,
                                               if_page=page_param.if_page)

    def instances(self, query=None, where=None, sort=None):
        query = query or self._page_query()

        if where:
            expressions = [condition() for condition in where]
            query = self._query_filter(query, self._and_expression(expressions))

        if sort:
            query = self._query_order_by(query, sort)
        return query

    def first(self, where=None, sort=None):
        res = self._query_get_first(self.instances(where, sort))
        if res is None:
            raise ItemNotFound()
        else:
            return res

    def read_or_raise(self, id_):
        res = self.read(id_)
        if not res:
            raise ItemNotFound()
        return res

    def read(self, id_):
        query = self._query()

        if query is None:
            raise RestfulException(msg='无法获取query对象')
        res = self._query_filter_by_id(query, id_)
        return res

    @property
    def query(self):
        return self._query()
