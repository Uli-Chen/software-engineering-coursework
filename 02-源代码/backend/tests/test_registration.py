from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from threading import Barrier
from sqlalchemy import select, text
import requests
from app import count
from models import db, Term, Offering, Schedule, Choice, Invoice
from conftest import Client
from worker import deliver_batch

VALID={'primary':[2,3,4,5],'alternate':[6,7],'submit':True}

def test_unauthenticated_and_csrf(app):
    c=app.test_client()
    assert c.get('/api/schedule').status_code==401
    assert c.post('/api/login',json={}).status_code==403

def test_bad_login(student):
    assert student.call('POST','/login',{'username':'student01','password':'wrong'}).status_code==401

def test_role_boundaries(student,professor):
    assert student.call('GET','/users').status_code==403
    assert professor.call('GET','/schedule').status_code==403
    assert student.call('POST','/registration/close',{'confirm':True}).status_code==403

def test_draft_does_not_reserve(student,app):
    assert student.call('PUT','/schedule',{'primary':[2],'alternate':[],'submit':False}).status_code==200
    with app.app_context(): assert count(2)==3

def test_first_submit_requires_four_plus_two(student):
    assert student.call('PUT','/schedule',{'primary':[2],'alternate':[],'submit':True}).status_code==400

def test_submit_and_alternates_no_seat(student,app):
    r=student.call('PUT','/schedule',VALID)
    assert r.status_code==200,r.json
    with app.app_context(): assert count(2)==4 and count(6)==0
    assert sum(c['status']=='enrolled' for c in r.json['choices'])==4

def test_duplicate_course_deliveries(student):
    assert student.call('PUT','/schedule',{'primary':[2,11,4,5],'alternate':[6,7],'submit':True}).status_code==400

def test_conflict_atomic_rollback(student,app):
    assert student.call('PUT','/schedule',VALID).status_code==200
    assert student.call('PUT','/schedule',{'primary':[11,3,4,5],'alternate':[6,7],'submit':True}).status_code==409
    with app.app_context(): assert count(2)==4 and count(11)==0

def test_prerequisite_rejected(app):
    assert Client(app,'student13').call('PUT','/schedule',VALID).status_code==409

def test_invalid_ids_and_types(student):
    for data in [{'primary':[True]},{'primary':['2']},{'primary':[9999]},{'primary':[2,2]},{'primary':[2],'submit':'yes'}]:
        assert student.call('PUT','/schedule',data).status_code==400

def test_drop_and_delete_release_seats(student,app):
    assert student.call('PUT','/schedule',VALID).status_code==200
    assert student.call('PUT','/schedule',{'primary':[3,4,5],'alternate':[6,7],'submit':True}).status_code==200
    with app.app_context(): assert count(2)==3
    assert student.call('DELETE','/schedule').status_code==200
    with app.app_context(): assert count(3)==3

def test_submitted_cannot_become_draft(student):
    student.call('PUT','/schedule',VALID)
    assert student.call('PUT','/schedule',dict(VALID,submit=False)).status_code==400

def test_schedule_isolation(app,student):
    student.call('PUT','/schedule',VALID)
    other=Client(app,'student05')
    assert other.call('GET','/schedule?student_id=201').json['choices']==[]
    assert other.call('DELETE','/schedule').status_code==404

def test_last_seat_concurrently(app):
    with app.app_context():
        for sid in range(205,211):
            s=Schedule(student_id=sid,term_id=2,submitted=True);db.session.add(s);db.session.flush()
            for rank,oid in enumerate([2,3,4,5]): db.session.add(Choice(schedule_id=s.id,offering_id=oid,kind='primary',rank=rank,status='enrolled'))
        db.session.commit();assert count(2)==9
    clients=[Client(app,'student11'),Client(app,'student12')];barrier=Barrier(2)
    def submit(c):
        barrier.wait();return c.call('PUT','/schedule',VALID).status_code
    with ThreadPoolExecutor(2) as pool: result=list(pool.map(submit,clients))
    assert sorted(result)==[200,409]
    with app.app_context(): assert all(count(oid)==10 for oid in [2,3,4,5])

def test_close_busy_registration(app,admin):
    with app.app_context():
        with db.engine.connect() as connection:
            tx=connection.begin();connection.execute(text('SELECT pg_advisory_xact_lock_shared(700002)'))
            assert admin.call('POST','/registration/close',{'confirm':True}).status_code==409
            tx.rollback()
        assert db.session.get(Term,2).state=='open'

