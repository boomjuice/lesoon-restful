import typing as t
from collections import OrderedDict
from functools import wraps

from flask import Blueprint
from flask import Flask
from flask import request
from werkzeug.wrappers import BaseResponse

from .resource import ModelResource
from .resource import Resource
from lesoon_restful.route import Route
from lesoon_restful.service import Service
from lesoon_restful.utils.req import unpack


class Api:
    """
    API用于注册路由，

    Attributes:
        app: a :class:`Flask` instance
        decorators: 装饰器列表
        prefix: API前缀
        default_service: 默认的service类, 未提供则为:class:`dbengine.alchemy.SQLAlchemyService`

    """

    def __init__(self,
                 app: t.Union[Flask, Blueprint] = None,
                 decorators: t.List[t.Callable] = None,
                 prefix: str = None,
                 default_service: t.Type[Service] = None):
        self.app = app
        self.blueprint = None
        self.prefix = prefix or ''
        self.decorators = decorators or []
        self.default_service = default_service

        self.resources: t.Dict[str, t.Type[Resource]] = {}
        self.views: t.List[tuple] = []

        if self.default_service is None:
            from lesoon_restful.dbengine.alchemy import SQLAlchemyService
            self.default_service = SQLAlchemyService

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # If app is a blueprint, defer the initialization
        try:
            app.record(self._deferred_blueprint_init)
        except AttributeError:
            # Flask.Blueprint has a 'record' attribute, Flask.Api does not
            self._init_app(app)
        else:
            self.blueprint = app

    def _deferred_blueprint_init(self, setup_state):
        self.prefix = ''.join((setup_state.url_prefix or '', self.prefix))

        for _resource in self.resources.values():
            _resource.route_prefix = '/'.join(
                (self.prefix, _resource.meta.name))

        self._init_app(setup_state.app)

    def _init_app(self, app: Flask):
        for route, resource, view_func, endpoint, methods in self.views:
            rule = route.rule_factory(resource)
            self._register_view(app, rule, route.skip_api_decorators, view_func,
                                endpoint, methods)

    def _register_view(self, app, rule: str, skip_decorators: bool,
                       view_func: t.Callable, endpoint: str,
                       methods: t.List[str]):
        """
        将视图函数与路由绑定

        Args:
            app: a :class:`Flask` instance
            skip_decorators: 是否忽略装饰器
            rule: 路由
            view_func: 视图函数
            endpoint: 端点
            methods: http方法

        """

        if self.blueprint:
            endpoint = f'{self.blueprint.name}.{endpoint}'

        view_func = self.output(view_func)

        if not skip_decorators:
            for decorator in self.decorators:
                view_func = decorator(view_func)

        app.add_url_rule(rule,
                         view_func=view_func,
                         endpoint=endpoint,
                         methods=methods)

    def output(self, view: t.Callable):

        @wraps(view)
        def wrapper(*args, **kwargs):
            resp = view(*args, **kwargs)

            if isinstance(resp, BaseResponse):
                return resp

            data, code, headers = unpack(resp)
            headers['Content-Type'] = 'application/json'
            return data, code, headers

        return wrapper

    def add_route(self,
                  route: Route,
                  resource: t.Type[Resource],
                  endpoint: str = None,
                  decorator: t.Callable = None):
        endpoint = endpoint or '_'.join((resource.meta.name, route.relation))
        methods = [route.method]
        rule = route.rule_factory(resource).replace('//', '/')

        view_func = route.view_factory(endpoint, resource)

        if decorator:
            view_func = decorator(view_func)

        if self.app and not self.blueprint:
            self._register_view(self.app, rule, route.skip_api_decorators,
                                view_func, endpoint, methods)
        else:
            self.views.append((route, resource, view_func, endpoint, methods))

    def add_resource(self, resource: t.Type[Resource]):
        """
        注册资源，添加资源中所有路由规则
        Args:
            resource: :class:`Resource`

        """
        if resource in self.resources.values():
            # 避免重复添加
            return

        if resource.api is not None and resource.api != self:
            raise RuntimeError(f'{resource}已绑定Api({resource.api}),无法绑定其他Api.')

        if issubclass(resource, ModelResource) and resource.service is None:
            if self.default_service:
                resource.service = self.default_service(resource.meta, resource)
            else:
                raise RuntimeError(
                    f'{resource.meta.name} 未设置service类, 并且默认service无法初始化. '
                    f'如果需要使用Sqlalchemy,请确保Flask-SQLAlchemy已安装.')

        resource.api = self
        resource.route_prefix = '/'.join((self.prefix, resource.meta.name))

        for route in resource.routes.values():
            route_decorator = resource.meta.route_decorators.get(
                route.relation, None)
            self.add_route(route, resource, decorator=route_decorator)

        self.resources[resource.meta.name] = resource
