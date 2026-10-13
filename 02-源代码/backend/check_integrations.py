"""Run real HTTP integration checks against an isolated mock container and test DB."""
import json, os
from datetime import datetime, timezone, timedelta
import requests
from sqlalchemy import select
from app import create_app
from models import db, Invoice
from seed import seed
from worker import deliver_batch

url=os.environ['ISOLATED_MOCK_URL']
uri=os.environ.get('TEST_DATABASE_URL',os.environ.get('DATABASE_URL','postgresql+psycopg://course:course_demo_db_2026@db:5432/course').rsplit('/',1)[0]+'/course_test')
assert uri.endswith('/course_test')
app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':uri,'CATALOG_URL':url,'BILLING_URL':url})
with app.app_context(): db.drop_all();seed()
client=app.test_client();token=client.get('/api/session').json['csrf']
r=client.post('/api/login',json={'username':'admin','password':'Demo2026!'},headers={'X-CSRF-Token':token})
headers={'X-CSRF-Token':r.json['csrf']}
control={'X-Control-Key':'local-demo-adapter-key'}
def mode(catalog=True,billing=True):
    r=requests.put(url+'/control',json={'catalog_available':catalog,'billing_available':billing},headers=control,timeout=3)
    r.raise_for_status()
results={}
mode(False,False)
assert client.get('/api/catalog').status_code==503
results['catalog_down_503']=True
mode(True,False)
assert len(client.get('/api/catalog').json['offerings'])==11
results['catalog_recovery']=True
assert client.post('/api/registration/close',json={'confirm':True},headers=headers).status_code==200
deliver_batch(app)
with app.app_context():
    invoices=db.session.scalars(select(Invoice)).all()
    assert all(i.status=='pending' and i.attempts==1 for i in invoices)
    for i in invoices: i.next_attempt=datetime.now(timezone.utc)-timedelta(seconds=1)
    db.session.commit()
results['billing_failure_persists_3_pending']=True
mode(True,True)
deliver_batch(app)
with app.app_context():
    invoices=db.session.scalars(select(Invoice)).all()
    assert all(i.status=='sent' and i.attempts==2 for i in invoices)
    first=invoices[0]
    requests.post(url+'/invoices',json=first.payload,headers={'Idempotency-Key':f'course-{first.term_id}-{first.student_id}'},timeout=3).raise_for_status()
results['billing_recovery_3_sent']=True
assert requests.get(url+'/control',headers=control,timeout=3).json()['receipts']==3
results['duplicate_delivery_receipt_count_3']=True
print(json.dumps(results,indent=2))
