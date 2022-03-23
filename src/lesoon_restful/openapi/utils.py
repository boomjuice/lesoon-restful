import os
import typing as t
from collections import defaultdict
from copy import deepcopy
from functools import wraps

from flasgger.utils import has_valid_dispatch_view_docs
from flasgger.utils import is_valid_method_view
from flasgger.utils import merge_specs
from flasgger.utils import parse_docstring
from lesoon_common import current_app

if t.TYPE_CHECKING:
    from lesoon_restful.resource import Resource


def get_specs(rules,
              ignore_verbs,
              optional_fields,
              sanitizer,
              openapi_version,
              doc_dir=None):
    specs = []
    for rule in rules:
        endpoint = current_app.view_functions[rule.endpoint]
        methods = dict()
        is_mv = is_valid_method_view(endpoint)

        for verb in rule.methods.difference(ignore_verbs):
            if not is_mv and has_valid_dispatch_view_docs(endpoint):
                endpoint.methods = endpoint.methods or ['GET']
                if verb in endpoint.methods:
                    methods[verb.lower()] = endpoint
            elif getattr(endpoint, 'methods', None) is not None:
                if isinstance(endpoint.methods, set):
                    if verb in endpoint.methods:
                        verb = verb.lower()
                        methods[verb] = getattr(endpoint.view_class, verb)
                else:
                    raise TypeError
            else:
                methods[verb.lower()] = endpoint

        verbs = []
        for verb, method in methods.items():

            klass = method.__dict__.get('view_class', None)
            if not is_mv and klass and hasattr(klass, 'verb'):
                method = getattr(klass, 'verb', None)
            elif klass and hasattr(klass, 'dispatch_request'):
                method = getattr(klass, 'dispatch_request', None)
            if method is None:  # for MethodView
                method = getattr(klass, verb, None)

            if method is None:
                if is_mv:  # #76 Empty MethodViews
                    continue
                raise RuntimeError(f'Cannot detect view_func for rule {rule}')

            swag = {}
            swag_def = {}

            swagged = False

            if getattr(method, 'specs_dict', None):
                from lesoon_restful.openapi.marshmallow_apispec import convert_schemas
                definition = {}
                merge_specs(
                    swag,
                    convert_schemas(deepcopy(method.specs_dict), definition))
                swag_def = definition
                swagged = True

            view_class = getattr(endpoint, 'view_class', None)

            if doc_dir:
                if view_class:
                    file_path = os.path.join(doc_dir, endpoint.__name__,
                                             method.__name__ + '.yml')
                else:
                    file_path = os.path.join(doc_dir,
                                             endpoint.__name__ + '.yml')
                if os.path.isfile(file_path):
                    func = method.__func__ \
                        if hasattr(method, '__func__') else method
                    setattr(func, 'swag_type', 'yml')
                    setattr(func, 'swag_path', file_path)

            doc_summary, doc_description, doc_swag = parse_docstring(
                method, sanitizer, endpoint=rule.endpoint, verb=verb)

            if is_openapi3(openapi_version):
                swag.setdefault('components', {})['schemas'] = swag_def
            else:  # openapi2
                swag['definitions'] = swag_def

            if doc_swag:
                merge_specs(swag, doc_swag)
                swagged = True

            if swagged:
                if doc_summary:
                    swag['summary'] = doc_summary

                if doc_description:
                    swag['description'] = doc_description

                verbs.append((verb, swag))

        if verbs:
            specs.append((rule, verbs))

    return specs


def is_openapi3(openapi_version):
    """
    Returns True if openapi_version is 3
    """
    return openapi_version and str(openapi_version).split('.')[0] == '3'


def extract_schema(spec: dict) -> defaultdict:
    """
    Returns schema resources according to openapi version
    """
    openapi_version = spec.get('openapi', None)
    if is_openapi3(openapi_version):
        return spec.get('components', {}).get('schemas', defaultdict(dict))
    else:  # openapi2
        return spec.get('definitions', defaultdict(dict))


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
