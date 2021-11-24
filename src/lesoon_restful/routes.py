import typing as t
from functools import wraps
from types import MethodType

from lesoon_common.utils.str import camelcase
from werkzeug.utils import cached_property

if t.TYPE_CHECKING:
    from lesoon_restful.resource import ModelResource

HTTP_METHODS = ('GET', 'PUT', 'POST', 'DELETE')


def _route_decorator(method: str):
    # 类路由方法设置
    def decorator(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return cls(method, args[0])
        else:
            return lambda f: cls(method, f, *args, **kwargs)

    decorator.__name__ = method
    return classmethod(decorator)


def _method_decorator(method: str):
    # 实例路由方法设置
    def wrapper(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return self._for_method(method, args[0], **kwargs)
        else:
            return lambda f: self._for_method(method, f, *args, **kwargs)

    wrapper.__name__ = method
    return wrapper


class Route:
    """
    路由类.

    Attributes:
        method: 请求方法(GET,POST,PUT,DELETE)
        view_func: 请求处理函数
        rule: 路由路径
        attribute: 属性
        rel: 路由描述

    """
    HTTP_METHOD_VERB_DEFAULTS = {
        'GET': 'read',
        'POST': 'create',
        'PUT': 'update',
        'DELETE': 'delete'
    }

    GET = _route_decorator('GET')
    POST = _route_decorator('POST')
    PUT = _route_decorator('PUT')
    DELETE = _route_decorator('DELETE')

    def __init__(self,
                 method: str = None,
                 view_func: t.Callable = None,
                 rule: t.Union[str, t.Callable] = None,
                 attribute: str = None,
                 rel: str = None,
                 **kwargs):
        self.rel = rel
        self.rule = rule
        self.method = method
        self.attribute = attribute

        self.view_func = view_func

        self._related_routes: t.Tuple['Route', ...] = ()

        for http_method in HTTP_METHODS:
            setattr(self, method,
                    MethodType(_method_decorator(http_method), self))

    @cached_property
    def relation(self):
        if self.rel:
            return self.rel
        else:
            verb = self.HTTP_METHOD_VERB_DEFAULTS.get(self.method,
                                                      self.method.lower())
            return camelcase(f'{verb}_{self.attribute}')

    def __get__(self, obj, owner):
        if obj is None:
            return self
        return lambda *args, **kwargs: self.view_func(obj, *args, **kwargs)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.rule)})'

    def _for_method(self,
                    method: str,
                    view_func: t.Callable,
                    rel: str = None,
                    **kwargs):
        attribute = kwargs.pop('attribute', self.attribute)

        instance = self.__class__(method,
                                  view_func,
                                  rule=self.rule,
                                  rel=rel,
                                  attribute=attribute,
                                  **kwargs)

        instance._related_routes = self._related_routes + (self,)
        return instance

    def rule_factory(self,
                     resource: t.Type['ModelResource'],
                     relative: bool = False):
        """
        路由规则工厂.

        Args:
            resource: 资源类
            relative: 是否根据`resource.route_prefix`生成相对路由

        """

        if self.rule is None:
            rule = camelcase(self.attribute)
        elif callable(self.rule):
            rule = self.rule(resource)
        else:
            rule = self.rule

        if relative or resource.route_prefix is None:
            return rule

        return '/'.join((resource.route_prefix, rule))

    def view_factory(self, name: str, resource: t.Type['ModelResource']):
        """
        视图函数工厂.
        注：因为`Flask`本身不支持类方法的路由,此处需要套一层装饰器

        Args:
            name: 请求出路函数名
            resource: 资源类

        """

        def make_func(fn):

            @wraps(fn)
            def decorator(*args, **kwargs):
                return fn(resource(), *args, **kwargs)

            return decorator

        view = make_func(self.view_func)
        view.__module__ = resource.__module__
        view.__doc__ = resource.__doc__
        view.__resource__ = resource

        return view


class ItemRoute(Route):
    """
    实例路由类.
    该类装饰过的函数, 会根据`resource.meta.id_attribute`查询数据模型实体,
    将其填充至args[0]中, 具体细节见下方:method:`view_factory`.

    """

    def rule_factory(self,
                     resource: t.Type['ModelResource'],
                     relative: bool = False):
        id_matcher = f'<{resource.meta.id_converter}:id>'

        if self.rule is None:
            rule = camelcase(self.attribute)
        elif callable(self.rule):
            rule = self.rule(resource)
        else:
            rule = self.rule

        if relative or resource.route_prefix is None:
            return rule

        return '/'.join((resource.route_prefix, id_matcher, rule))

    def view_factory(self, name: str, resource: t.Type['ModelResource']):
        original_view = super().view_factory(name, resource)

        def view(*args, **kwargs):
            id = kwargs.pop(resource.meta.id_attribute)
            item = resource.manager.read(id)
            return original_view(item, *args, **kwargs)

        view.__resource__ = getattr(  # type:ignore
            original_view, '__resource__')
        return view
