# type:ignore
class DefaultConfig:
    # flask
    SECRET_KEY = ('\x00\x8c\xfd\xed\x963\xac.\xcfl\xea\x80e'
                  '\xc7\xbbB\xde\xef-\xd3\xeb6\xf3\xa4')
    PROPAGATE_EXCEPTIONS = True

    # sqlalchemy
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = None

    # jwt
    JWT_HEADER_NAME = 'token'
    JWT_HEADER_TYPE = None  # type:ignore
    JWT_SECRET_KEY = None
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60

    # cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 60

    # debug-toolbar
    DEBUG_TB_PROFILER_ENABLED = False

    # tracing
    TRACING_TYPE = 'jaeger'
    TRACING_ENABLED = True
    TRACING_JAEGER_CONFIG = {'SERVICE_NAME': 'lesoon-integration'}


class Config(DefaultConfig):
    # sqlalchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'

    # mongo
    MONGODB_SETTINGS = {
        'db': 'belledoc',
        'host': 'scm-mongo-dev.belle.net.cn',
        'port': 27077,
        'username': 'bldoc',
        'password': 'blf1#root',
        'authentication_source': 'admin',
    }
