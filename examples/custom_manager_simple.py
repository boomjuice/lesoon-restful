from flask_sqlalchemy import SQLAlchemy
from lesoon_common.base import LesoonFlask

from lesoon_restful import Api
from lesoon_restful import ModelResource
from lesoon_restful.contrib.alchemy.manager import SQLAlchemyManager
from lesoon_restful.contrib.alchemy.schema import SQLAlchemyAutoSchema
from lesoon_restful.routes import ItemRoute

app = LesoonFlask(__name__)
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    year_published = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=5)


db.create_all()


class BookSchema(SQLAlchemyAutoSchema):

    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Book
        load_instance = True


class BookManager(SQLAlchemyManager):

    def write_off_book(self, item):
        pass


class BookResource(ModelResource):
    manager: BookManager

    class Meta:
        model = Book
        schema = BookSchema
        manager = BookManager

    @ItemRoute.GET('/rating')
    def rating(self, book):
        return book.rating

    @ItemRoute.POST('/writeOff')
    def write_off_book(self, item):
        self.manager.write_off_book(item)
        return None


api = Api(app)
api.add_resource(BookResource)

if __name__ == '__main__':
    import pprint

    pprint.pprint(sorted(app.url_map.iter_rules(), key=lambda x: x.rule))
    app.run()
