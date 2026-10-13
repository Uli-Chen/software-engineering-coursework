import os
import pytest
from app import create_app
from models import db
from seed import seed

@pytest.fixture()
def app():
    uri=os.environ.get('TEST_DATABASE_URL',os.environ.get('DATABASE_URL','postgresql+psycopg://course:course_demo_db_2026@db:5432/course').rsplit('/',1)[0]+'/course_test')
    if not uri.endswith('/course_test'): raise RuntimeError('Only the dedicated course_test database may be reset')
    application=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':uri,'SECRET_KEY':'test-only','SKIP_EXTERNAL':True})
    with application.app_context():
        db.drop_all();seed()
    yield application
    with application.app_context(): db.session.remove()

class Client:
    def __init__(self,app,username='student01'):
        self.client=app.test_client()
        self.token=self.client.get('/api/session').json['csrf']
        r=self.call('POST','/login',{'username':username,'password':'Demo2026!'})
        assert r.status_code==200,r.json
        self.token=r.json['csrf']
    def call(self,method,path,data=None):
        return self.client.open('/api'+path,method=method,json=data,headers={'X-CSRF-Token':self.token})

@pytest.fixture()
def student(app): return Client(app)
@pytest.fixture()
def admin(app): return Client(app,'admin')
@pytest.fixture()
def professor(app): return Client(app,'professor01')
