import typing as t

import marshmallow as ma
import pytest
from lesoon_common import LesoonFlask
from lesoon_common.code import ResponseCode
from lesoon_common.test import ft
from lesoon_common.wrappers import LesoonTestClient

from lesoon_restful.api import Api
from lesoon_restful.dbengine.memory import MemoryService
from lesoon_restful.resource import ModelResource


class FooSchema(ma.Schema):
    id = ma.fields.Int()
    name = ma.fields.Str()
    age = ma.fields.Int()
    slug = ma.fields.Str()


class FooResource(ModelResource):

    class Meta:
        name = 'foo'
        service = MemoryService
        schema = FooSchema


class FooFactory(ft.Factory):
    id = ft.Sequence(lambda n: n + 1)
    name = ft.Faker('word')
    age = ft.Faker('pyint', max_value=100)
    slug = ft.Faker('word')


class TestModelResource:

    @pytest.fixture(autouse=True)
    def setup_method(self, app: LesoonFlask, test_client: LesoonTestClient):
        api = Api(app)
        FooResource.api = None
        api.add_resource(FooResource)

    def test_resource_schema(self, test_client: LesoonTestClient):
        response = test_client.get('/foo/schema')
        assert response.status_code == 200
        assert response.json == {
            'title':
                FooResource.meta.get('title'),
            'description':
                FooResource.meta.get('description'),
            'name':
                FooResource.meta.get('name'),
            'resource':
                FooResource.__name__,
            'schema':
                FooResource.schema.__class__.__name__,
            'fields': {
                name: field.__class__.__name__
                for name, field in FooResource.schema.fields.items()
            },
            'links': [
                f'{route.method} : {route.rule_factory(FooResource)}'
                for route in FooResource.routes.values()
            ]
        }

    def test_resource_curd(self, app: LesoonFlask):
        test_client: LesoonTestClient = app.test_client()  # noqa

        url = FooResource.Meta.name
        assert FooResource.service.id_attribute == 'id'
        assert isinstance(FooResource.service.schema, FooSchema)

        f = ft.build(dict, FACTORY_CLASS=FooFactory)
        response = test_client.post(url, json=f)
        assert response.code == ResponseCode.Success.code

        response = test_client.get(url)
        assert response.result == [f]

        update_f = ft.build(dict, FACTORY_CLASS=FooFactory, id=f['id'])
        response = test_client.put(url, json=update_f)
        assert response.code == ResponseCode.Success.code
        assert response.result == update_f

        response = test_client.delete(url, json=[f['id']])
        assert response.code == ResponseCode.Success.code

        response = test_client.get(url)
        assert response.result is None
