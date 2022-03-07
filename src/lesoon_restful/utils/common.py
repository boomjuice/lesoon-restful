import json
import typing as t
from urllib import parse

from lesoon_restful.exceptions import InvalidJSON
from lesoon_restful.filters import legitimize_sort
from lesoon_restful.filters import legitimize_where


class AttributeDict(dict):

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


def convert_dict(param: str = None,
                 silent: bool = False) -> t.Union[str, t.Dict[str, t.Any]]:
    if param:
        try:
            # 特殊字符转义处理
            param = parse.unquote_plus(param)
            _param = json.loads(param)
            if not isinstance(_param, dict):
                return {}
            else:
                return _param
        except (json.JSONDecodeError, TypeError, Exception):
            if silent:
                return param
            raise InvalidJSON(msg=f'参数无法序列化 {param}')
    else:
        return dict()


def convert_where(param: str = None) -> t.Dict[str, t.Any]:
    where = convert_dict(param)
    return legitimize_where(where)  # type:ignore


def convert_sort(param: str = None) -> t.Dict[str, bool]:
    sort = convert_dict(param, silent=True)
    return legitimize_sort(sort)
