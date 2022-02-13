from lesoon_common.base import LesoonFlask
from lesoon_common.extensions import db
from marshmallow_sqlalchemy.schema import SQLAlchemyAutoSchema

from lesoon_restful import Api
from lesoon_restful import ModelResource
from lesoon_restful.route import ItemRoute

app = LesoonFlask(__name__)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    year_published = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=5)


class BookSchema(SQLAlchemyAutoSchema):

    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Book
        load_instance = True
        sqla_session = db.session


class BookResource(ModelResource):

    class Meta:
        model = Book
        schema = BookSchema

    @ItemRoute.GET('/rating')
    def rating(self, book):
        return book.rating


api = Api(app)
api.add_resource(BookResource)

if __name__ == '__main__':
    import pprint

    pprint.pprint(sorted(app.url_map.iter_rules(), key=lambda x: x.rule))
    app.before_first_request_funcs.append(db.create_all)
    app.run()
