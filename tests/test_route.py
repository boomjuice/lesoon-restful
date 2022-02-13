import typing as t
from functools import wraps
from unittest import mock

import pytest
from lesoon_common import LesoonFlask
from lesoon_common import request
from lesoon_common.wrappers import LesoonTestClient
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import Unauthorized

from lesoon_restful.api import Api
from lesoon_restful.dbengine.memory import MemoryService
from lesoon_restful.resource import ModelResource
from lesoon_restful.resource import Resource
from lesoon_restful.route import ItemRoute
from lesoon_restful.route import Route


class FooResource(ModelResource):

    class Meta:
        name = 'foo'
        service = MemoryService


class TestRoute:

    def test_route(self, app: LesoonFlask, test_client: LesoonTestClient):
        route = Route.GET(rule='/test', rel='test')(lambda resource: {
            'resource': resource.meta.name
        })

        view = route.view_factory('', FooResource)

        assert getattr(view, '__resource__') == FooResource
        with app.test_request_context('/foo/test'):
            assert view() == {'resource': 'foo'}

    def test_item_route(self, app: LesoonFlask, test_client: LesoonTestClient):
        route = ItemRoute.GET('', rel='test')(lambda resource, item: {
            'resource': resource.meta.name,
            'item': item
        })

        view = route.view_factory('', FooResource)
        assert getattr(view, '__resource__') == FooResource
        with mock.patch.object(FooResource, 'service') as mock_service:
            mock_service.read_or_raise = lambda id_: id_
            with app.test_request_context('/foo/1/'):
                assert view(id=1) == {'resource': 'foo', 'item': 1}


class TestRouteWithResource:

    def test_simple_route(self):

        class FooResource(Resource):

            @Route.GET()
            def foo(self):
                return True

            class Meta:
                name = 'foo'

        resource = FooResource()
        assert 'foo' in resource.routes
        assert resource.routes['foo'] == Route(attribute='foo', method='GET')

    def test_lambda_rule(self):

        class FooResource(Resource):

            @Route.GET(lambda r: f'/<{r.meta.id_converter}:id>', rel='self')
            def read(self, id):
                return {'id': id}

            class Meta:
                name = 'foo'
                id_converter = 'int'

        resource = FooResource()
        assert 'self' in resource.routes
        assert resource.routes['self'].rule_factory(FooResource) == '/<int:id>'

    def test_method_route(self):

        class FooResource(Resource):

            @Route.POST()
            def foo(self, value):
                pass

            @foo.GET()
            def bar(self):
                pass

            class Meta:
                name = 'foo'

        resource = FooResource()
        assert 'bar' in resource.routes
        assert resource.routes['bar'] == Route(attribute='bar', method='GET')

    def test_subclass_rewrite(self):

        class FooResource(Resource):

            @Route.GET('', rel='read')
            def read(self):
                return 'read-foo'

            @Route.POST(rel='create')
            def create(self):
                return 'foo'

            class Meta:
                name = 'foo'

        class BarResource(FooResource):

            @Route.POST('', rel='create')
            def rewrite(self):
                return 'bar'

            class Meta:
                name = 'bar'

        foo_resource = FooResource()
        assert foo_resource.routes == {
            'read': Route(attribute='read', rel='read', method='GET', rule=''),
            'create': Route(attribute='create', rel='create', method='POST')
        }

        bar_resource = BarResource()
        assert bar_resource.routes == {
            'read':
                Route(attribute='read', rel='read', method='GET', rule=''),
            'create':
                Route(attribute='rewrite', rel='create', method='POST', rule='')
        }

    def test_route_decorator(self, app: LesoonFlask,
                             test_client: LesoonTestClient):

        def unauthorized(fn):

            @wraps(fn)
            def wrapper(*args, **kwargs):
                raise Unauthorized()

            return wrapper

        def denormalize(fn):

            @wraps(fn)
            def wrapper(*args, **kwargs):
                return 'not ' + fn(*args, **kwargs)

            return wrapper

        class FooResource(Resource):

            @Route.GET
            def no_decorator(self):
                return 'normal'

            @Route.GET
            @denormalize
            def simple_decorator(self):
                return 'normal'

            @Route.GET
            @unauthorized
            def unauthorized_decorator(self):
                return 'normal'

            class Meta:
                name = 'foo'
                title = 'Foo bar'

        api = Api(app=app)
        api.add_resource(FooResource)

        response = test_client.get('/foo/noDecorator')
        assert response.get_data(as_text=True) == 'normal'

        response = test_client.get('/foo/simpleDecorator')
        assert response.get_data(as_text=True) == 'not normal'

        response = test_client.get('/foo/unauthorizedDecorator')
        assert response.status_code == Unauthorized.code

    def test_route_disabling(self, app: LesoonFlask,
                             test_client: LesoonTestClient):

        class FooResource(Resource):

            @Route.GET
            def foo(self):
                return 'foo'

            @Route.POST
            def baz(self):
                value = request.get_data(as_text=True)
                return f'baz: {value}'

            class Meta:
                name = 'foo'

        class BarResource(FooResource):

            class Meta:
                name = 'bar'
                exclude_routes = ('baz',)

        class BazResource(BarResource):

            class Meta:
                name = 'baz'
                exclude_routes = ('foo',)

        api = Api(app)
        api.add_resource(FooResource)
        api.add_resource(BarResource)
        api.add_resource(BazResource)

        assert FooResource.routes == {
            'foo': FooResource.foo,
            'baz': FooResource.baz
        }

        assert BarResource.routes == {
            'foo': FooResource.foo,
        }

        assert BazResource.routes == {'baz': FooResource.baz}

        response = test_client.get('/bar/foo')
        assert response.get_data(as_text=True) == 'foo'

        response = test_client.get('/bar/baz')
        assert response.status_code == NotFound.code

        response = test_client.get('/baz/foo')
        assert response.status_code == NotFound.code

        response = test_client.post('/baz/baz', data='xyz')
        assert response.get_data(as_text=True) == 'baz: xyz'
