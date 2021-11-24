from flask_mongoengine import MongoEngine
from lesoon_common import LesoonFlask
from mongoengine import fields as mg_fields

from lesoon_restful import Api
from lesoon_restful import ModelResource
from lesoon_restful.contrib.mongoengine.manager import MongoEngineManager
from lesoon_restful.contrib.mongoengine.schema import MongoAutoSchema

app = LesoonFlask(__name__)
app.debug = True
app.config['MONGODB_SETTINGS'] = {
    'db': 'belledoc',
    'host': 'scm-mongo-dev.belle.net.cn',
    'port': 27077,
    'username': 'bldoc',
    'password': 'blf1#root',
    'authentication_source': 'admin',
}

me = MongoEngine(app)


class Book(me.Document):
    title = mg_fields.StringField(null=False, unique=True)
    year_published = mg_fields.IntField(null=True)
    rating = mg_fields.IntField(default=5)


class BookSchema(MongoAutoSchema):

    class Meta(MongoAutoSchema.Meta):
        model = Book


class BookResource(ModelResource):

    class Meta:
        model = Book
        schema = BookSchema
        id_converter = 'string'


api = Api(app, default_manager=MongoEngineManager)
api.add_resource(BookResource)

if __name__ == '__main__':
    import pprint

    pprint.pprint(sorted(app.url_map.iter_rules(), key=lambda x: x.rule))
    app.run()
