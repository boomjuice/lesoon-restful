import functools
import typing as t

import marshmallow as ma
from lesoon_common.globals import current_app
from lesoon_common.schema import CamelSchema
from lesoon_common.utils.str import camelcase
from webargs.core import _UNKNOWN_DEFAULT_PARAM
from webargs.core import ArgMap
from webargs.core import Request
from webargs.core import ValidateArg
from webargs.flaskparser import FlaskParser

from lesoon_restful.utils.openapi import schema2parameters_to_specs


class WebArgParser(FlaskParser):
    __location_map__ = dict(
        list_json='load_list_json',
        **FlaskParser.__location_map__,
    )

    __openapi_location_map__ = dict(view_args='path',
                                    querystring='query',
                                    query='query',
                                    form='form',
                                    json='json',
                                    headers='headers',
                                    cookies='cookies',
                                    files='files')

    def use_args(
        self,
        argmap: ArgMap,
        req: t.Optional[Request] = None,
        *,
        location: t.Optional[str] = None,
        unknown: t.Optional[str] = _UNKNOWN_DEFAULT_PARAM,
        as_kwargs: bool = False,
        validate: ValidateArg = None,
        error_status_code: t.Optional[int] = None,
        error_headers: t.Optional[t.Mapping[str, str]] = None
    ) -> t.Callable[..., t.Callable]:
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': fields.Str()}, location="querystring")
            def greet(args):
                return 'Hello ' + args['name']

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param str location: Where on the request to load values.
        :param str unknown: A value to pass for ``unknown`` when calling the
            schema's ``load`` method.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.
        """
        location = location or self.location
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, t.Mapping):
            argmap = self.schema_class.from_dict(argmap)()

        def decorator(func):
            req_ = request_obj
            argmap_ = argmap
            # --- swagger ---
            func.specs_dict = getattr(func, 'specs_dict', {})
            if not isinstance(argmap_, t.Callable):
                # argmap为可调用函数时 无法注入swagger
                schema2parameters_to_specs(
                    specs=func.specs_dict,
                    schema=argmap_,
                    location=self.__openapi_location_map__.get(
                        location, location))

            # --- swagger ---
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                req_obj = req_

                if not req_obj:
                    req_obj = self.get_request_from_view_args(
                        func, args, kwargs)

                # NOTE: At this point, argmap may be a Schema, or a callable
                parsed_args = self.parse(
                    argmap_,
                    req=req_obj,
                    location=location,
                    unknown=unknown,
                    validate=validate,
                    error_status_code=error_status_code,
                    error_headers=error_headers,
                )
                args, kwargs = self._update_args_kwargs(args, kwargs,
                                                        parsed_args, as_kwargs)
                return func(*args, **kwargs)

            wrapper.__wrapped__ = func
            return wrapper

        return decorator

    def load_list_json(self, request: Request, schema: ma.Schema):
        """
        此方法用于读取请求体中为列表的情况.
        注意：schema定义的字段只允许为一个
        Args:
            request:
            schema:

        Returns:

        """
        if not request.get_json(silent=True):
            return {}
        else:
            fields = schema.fields
            if len(fields) > 1:
                raise ma.ValidationError(message='list_json只允许定义一个字段')
            field = list(fields.values())[0]
            key = field.data_key or field.name
            new_data = {key: request.json}
            return self._makeproxy(new_data, schema)


class CamelArgParser(WebArgParser):
    DEFAULT_SCHEMA_CLASS = CamelSchema


parser = WebArgParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs

camel_parser = CamelArgParser()
ca_use_args = camel_parser.use_args
ca_use_kwargs = camel_parser.use_kwargs
