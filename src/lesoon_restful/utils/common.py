import json
import typing as t
from urllib import parse

from lesoon_restful.exceptions import InvalidJSON


class AttributeDict(dict):
    __getattr__ = dict.__getitem__  # type:ignore
    __setattr__ = dict.__setitem__  # type:ignore


def convert_dict(param: str = None) -> t.Dict[str, t.Any]:
    if param:
        try:
            # 特殊字符转义处理
            where = parse.unquote(param)
            _where = json.loads(where)
            if not isinstance(_where, dict):
                return dict()
            else:
                return _where
        except (json.JSONDecodeError, TypeError):
            raise InvalidJSON(f'参数无法序列化 {param}')

    else:
        return dict()