def test_close_cancels_and_is_not_repeatable(app,admin,student):
    student.call('PUT','/schedule',VALID)
    r=admin.call('POST','/registration/close',{'confirm':True});assert r.status_code==200,r.json
    with app.app_context():
        assert db.session.get(Offering,9).status=='cancelled'
        assert db.session.get(Offering,2).status=='closed'
        assert len(db.session.scalars(select(Invoice)).all())==4
        assert db.session.scalar(select(Invoice).where(Invoice.student_id==201)).amount_cents==390000
    assert admin.call('POST','/registration/close',{'confirm':True}).status_code==409
    assert student.call('PUT','/schedule',VALID).status_code==409
    assert student.call('DELETE','/schedule').status_code==409

def test_teacherless_primary_uses_alternate(app,admin):
    with app.app_context():
        for sid in [202,203,204]:
            s=db.session.scalar(select(Schedule).where(Schedule.student_id==sid,Schedule.term_id==2))
            c=db.session.scalar(select(Choice).where(Choice.schedule_id==s.id,Choice.offering_id==5));c.offering_id=9
        db.session.commit()
    assert admin.call('POST','/registration/close',{'confirm':True}).status_code==200
    with app.app_context():
        assert count(6)==3 and db.session.get(Offering,6).status=='closed' and count(9)==0
        for sid in [202,203,204]: assert len(db.session.scalar(select(Invoice).where(Invoice.student_id==sid)).payload['courses'])==4

def test_low_enrollment_cancelled_without_alternates(app,admin):
    with app.app_context():
        s=Schedule(student_id=201,term_id=2,submitted=True);db.session.add(s);db.session.flush()
        db.session.add(Choice(schedule_id=s.id,offering_id=8,kind='primary',rank=0,status='enrolled'));db.session.commit()
    admin.call('POST','/registration/close',{'confirm':True})
    with app.app_context():
        assert db.session.get(Offering,8).status=='cancelled' and count(8)==0
        assert db.session.scalar(select(Invoice).where(Invoice.student_id==201)).amount_cents==0

def test_teacher_roster_ownership(professor):
    assert professor.call('GET','/offerings/101/roster').status_code==200
    assert professor.call('GET','/offerings/102/roster').status_code==403

def test_grade_edit_and_report(professor,student):
    assert professor.call('PUT','/offerings/101/grades',{'grades':[{'student_id':201,'value':'C'}]}).status_code==200
    assert student.call('GET','/report-card').json['grades'][0]['value']=='C'
    assert professor.call('PUT','/offerings/101/grades',{'grades':[{'student_id':201,'value':''}]}).status_code==200
    assert student.call('GET','/report-card').json['grades'][0]['value']=='C'
    assert student.call('PUT','/offerings/101/grades',{'grades':[]}).status_code==403

def test_invalid_grade_and_non_roster(professor):
    assert professor.call('PUT','/offerings/101/grades',{'grades':[{'student_id':201,'value':'Z'}]}).status_code==400
    assert professor.call('PUT','/offerings/101/grades',{'grades':[{'student_id':214,'value':'A'}]}).status_code==400
    assert professor.call('PUT','/offerings/3/grades',{'grades':[]}).status_code==409

def test_grade_batch_atomic(professor,student):
    assert professor.call('PUT','/offerings/101/grades',{'grades':[{'student_id':201,'value':'F'},{'student_id':214,'value':'A'}]}).status_code==400
    assert student.call('GET','/report-card').json['grades'][0]['value']=='A'

def test_teaching_conflict_and_other_teacher(professor):
    assert professor.call('PUT','/teaching',{'offering_ids':[3,11]}).status_code==409
    assert professor.call('PUT','/teaching',{'offering_ids':[2]}).status_code==409

def test_teaching_update_and_closure(professor,admin):
    assert professor.call('PUT','/teaching',{'offering_ids':[3,6,9]}).status_code==200
    assert 9 in [o['id'] for o in professor.call('GET','/teaching').json['mine']]
    admin.call('POST','/registration/close',{'confirm':True})
    assert professor.call('PUT','/teaching',{'offering_ids':[]}).status_code==409

def test_user_lifecycle_and_eligibility(admin):
    data=dict(username='new_teacher',password='Password123',name='新教师',department='计算机科学与技术',role='professor')
    r=admin.call('POST','/users',data);assert r.status_code==201,r.json
    uid=r.json['user']['id'];assert uid>214
    assert admin.call('PUT',f'/users/{uid}/eligibility',{'course_ids':[1,2]}).status_code==200
    assert admin.call('GET',f'/users/{uid}/eligibility').json['course_ids']==[1,2]
    assert admin.call('PUT',f'/users/{uid}',dict(data,name='更新教师')).status_code==200
    assert admin.call('DELETE',f'/users/{uid}').status_code==200
    assert uid not in [u['id'] for u in admin.call('GET','/users').json['users']]

