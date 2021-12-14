import typing as t

from lesoon_common.wrappers import LesoonRequest
from marshmallow import fields as ma_fields
from werkzeug.utils import cached_property

from lesoon_restful.exceptions import ItemNotFound
from lesoon_restful.exceptions import RequestMustBeJSON
from lesoon_restful.exceptions import RestfulException
from lesoon_restful.filters import BaseFilter
from lesoon_restful.filters import Condition
from lesoon_restful.filters import convert_filters
from lesoon_restful.filters import FILTER_NAMES
from lesoon_restful.filters import FILTERS_BY_TYPE
from lesoon_restful.filters import filters_for_fields
from lesoon_restful.resource import ModelResource
from lesoon_restful.utils.common import AttributeDict
from lesoon_restful.utils.common import convert_dict
from lesoon_restful.utils.common import ManagerProxy


class Manager:
    """
    数据控制层.

    Attributes:
        resource: 资源类
        model: 数据模型 e.g: `Sqlalchemy.Model`, `MongoEngine.Document`,...

    """
    FILTER_NAMES = FILTER_NAMES
    FILTERS_BY_TYPE = FILTERS_BY_TYPE

    def __init__(self, resource: t.Type[ModelResource], model: t.Any):
        self.resource = resource
        self.filters: t.Dict[str, dict] = {}

        resource.manager = self
        if hasattr(model, 'manager') and isinstance(model.manager,
                                                    ManagerProxy):
            model.manager.manager = self

        self._init_model(resource, model, resource.meta)
        self._init_filters(resource, resource.meta)

    def _init_model(self, resource: t.Type[ModelResource], model: t.Any,
                    meta: AttributeDict):
        self.model = model
        self.id_attribute = meta.id_attribute

    def _init_filter(self, filter_class: t.Type[BaseFilter], name: str,
                     field: ma_fields.Field, attribute: str):
        # 此时初始化的过滤器实例中的column = None
        return filter_class(name, field=field, attribute=attribute)

    def _init_filters(self, resource: t.Type[ModelResource],
                      meta: AttributeDict):
        fields = resource.schema.fields

        # e.g：field_filters = {"name":{ "eq":EqualFilter, "ne":NotEqualFilter }}
        field_filters = filters_for_fields(resource.schema.dump_fields,
                                           meta.filters,
                                           filter_names=self.FILTER_NAMES,
                                           filters_by_type=self.FILTERS_BY_TYPE)
        self.filters = {
            field_name: {
                name: self._init_filter(filter_cls, name, fields[field_name],
                                        field_name)
                for name, filter_cls in field_filters.items()
            } for field_name, field_filters in field_filters.items()
        }

    @cached_property
    def _sort_fields(self):
        return {
            name: field
            for name, field in self.resource.schema.dump_fields.items()
            if name in self.filters and self._is_sortable_field(field)
        }

    def _convert_filters(self, where: t.Dict[str, str]):
        """
        解析过滤条件.
        e.g: where = {"id": 1}
                     {"id": {"$gt": 1} }
        Args:
            where: 过滤字典

        Returns:

        """
        for name, value in where.items():
            yield convert_filters(value, self.filters[name])

    def _convert_sort(self, sort: t.Dict[str, bool]):
        """
        解析排序条件.
        e.g： sort = {"id":true,"name":false}
        Args:
            sort: 排序字典

        """
        for name, reverse in sort.items():
            field = self._sort_fields[name]
            yield field, field.attribute or name, reverse

    def parse_request(self, request: LesoonRequest) -> t.Dict[str, t.Any]:
        """
        解析请求中的分页参数.
        目前包括： page - 页号
                  per_page - 页大小
                  where - 过滤条件
                  sort -排序条件

        """
        where_dict = convert_dict(request.args.get('where'))
        sort_dict = convert_dict(request.args.get('sort'))

        where = tuple(self._convert_filters(where_dict))
        sort = tuple(self._convert_sort(sort_dict))
        return {
            'page': request.page,
            'per_page': request.page_size,
            'where': where,
            'sort': sort
        }

    def _is_sortable_field(self, field: ma_fields.Field):
        return isinstance(
            field, (ma_fields.String, ma_fields.Boolean, ma_fields.Number,
                    ma_fields.Integer, ma_fields.Float, ma_fields.Decimal,
                    ma_fields.Date, ma_fields.DateTime))

    def deserialize_instance(self,
                             items: t.Union[t.List[object], object],
                             many: bool = False):
        """
        反序列化数据模型实例.
        因为对象不可作为返回结果,需要作反序列化
        Args:
            items: 对象或对象列表
            many: 是否列表

        """
        pass

    def paginated_instances(self,
                            page: int,
                            per_page: int,
                            where: t.Tuple[Condition, ...] = None,
                            sort: t.Tuple[ma_fields.Field, str, bool] = None):
        """
        分页查询数据模型实例.

        Args:
            page: 页号
            per_page: 页大小
            where: 过滤条件
            sort: 排序条件

        Returns:
            Pagination()

        """
        pass

    def instances(
            self,
            where: t.Tuple[Condition, ...] = None,
            sort: t.Tuple[ma_fields.Field, str,
                          bool] = None) -> t.Sequence[object]:
        """
        获取数据模型实例.

        Args:
            where: 过滤条件
            sort: 排序条件

        :return:
            a list of :class:`self.meta.model` instance

        """
        pass

    def read(self, id: t.Any) -> object:
        """
        通过id获取单个数据模型实例.

        Args:
            id: 标识字段,通常为id

        """
        pass

    def first(self,
              where: t.Tuple[Condition, ...] = None,
              sort: t.Tuple[ma_fields.Field, str, bool] = None) -> object:
        """
        获取查询的第一个数据模型实例.

        Args:
            where: 过滤条件
            sort: 排序条件

        Raises:

        """
        try:
            return self.instances(where, sort)[0]
        except IndexError:
            raise ItemNotFound()

    def create(self, properties: dict, commit=True):
        """
        写入数据.

        Args:
            properties: 数据模型json
            commit: 是否提交

        Returns:
            写入的数据模型实例

        """
        pass

    def update(self, item: object, changes: dict, commit=True):
        """
        更新数据.

        Args:
            item: :class:`self.meta.model` instance
            changes: 更新的数据
            commit: 是否提交

        Returns:
            更新后的数据模型实例
        """
        pass

    def delete(self, item: object):
        """
        删除数据.

         Args:
            item: :class:`self.meta.model` instance

        """
        pass

    def delete_by_id(self, id):
        """
        根据id删除数据.

        Args:
            id: 标识字段,通常为id

        """
        return self.delete(self.read(id))

    def commit(self):
        pass

    def begin(self):
        pass


