import inspect
import json
import typing as t

import marshmallow as ma
from lesoon_common.globals import request
from lesoon_common.response import success_response
from lesoon_common.schema import ListOrNotSchema
from webargs import fields

from lesoon_restful.parser import use_args
from lesoon_restful.route import ItemRoute
from lesoon_restful.route import Route
from lesoon_restful.utils.common import AttributeDict

if t.TYPE_CHECKING:
    from lesoon_restful.api import Api
    from lesoon_restful.service import Service


class ResourceMeta(type):

    def __new__(mcs, name: str, bases: t.Tuple[t.Type, ...], members: dict):
        class_ = super().__new__(mcs, name, bases, members)
        class_.routes = routes = dict(  # type:ignore
            getattr(class_, 'routes') or {})

        class_.meta = meta = AttributeDict(  # type:ignore
            getattr(class_, 'meta') or {})

        def append_route(routes_: t.Dict[str, Route], route: Route, name_: str):
            if route.attribute is None:
                route.attribute = name_

            for r in route._related_routes:  # noqa
                if r.attribute is None:
                    r.attribute = name_
                routes_[r.relation] = r

            routes_[route.relation] = route

        for base in bases:
            # 继承父类路由规则
            for mem_name, member in inspect.getmembers(
                    base, lambda m: isinstance(m, Route)):
                append_route(routes, member, mem_name)

            if hasattr(base, 'meta'):
                meta.update(base.meta)

        # 添加当前类路由规则
        for mem_name, member in members.items():
            if isinstance(member, Route):
                append_route(routes, member, mem_name)

        # 更新meta
        if 'Meta' in members:
            changes = members['Meta'].__dict__
            for k, v in changes.items():
                if not k.startswith('__'):
                    meta[k] = v

            if not changes.get('name', None):
                meta['name'] = name
        else:
            meta['name'] = name

        if meta.exclude_routes:
            for relation in meta.exclude_routes:
                routes.pop(relation, None)

        return class_


class Resource(metaclass=ResourceMeta):
    api: 'Api' = None
    meta: AttributeDict = None
    routes: t.Dict[str, Route] = None
    route_prefix: str = None

    class Meta:
        name: str = None
        title: str = None
        description: str = None
        exclude_routes: t.Tuple[str, ...] = ()
        route_decorators: t.Dict[str, t.Union[t.Callable,
                                              t.List[t.Callable]]] = {}


class ModelResourceMeta(ResourceMeta):

    def __new__(mcs, name, bases, members):
        class_ = super().__new__(mcs, name, bases, members)
        meta = class_.meta

        if meta.service:
            for k, v in meta.service.meta.items():
                # service中的定义大于resource中的定义
                if v:
                    meta[k] = v
            class_.service = meta.service(meta, resource=class_)

        if meta.schema:
            class_.schema = meta.schema()

        return class_


class ModelResource(Resource, metaclass=ModelResourceMeta):
    service: 'Service' = None
    schema: ma.Schema = None

    @Route.GET('/schema', rel='schema', attribute='schema')
    def model_schema(self):
        schema = {
            'title':
                self.meta.get('title'),
            'description':
                self.meta.get('description'),
            'name':
                self.meta.get('name'),
            'resource':
                self.__class__.__name__,
            'schema':
                self.schema.__class__.__name__,
            'fields': {
                name: field.__class__.__name__
                for name, field in self.schema.fields.items()
            },
            'links': [
                f'{route.method} : {route.rule_factory(self)}'
                for route in self.routes.values()
            ]
        }

        return json.dumps(schema)

    @Route.GET('', rel='instances')
    def instances(self):
        pagination = self.service.paginated_instances()
        results = self.schema.dump(pagination.items, many=True)
        return success_response(result=results, total=pagination.total)

    @ItemRoute.GET('', rel='instance')
    def read(self, item: object):
        return success_response(self.schema.dump(item))

    @Route.POST('', rel='create_entrance')
    @use_args(ListOrNotSchema(unknown=ma.INCLUDE), location='json')
    def create(self, properties: t.Union[dict, t.List[dict]]):
        item = self.service.create(properties)
        return success_response(result=self.schema.dump(item), msg='新建成功')

    @ItemRoute.POST('', rel='create_instance')
    @use_args(ma.Schema(unknown=ma.INCLUDE), location='json')
    def create_instance(self, item: object):
        item = self.service._create_one(item=item)
        return success_response(result=self.schema.dump(item), msg='新建成功')

    @Route.PUT('', rel='update_entrance')
    @use_args(ListOrNotSchema(unknown=ma.INCLUDE), location='json')
    def update(self, properties: t.Union[dict, t.List[dict]]):
        item = self.service.update(properties)
        return success_response(self.schema.dump(item), msg='更新成功')

    @ItemRoute.PUT('', rel='update_instance')
    @use_args(ma.Schema(unknown=ma.INCLUDE), location='json')
    def update_instance(self, item: object, properties: dict):
        item = self.service._update_one(item, properties)
        return success_response(result=self.schema.dump(item), msg='更新成功')

    @Route.DELETE('', rel='delete_entrance')
    @use_args({'ids': fields.DelimitedList(fields.Raw())},
              as_kwargs=True,
              location='query')
    @use_args({'ids': fields.List(fields.Raw())},
              as_kwargs=True,
              location='list_json')
    def delete(self, ids: t.List[str]):
        self.service.delete(ids)
        return success_response(msg='删除成功')

    @ItemRoute.DELETE('', rel='delete_instance')
    def delete_instance(self, item):
        id_ = getattr(item, self.service.id_attribute)
        self.service._delete_one(id_)
        return success_response(msg='删除成功')

    class Meta:
        id_attribute: str = 'id'
        id_converter: str = 'int'
        schema: t.Type[ma.Schema] = None
        model: t.Any = None
        filters: t.Union[bool, dict] = True
        sortable: bool = True
        service: t.Type['Service'] = None
