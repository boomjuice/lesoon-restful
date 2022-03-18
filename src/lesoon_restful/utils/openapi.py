import importlib
import typing as t
from functools import wraps

from apispec.ext.marshmallow import openapi
from apispec.utils import OpenAPIVersion
from flasgger import Flasgger
from flasgger.utils import merge_specs
from lesoon_common.globals import current_app
from marshmallow import Schema

if t.TYPE_CHECKING:
    from lesoon_restful.resource import Resource

DEFAULT_OPENAPI_VERSION = '3.0'

DEFUALT_SWAGGER_RESPONSES = {
    200: {
        'description': 'OK'
    },
    401: {
        'description': 'Unauthorized'
    },
    403: {
        'description': 'Forbidden'
    },
    404: {
        'description': 'Not Found'
    },
    405: {
        'description': 'Method Not Allow'
    }
}

openapi_converter = openapi.OpenAPIConverter(
    openapi_version=DEFAULT_OPENAPI_VERSION,
    schema_name_resolver=lambda schema: None,
    spec=None)
schema2jsonschema = openapi_converter.schema2jsonschema
schema2parameters = openapi_converter.schema2parameters
field2parameter = openapi_converter._field2parameter


def check_openapi_version():
    if (not current_app or not hasattr(current_app, 'swag') or
            getattr(openapi_converter, 'configured', False)):
        return
    openapi_converter.openapi_version = OpenAPIVersion(
        current_app.swag.config.get(  # type: ignore
            'openapi', DEFAULT_OPENAPI_VERSION))
    openapi_converter.configured = True


class Swagger(Flasgger):
    DEFAULT_TEMPLATE = {
        'securityDefinitions': {
            'JWT': {
                'type': 'apiKey',
                'name': 'token',
                'in': 'header'
            }
        },
        'security': [{
            'JWT': []
        }]
    }

    def __init__(self, *args, schemas: t.List[t.Type[Schema]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        if schemas:
            definitions = {}
            for schema in schemas:
                definitions[schema.__name__] = schema2jsonschema(schema())
            self.config['definitions'] = definitions

    def init_app(self, app, decorators=None):
        self.template = self.template or self.DEFAULT_TEMPLATE
        super().init_app(app, decorators=decorators)


def schema2parameters_to_specs(specs: dict, schema: Schema, location: str):
    """
    注入schema相关字段定义.
    Args:
        specs: openapi定义字典
        schema: a marshmallow schema instance
        location: 参数位置. e.q: query,header,cookie,body,...

    """
    if location == 'list_json':
        spec = [
            field2parameter(
                field_obj,
                name=field_obj.data_key or field_name,
                location='body',
            ) for field_name, field_obj in schema.fields.items()
        ]
    else:
        spec = schema2parameters(schema=schema, location=location)
    if not isinstance(spec, list):
        spec = [spec]
    parameters = {'parameters': spec, 'responses': DEFUALT_SWAGGER_RESPONSES}
    merge_specs(specs, parameters)


def resource_to_specs(specs: dict, resource: t.Type['Resource']):
    """
    注入resource相关信息.
    Args:
        specs: openapi定义字典
        resource: Resource资源类

    """
    tmp = {
        'tags': [resource.__name__],
        'produces': 'application/json',
        'security': [{
            'JWT': []
        }],
    }
    merge_specs(specs, tmp)


def cover_swag(parameters: list = None,
               tags: list = None,
               definitions: dict = None,
               responses: dict = None,
               schemas: list = None,
               security: list = None,
               summary: str = '',
               description: str = ''):
    """
    swagger定义
    Args:
        parameters: 入参定义
        tags: 标签定义
        definitions: 模型定义
        responses: 返回体定义
        schemas: schemas定义
        security: 安全定义
        summary: 功能概括定义
        description: 功能详细定义

    """
    attrs = {
        'parameters': parameters or [],
        'tags': tags or [],
        'definitions': definitions or {},
        'responses': responses or {},
        'schemas': schemas or [],
        'security': security or [],
        'summary': summary,
        'description': description
    }

    def decorator(fn):
        if not hasattr(fn, 'specs_dict'):
            fn.specs_dict = {}
        merge_specs(fn.specs_dict, attrs)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator
