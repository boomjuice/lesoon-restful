from lesoon_common.code.response import ResponseCode
from lesoon_common.exceptions import ServiceError


class RestfulException(ServiceError):
    pass


class ItemNotFound(RestfulException):
    code = ResponseCode.NotFoundError

    def __init__(self, code=None, msg='记录不存在'):
        super().__init__(code, msg)


class RequestMustBeJSON(RestfulException):
    code = ResponseCode.ReqError

    def __init__(self, code=None, msg='请求格式必须为json'):
        super().__init__(code, msg)


class InvalidParam(RestfulException):

    def __init__(self, code=None, msg='参数格式不合法'):
        super().__init__(code, msg)


class InvalidJSON(RestfulException):

    def __init__(self, code=None, msg='json格式不合法'):
        super().__init__(code, msg)


class FilterInvalid(RestfulException):
    pass


class FilterNotAllow(RestfulException):
    pass
