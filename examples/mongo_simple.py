from lesoon_common import LesoonFlask
from lesoon_common.extensions import mg
from lesoon_common.model import MongoAutoSchema
from mongoengine import fields as mg_fields

from lesoon_restful import Api
from lesoon_restful import ModelResource
from lesoon_restful.dbengine.mongoengine.service import MongoEngineService

app = LesoonFlask(__name__)


class Book(mg.Document):
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


api = Api(app, default_service=MongoEngineService)
api.add_resource(BookResource)

if __name__ == '__main__':
    import pprint
    pprint.pprint(sorted(app.url_map.iter_rules(), key=lambda x: x.rule))
    app.run()