class QueryManager(Manager):

    def _or_expression(self, expressions: list):
        """ or条件合并."""
        raise NotImplementedError()

    def _and_expression(self, expressions: list):
        """ and条件合并."""
        raise NotImplementedError()

    def _query(self):
        """ query查询对象."""
        raise NotImplementedError()

    def _query_filter(self, query, expression: t.Any):
        """ query注入过滤条件."""
        raise NotImplementedError()

    def _query_order_by(self, query, sort=None):
        """ query注入排序条件."""
        raise NotImplementedError()

    def _query_get_first(self, query):
        raise NotImplementedError()

    def _query_filter_by_id(self, query, id):
        raise NotImplementedError()

    def _query_get_paginated_items(self, query, page, per_page):
        """ query分页获取."""
        raise NotImplementedError()

    def deserialize_instance(self, items, many: bool = False):
        return self.resource.schema.dump(items, many=many)

    def paginated_instances(self, page, per_page, where=None, sort=None):
        instances = self.instances(where=where, sort=sort)
        return self._query_get_paginated_items(instances, page, per_page)

    def instances(self, where=None, sort=None):
        query = self._query()

        if query is None:
            return []

        if where:
            expressions = [condition() for condition in where]
            query = self._query_filter(query, self._and_expression(expressions))

        return self._query_order_by(query, sort)

    def first(self, where=None, sort=None):
        res = self._query_get_first(self.instances(where, sort))
        if res is None:
            raise ItemNotFound('记录不存在')
        else:
            return res

    def read(self, id):
        query = self._query()

        if query is None:
            raise RestfulException('无法获取query对象')
        res = self._query_filter_by_id(query, id)
        if not res:
            raise ItemNotFound('记录不存在')
        return res

    @property
    def query(self):
        return self._query()
