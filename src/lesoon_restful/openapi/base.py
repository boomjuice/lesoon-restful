import re
import typing as t
from collections import defaultdict

from flasgger import Flasgger
from flasgger.constants import OPTIONAL_FIELDS
from flasgger.constants import OPTIONAL_OAS3_FIELDS
from flasgger.utils import extract_definitions
from flasgger.utils import get_vendor_extension_fields
from flasgger.utils import parse_definition_docstring
from marshmallow import Schema

from lesoon_restful.openapi.marshmallow_apispec import schema2jsonschema
from lesoon_restful.openapi.utils import extract_schema
from lesoon_restful.openapi.utils import get_specs
from lesoon_restful.openapi.utils import is_openapi3

DEFAULT_SWAGGER_RESPONSES = {
    '200': {
        'description': 'OK'
    },
    '401': {
        'description': 'Unauthorized'
    },
    '403': {
        'description': 'Forbidden'
    },
    '404': {
        'description': 'Not Found'
    },
    '405': {
        'description': 'Method Not Allow'
    }
}


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
        self.template: t.Dict[str, t.Any] = {}
        self.schemas: t.Dict[str, Schema] = {}
        if schemas:
            for schema in schemas:
                self.schemas[schema.__name__] = schema2jsonschema(schema())

    def init_app(self, app, decorators=None):
        self.template = self.template or self.DEFAULT_TEMPLATE
        super().init_app(app, decorators=decorators)

    def get_apispecs(self, endpoint='apispec_1'):
        if not self.app.debug and endpoint in self.apispecs:
            return self.apispecs[endpoint]

        spec = None
        for _spec in self.config['specs']:
            if _spec['endpoint'] == endpoint:
                spec = _spec
                break
        if not spec:
            raise RuntimeError(f'Can`t find specs by endpoint {endpoint:d},'
                               'check your flasgger`s config')

        data = {
            # try to get from config['SWAGGER']['info']
            # then config['SWAGGER']['specs'][x]
            # then config['SWAGGER']
            # then default
            'info':
                self.config.get('info') or {
                    'version':
                        spec.get('version', self.config.get('version',
                                                            '0.0.1')),
                    'title':
                        spec.get('title',
                                 self.config.get('title', 'A swagger API')),
                    'description':
                        spec.get(
                            'description',
                            self.config.get('description',
                                            'powered by Flasgger')),
                    'termsOfService':
                        spec.get('termsOfService',
                                 self.config.get('termsOfService', '/tos')),
                },
            'paths':
                self.config.get('paths') or defaultdict(dict),
            'definitions':
                self.config.get('definitions') or defaultdict(dict)
        }

        openapi_version = self.config.get('openapi')
        if openapi_version:
            data['openapi'] = openapi_version
        else:
            data['swagger'] = self.config.get('swagger') or self.config.get(
                'swagger_version', '2.0')

        # Support extension properties in the top level config
        top_level_extension_options = get_vendor_extension_fields(self.config)
        if top_level_extension_options:
            data.update(top_level_extension_options)

        # if True schemaa ids will be prefized by function_method_{id}
        # for backwards compatibility with <= 0.5.14
        prefix_ids = self.config.get('prefix_ids')

        if self.config.get('host'):
            data['host'] = self.config.get('host')
        if self.config.get('basePath'):
            data['basePath'] = self.config.get('basePath')
        if self.config.get('schemes'):
            data['schemes'] = self.config.get('schemes')
        if self.config.get('securityDefinitions'):
            data['securityDefinitions'] = self.config.get('securityDefinitions')

        if is_openapi3(openapi_version):
            # enable oas3 fields when openapi_version is 3.*.*
            data['components'] = {'schemas': self.schemas}
            del data['definitions']
            optional_oas3_fields = self.config.get(
                'optional_oas3_fields') or OPTIONAL_OAS3_FIELDS
            for key in optional_oas3_fields:
                if self.config.get(key):
                    data[key] = self.config.get(key)
        else:
            data['definitions'] = self.schemas

        # set defaults from template
        if self.template is not None:
            data.update(self.template)

        paths = data['paths']
        definitions = extract_schema(data)
        ignore_verbs = set(self.config.get('ignore_verbs', ('HEAD', 'OPTIONS')))

        # technically only responses is non-optional
        optional_fields = self.config.get('optional_fields') or OPTIONAL_FIELDS

        for name, def_model in self.get_def_models(
                spec.get('definition_filter')).items():
            description, swag = parse_definition_docstring(
                def_model, self.sanitizer)
            if name and swag:
                if description:
                    swag.update({'description': description})
                definitions[name].update(swag)

        specs = get_specs(self.get_url_mappings(spec.get('rule_filter')),
                          ignore_verbs,
                          optional_fields,
                          self.sanitizer,
                          openapi_version=openapi_version,
                          doc_dir=self.config.get('doc_dir'))

        http_methods = ['get', 'post', 'put', 'delete']
        for rule, verbs in specs:
            operations = dict()
            for verb, swag in verbs:
                update_dict = swag.get('definitions', {})
                if type(update_dict) == list and type(update_dict[0]) == dict:
                    # pop, assert single element
                    update_dict, = update_dict
                definitions.update(update_dict)
                defs = []  # swag.get('definitions', [])
                defs += extract_definitions(defs,
                                            endpoint=rule.endpoint,
                                            verb=verb,
                                            prefix_ids=prefix_ids)

                params = swag.get('parameters', [])
                if verb in swag.keys():
                    verb_swag = swag.get(verb)
                    if len(params) == 0 and verb.lower() in http_methods:
                        params = verb_swag.get('parameters', [])

                defs += extract_definitions(params,
                                            endpoint=rule.endpoint,
                                            verb=verb,
                                            prefix_ids=prefix_ids)

                request_body = swag.get('requestBody')
                if request_body:
                    content = request_body.get('content', {})
                    extract_definitions(list(content.values()),
                                        endpoint=rule.endpoint,
                                        verb=verb,
                                        prefix_ids=prefix_ids)

                callbacks = swag.get('callbacks', {})
                if callbacks:
                    callbacks = {
                        str(key): value for key, value in callbacks.items()
                    }
                    extract_definitions(list(callbacks.values()),
                                        endpoint=rule.endpoint,
                                        verb=verb,
                                        prefix_ids=prefix_ids)

                responses = {}
                if 'responses' in swag:
                    responses = swag.get('responses', {})
                    # OAS3
                    new_responses = {}
                    for key, value in responses.items():
                        if is_openapi3(openapi_version) and 'schema' in value:
                            value['content'] = {
                                '*/*': {
                                    'schema': value['schema']
                                }
                            }
                            del value['schema']
                        new_responses[str(key)] = value
                    responses = new_responses

                    if responses is not None:
                        defs = defs + extract_definitions(
                            responses.values(),
                            endpoint=rule.endpoint,
                            verb=verb,
                            prefix_ids=prefix_ids)
                    for definition in defs:
                        if 'id' not in definition:
                            definitions.update(definition)
                            continue
                        def_id = definition.pop('id')
                        if def_id is not None:
                            definitions[def_id].update(definition)

                operation = {}
                if swag.get('summary'):
                    operation['summary'] = swag.get('summary')
                if swag.get('description'):
                    operation['description'] = swag.get('description')
                if request_body:
                    operation['requestBody'] = request_body
                if callbacks:
                    operation['callbacks'] = callbacks

                operation['responses'] = dict(DEFAULT_SWAGGER_RESPONSES,
                                              **responses)
                # parameters - swagger ui dislikes empty parameter lists
                if len(params) > 0:
                    operation['parameters'] = params
                # other optionals
                for key in optional_fields:
                    if key in swag:
                        value = swag.get(key)
                        if key in ('produces', 'consumes'):
                            if not isinstance(value, (list, tuple)):
                                value = [value]

                        operation[key] = value
                operations[verb] = operation

            if len(operations):
                try:
                    # Add reverse proxy prefix to route
                    prefix = self.template['swaggerUiPrefix']
                except (KeyError, TypeError):
                    prefix = ''
                swag_rule = f'{prefix}{rule}'

                try:
                    # handle basePath
                    base_path: str = self.template.get('basePath', '')

                    if base_path:
                        if base_path.endswith('/'):
                            base_path = base_path[:-1]
                        if base_path:
                            # suppress base_path from swag_rule if needed.
                            # Otherwise, we will get definitions twice...
                            if swag_rule.startswith(base_path):
                                swag_rule = swag_rule[len(base_path):]
                except (KeyError, TypeError):
                    pass

                # old regex '(<(.*?\:)?(.*?)>)'
                for arg in re.findall('(<([^<>]*:)?([^<>]*)>)', swag_rule):
                    swag_rule = swag_rule.replace(arg[0], '{%s}' % arg[2])

                for key, val in operations.items():
                    if swag_rule not in paths:
                        paths[swag_rule] = {}
                    if key in paths[swag_rule]:
                        paths[swag_rule][key].update(val)
                    else:
                        paths[swag_rule][key] = val
        self.apispecs[endpoint] = data
        return data
