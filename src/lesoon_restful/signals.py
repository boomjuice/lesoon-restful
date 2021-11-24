from flask.signals import Namespace

lesoon_restful = Namespace()

before_create = lesoon_restful.signal('before-create')

after_create = lesoon_restful.signal('after-create')

before_update = lesoon_restful.signal('before-update')

after_update = lesoon_restful.signal('after-update')

before_delete = lesoon_restful.signal('before-delete')

after_delete = lesoon_restful.signal('after-delete')
