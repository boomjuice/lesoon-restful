from lesoon_common.base import LesoonFlask
from lesoon_common.extensions import db
from lesoon_common.model.alchemy import fields
from marshmallow.schema import Schema
from marshmallow_sqlalchemy.schema import SQLAlchemyAutoSchema

from lesoon_restful import Api
from lesoon_restful import ModelResource
from lesoon_restful import use_args
from lesoon_restful import web_fields as wf
from lesoon_restful.dbengine import SQLAlchemyService
from lesoon_restful.route import Route

app = LesoonFlask(__name__)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, null=True)
    title = db.Column(db.String(), nullable=False)
    year_published = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=5)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    country = db.Column(db.String)


class BookSchema(SQLAlchemyAutoSchema):

    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Book
        load_instance = True


class AuthorSchema(SQLAlchemyAutoSchema):
    name = fields.String(data_key='author_name')
    country = fields.String(data_key='author_country')

    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Author
        load_instance = True


class BookService(SQLAlchemyService):

    class Meta:
        model = Book
        schema = BookSchema


class AuthorService(SQLAlchemyService):
    book_service = BookService()

    class Meta:
        model = Author
        schema = AuthorSchema

    def write_off(self, ids: list):
        self.book_service.query.filter(Book.author_id.in_(ids)).delete()
        self.delete_many(ids=ids, commit=False)
        self.commit()


class BookResource(ModelResource):
    service: BookService

    class Meta:
        name = 'book'
        service = BookService


class AuthorResource(ModelResource):
    service: AuthorService

    class Meta:
        name = 'author'
        service = AuthorService

    @Route.POST('/writeOff')
    @use_args({'ids': fields.List(fields.Int())},
              as_kwargs=True,
              location='list_json')
    def write_off(self, ids: list):
        self.service.write_off(ids)
        return 'success'


api = Api(app)
api.add_resource(BookResource)
api.add_resource(AuthorResource)

if __name__ == '__main__':
    import pprint

    pprint.pprint(sorted(app.url_map.iter_rules(), key=lambda x: x.rule))
    app.before_first_request_funcs.append(db.create_all)
    app.run()
