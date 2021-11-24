import inspect
import json
import typing as t
from collections import OrderedDict

from lesoon_common.globals import request
from lesoon_common.response import success_response
from marshmallow import INCLUDE
from marshmallow import Schema
from webargs.flaskparser import use_args

from lesoon_restful.routes import ItemRoute
from lesoon_restful.routes import Route
from lesoon_restful.utils.common import AttributeDict

if t.TYPE_CHECKING:
    from lesoon_restful.api import Api
    from lesoon_restful.manager import Manager


class ResourceMeta(type):

    def __new__(mcs, name: str, bases: t.Tuple[t.Type, ...], members: dict):
        class_ = super().__new__(mcs, name, bases, members)
        class_.routes = routes = dict(  # type:ignore
            getattr(class_, 'routes') or {})

        class_.meta = meta = AttributeDict(  # type:ignore
            getattr(class_, 'meta') or {})

        def append_route(routes: t.Dict[str, Route], route: Route, name: str):
            if route.attribute is None:
                route.attribute = name

            for r in route._related_routes:
                if r.attribute is None:
                    r.attribute = name
                routes[r.relation] = r

            routes[route.relation] = route

        for base in bases:
            # 继承父类路由规则
            for name, member in inspect.getmembers(
                    base, lambda m: isinstance(m, Route)):
                append_route(routes, member, name)

            if hasattr(base, 'Meta'):
                meta.update(base.Meta.__dict__)

        # 添加当前类路由规则
        for name, member in members.items():
            if isinstance(member, Route):
                append_route(routes, member, name)

        # 更新meta
        if 'Meta' in members:
            changes = members['Meta'].__dict__
            for k, v in changes.items():
                if not k.startswith('__'):
                    meta[k] = v

            if not changes.get('name', None):
                meta['name'] = name.lower()
        else:
            meta['name'] = name.lower()

        if schema := meta.get('schema', None):
            class_.schema = schema()  # type:ignore

        if meta.exclude_routes:
            for relation in meta.exclude_routes:
                routes.pop(relation, None)

        return class_


class Resource(metaclass=ResourceMeta):
    api: 'Api' = None
    meta: AttributeDict = None
    routes: t.Dict[str, Route] = None
    schema: Schema = None
    route_prefix: str = None
    representations: OrderedDict = None

    @Route.GET('/schema', rel='describedBy', attribute='schema')
    def described_by(self):
        fields = {
            name: field.__class__.__name__
            for name, field in self.schema.fields.items()
        }
        schema = OrderedDict({
            'title': self.meta.get('title'),
            'description': self.meta.get('description'),
            'name': self.meta.get('name'),
            'resource': self.__class__.__name__,
            'schema': self.schema.__class__.__name__,
            'fields': fields,
        })

        return json.dumps(schema), 200, {
            'Content-Type': 'application/schema+json'
        }

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

        if 'Meta' in members:
            meta = class_.meta
            changes = members['Meta'].__dict__

            if 'model' in changes or 'model' in meta and 'manager' in changes:
                if meta.manager is not None:
                    class_.manager = meta.manager(class_, meta.model)
        return class_


class ModelResource(Resource, metaclass=ModelResourceMeta):
    manager: 'Manager' = None

    @Route.GET('', rel='instances')
    def instances(self):
        page_params = self.manager.parse_request(request)
        res = self.manager.paginated_instances(**page_params)
        return success_response(result=self.manager.deserialize_instance(
            res.items, many=True),
                                total=res.total)

    @Route.POST('', rel='create')
    @use_args(Schema(unknown=INCLUDE), location='json')
    def create(self, properties):
        item = self.manager.create(properties)
        return success_response(self.manager.deserialize_instance(item))

    @ItemRoute.GET('', rel='instance')
    def read(self, item):
        return success_response(self.manager.deserialize_instance(item))

    @ItemRoute.PUT('', rel='update')
    @use_args(Schema(unknown=INCLUDE), location='json')
    def update_instance(self, item, properties):
        updated_item = self.manager.update(item, properties)
        return success_response(self.manager.deserialize_instance(updated_item))

    @ItemRoute.DELETE('', rel='delete')
    def delete_instance(self, item):
        self.manager.delete(item)
        return success_response()

    class Meta:
        id_attribute: str = 'id'
        id_converter: str = 'int'
        manager: 'Manager' = None
        filters: bool = True
        sortable: bool = True
