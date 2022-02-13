import typing as t

import marshmallow as ma
from lesoon_common.schema import CamelSchema
from lesoon_common.utils.str import camelcase
from webargs.core import Request
from webargs.flaskparser import FlaskParser


class LesoonParser(FlaskParser):
    __location_map__ = dict(
        list_json='load_list_json',
        **FlaskParser.__location_map__,
    )

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
            fields = schema.load_fields
            if len(fields) > 1:
                raise ma.ValidationError(message='list_json只允许定义一个字段')
            field = list(fields.values())[0]
            key = field.data_key or field.name
            new_data = {key: request.json}
            return self._makeproxy(new_data, schema)


class CamelParser(LesoonParser):
    DEFAULT_SCHEMA_CLASS = CamelSchema


parser = LesoonParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs

camel_parser = CamelParser()
ca_use_args = camel_parser.use_args
ca_use_kwargs = camel_parser.use_kwargs