def test_delete_current_dependencies_rejected(admin):
    assert admin.call('DELETE','/users/202').status_code==409
    assert admin.call('DELETE','/users/101').status_code==409

def test_inactive_login_rejected(app,admin):
    assert admin.call('PUT','/users/201',{'status':'inactive'}).status_code==200
    c=app.test_client();token=c.get('/api/session').json['csrf']
    assert c.post('/api/login',headers={'X-CSRF-Token':token},json={'username':'student01','password':'Demo2026!'}).status_code==401

def test_external_catalog_failure(app,student,monkeypatch):
    app.config['SKIP_EXTERNAL']=False
    def unavailable(*args,**kwargs): raise requests.ConnectionError('simulation')
    monkeypatch.setattr('app.requests.get',unavailable)
    assert student.call('GET','/catalog').status_code==503

def test_billing_retry_keeps_outbox(app,admin,monkeypatch):
    admin.call('POST','/registration/close',{'confirm':True})
    def unavailable(*args,**kwargs): raise requests.ConnectionError('simulation')
    monkeypatch.setattr('worker.requests.post',unavailable);deliver_batch(app)
    with app.app_context():
        invoices=db.session.scalars(select(Invoice)).all();assert len(invoices)==3
        assert all(i.status=='pending' and i.attempts==1 for i in invoices)
        for i in invoices:i.next_attempt=datetime.now(timezone.utc)-timedelta(seconds=1)
        db.session.commit()
    keys=[]
    class OK:
        def raise_for_status(self): pass
    def available(*args,**kwargs): keys.append(kwargs['headers']['Idempotency-Key']);return OK()
    monkeypatch.setattr('worker.requests.post',available);deliver_batch(app);deliver_batch(app)
    assert len(keys)==len(set(keys))==3
    with app.app_context(): assert all(i.status=='sent' and i.attempts==2 for i in db.session.scalars(select(Invoice)).all())

def test_zero_grade_report(app):
    assert Client(app,'student14').call('GET','/report-card').json['grades']==[]

def test_close_does_not_charge_drafts(student,admin,app):
    student.call('PUT','/schedule',dict(VALID,submit=False));admin.call('POST','/registration/close',{'confirm':True})
    with app.app_context(): assert db.session.scalar(select(Invoice).where(Invoice.student_id==201)) is None

def test_alternate_fallback_when_first_full(app,admin):
    with app.app_context():
        # Populate the first alternate to capacity using schedules with no other choices.
        for sid in [201,205,206,207,208,209,210,211,212,213]:
            s=Schedule(student_id=sid,term_id=2,submitted=True);db.session.add(s);db.session.flush()
            db.session.add(Choice(schedule_id=s.id,offering_id=6,kind='primary',rank=0,status='enrolled'))
        for sid in [202,203,204]:
            s=db.session.scalar(select(Schedule).where(Schedule.student_id==sid,Schedule.term_id==2))
            db.session.scalar(select(Choice).where(Choice.schedule_id==s.id,Choice.offering_id==5)).offering_id=9
        db.session.commit()
    assert admin.call('POST','/registration/close',{'confirm':True}).status_code==200
    with app.app_context(): assert count(6)==10 and count(7)==3 and count(9)==0

def test_missing_eligibility_rejected(app,admin):
    data=dict(username='new_prof',password='Password123',name='无资格教师',department='计算机科学与技术',role='professor')
    assert admin.call('POST','/users',data).status_code==201
    c=app.test_client();token=c.get('/api/session').json['csrf']
    r=c.post('/api/login',json={'username':'new_prof','password':'Password123'},headers={'X-CSRF-Token':token})
    r=c.put('/api/teaching',json={'offering_ids':[9]},headers={'X-CSRF-Token':r.json['csrf']})
    assert r.status_code==403

def test_cancelled_primary_retains_no_more_than_four(app,admin):
    with app.app_context():
        for sid in [202,203,204]:
            s=db.session.scalar(select(Schedule).where(Schedule.student_id==sid,Schedule.term_id==2))
            db.session.scalar(select(Choice).where(Choice.schedule_id==s.id,Choice.offering_id==5)).offering_id=9
        db.session.commit()
    admin.call('POST','/registration/close',{'confirm':True})
    with app.app_context():
        for s in db.session.scalars(select(Schedule).where(Schedule.term_id==2)).all():
            enrolled=db.session.scalars(select(Choice).where(Choice.schedule_id==s.id,Choice.status=='enrolled')).all()
            assert len(enrolled)<=4
        assert all(count(o.id)<=10 for o in db.session.scalars(select(Offering)).all())
