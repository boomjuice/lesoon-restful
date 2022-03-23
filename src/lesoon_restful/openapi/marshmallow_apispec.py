import typing as t

from apispec.ext.marshmallow import openapi
from apispec.utils import OpenAPIVersion
from flasgger.utils import merge_specs
from lesoon_common.globals import current_app
from marshmallow import Schema

from lesoon_restful.openapi.utils import is_openapi3

DEFAULT_OPENAPI_VERSION = '2.0'

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


def is_schema_type(v: t.Any):
    return isinstance(v, Schema) or (isinstance(v, type) and
                                     issubclass(v, Schema))


def convert_schemas(d, definitions=None):
    """
       Convert Marshmallow schemas to dict definitions
       Also updates the optional definitions argument with any definitions
       entries contained within the schema.
       """
    check_openapi_version()

    if definitions is None:
        definitions = {}
    definitions.update(d.get('definitions', {}))

    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = convert_schemas(v, definitions)
        if isinstance(v, (list, tuple)):
            new_v = []
            for item in v:
                if isinstance(item, dict):
                    new_v.append(convert_schemas(item, definitions))
                else:
                    new_v.append(item)
            v = new_v

        if k == 'parameters' and isinstance(v, list):
            new_v = []
            for s in v:
                if is_schema_type(s):
                    new_v.append(_schema2parameters(s, s.swag_in)[0])
                else:
                    new_v.append(s)
            v = new_v
        if is_schema_type(v):
            if isinstance(v, Schema):
                schema_name = v.__class__.__name__
            else:
                schema_name = v.__name__
                v = v()
            definitions[schema_name] = schema2jsonschema(v)
            ref = {
                '$ref': (f'#/components/schemas/{schema_name}'
                         if is_openapi3(openapi_converter.openapi_version) else
                         f'#/definitions/{schema_name}')
            }
            new[k] = ref
        else:
            new[k] = v

    # This key is not permitted anywhere except the very top level.
    if 'definitions' in new:
        del new['definitions']

    return new


def _schema2parameters(schema: Schema, location: str):
    """
    注入schema相关字段定义.
    Args:
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
    return spec
