import typing as t
from functools import wraps

import pytest
from flask import Blueprint
from lesoon_common import LesoonFlask
from lesoon_common.wrappers import LesoonTestClient

from lesoon_restful.api import Api
from lesoon_restful.resource import Resource
from lesoon_restful.route import Route


class FooResource(Resource):

    @Route.GET
    def foo(self):
        return 'foo'

    class Meta:
        name = 'foo'


class BarResource(Resource):

    @Route.GET
    def foo(self):
        return 'bar'

    class Meta:
        name = 'bar'


class TestApi:

    def setup_method(self):
        FooResource.api = None

    def test_add_resource(self, app: LesoonFlask,
                          test_client: LesoonTestClient):
        api = Api(app)
        api.add_resource(FooResource)
        response = test_client.get('/foo/foo')
        assert response.get_data(as_text=True) == 'foo'

    def test_prefix(self, app: LesoonFlask, test_client: LesoonTestClient):
        api = Api(app, prefix='/api/v1')
        api.add_resource(FooResource)
        response = test_client.get('/api/v1/foo/foo')
        assert response.get_data(as_text=True) == 'foo'

    def test_decorator(self, app: LesoonFlask, test_client: LesoonTestClient):

        def is_teapot(fn):

            @wraps(fn)
            def wrapper(*args, **kwargs):
                return '', 418, {}

            return wrapper

        api = Api(app, decorators=[is_teapot])

        api.add_resource(FooResource)

        response = test_client.get('/foo/foo')

        assert response.status_code == 418


class TestApiWithBlueprint:

    def setup_method(self):
        FooResource.api = None

    def test_api_blueprint(self, app: LesoonFlask,
                           test_client: LesoonTestClient):
        api_bp = Blueprint('lesoon-restful', __name__.split('.')[0])
        api = Api(api_bp)
        api.add_resource(FooResource)

        # Register Blueprint
        app.register_blueprint(api_bp)
        response = test_client.get('/foo/foo')
        assert response.get_data(as_text=True) == 'foo'

    def test_api_blueprint_with_prefix(self, app: LesoonFlask,
                                       test_client: LesoonTestClient):
        api_bp = Blueprint('lesoon-restful', __name__.split('.')[0])
        api = Api(api_bp, prefix='/api/v1')
        api.add_resource(FooResource)

        # Register Blueprint
        app.register_blueprint(api_bp)
        response = test_client.get('/api/v1/foo/foo')
        assert response.get_data(as_text=True) == 'foo'

    def test_api_blueprint_init_app(self, app: LesoonFlask,
                                    test_client: LesoonTestClient):
        api = Api()
        api.add_resource(FooResource)

        api_bp = Blueprint('lesoon-restful', __name__.split('.')[0])
        api.init_app(api_bp)

        # Register Blueprint
        app.register_blueprint(api_bp, url_prefix='/api/v1')
        response = test_client.get(f'/api/v1/foo/foo')

        assert response.get_data(as_text=True) == 'foo'

    def test_multiple_blueprints(self, app: LesoonFlask,
                                 test_client: LesoonTestClient):
        # Create Blueprints
        api_bp1 = Blueprint('lesoon-restful-1', __name__.split('.')[0])
        api_bp2 = Blueprint('lesoon-restful-2', __name__.split('.')[0])

        # Create Api objects, add resources, and register blueprints with app
        api1 = Api(api_bp1, prefix='/api/v1')
        api2 = Api(api_bp2, prefix='/api/v2')
        api1.add_resource(FooResource)

        with pytest.raises(RuntimeError):
            api2.add_resource(FooResource)

        api2.add_resource(BarResource)
        app.register_blueprint(api_bp1)
        app.register_blueprint(api_bp2)

        response = test_client.get(f'/api/v1/foo/foo')
        assert response.get_data(as_text=True) == 'foo'
        response = test_client.get(f'/api/v2/bar/foo')
        assert response.get_data(as_text=True) == 'bar'
