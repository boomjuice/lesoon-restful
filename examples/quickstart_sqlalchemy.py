from flask_sqlalchemy import SQLAlchemy
from lesoon_common.base import LesoonFlask

from lesoon_restful import Api
from lesoon_restful import ModelResource
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
    app.run()

# Example use:
# $ http :5000/book title=Foo year_published:=1990
# HTTP/1.0 200 OK
# Content-Length: 72
# Content-Type: application/json
# Date: Sat, 07 Feb 2015 13:43:02 GMT
# Server: Werkzeug/0.9.6 Python/3.3.2
#
# {
#     "$uri": "/book/1",
#     "rating": 2,
#     "title": "Foo",
#     "year_published": 1990
# }
#
# $ http GET :5000/book/1/rating
# HTTP/1.0 200 OK
# Content-Length: 3
# Content-Type: application/json
# Date: Sat, 07 Feb 2015 13:43:06 GMT
# Server: Werkzeug/0.9.6 Python/3.3.2
#
# 2.5
#
# $ http POST :5000/book/1/rating value:=4
# HTTP/1.0 200 OK
# Content-Length: 3
# Content-Type: application/json
# Date: Sat, 07 Feb 2015 13:43:09 GMT
# Server: Werkzeug/0.9.6 Python/3.3.2
#
# 4.0
#
# $ http GET :5000/book/1/is-recent
# HTTP/1.0 200 OK
# Content-Length: 5
# Content-Type: application/json
# Date: Sat, 07 Feb 2015 13:43:18 GMT
# Server: Werkzeug/0.9.6 Python/3.3.2
#
# false
#
# $ http GET :5000/book/genres
# HTTP/1.0 200 OK
# Content-Length: 54
# Content-Type: application/json
# Date: Sat, 07 Feb 2015 13:43:31 GMT
# Server: Werkzeug/0.9.6 Python/3.3.2
#
# [
#     "biography",
#     "history",
#     "essay",
#     "law",
#     "philosophy"
# ]
