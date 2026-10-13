"""Idempotent demo data loader. Never resets an existing database."""
from werkzeug.security import generate_password_hash
from sqlalchemy import select, text
from app import create_app
from models import db, User, Term, Course, Offering, Eligibility, Schedule, Choice, Grade
from catalog_data import catalog


def seed():
    db.create_all()
    if db.session.scalar(select(Term.id).limit(1)):
        print('Existing database found; seed skipped.')
        return
    password=generate_password_hash('Demo2026!')
    db.session.add(User(id=1,username='admin',password_hash=password,role='registrar',name='教务管理员',department='教务处'))
    for i in range(1,4):
        db.session.add(User(id=100+i,username=f'professor{i:02}',password_hash=password,role='professor',name=['林老师','陈老师','周老师'][i-1],department='计算机科学与技术'))
    for i in range(1,15):
        db.session.add(User(id=200+i,username=f'student{i:02}',password_hash=password,role='student',name=f'演示学生{i:02}',department='计算机科学与技术',graduation_date='2027-06-30'))
    db.session.add_all([Term(id=1,name='2026 春季学期',state='closed',current=False),Term(id=2,name='2026 秋季学期',state='open',current=True)])
    db.session.flush()
    for c in catalog():
        db.session.add(Course(**c))
        db.session.flush()
    for i in range(1,11):
        db.session.add(Offering(id=i,course_id=i,term_id=2,professor_id=101+(i%3) if i!=9 else None,
            day=(i-1)%5+1,start=1 if i<=5 else 5,end=2 if i<=5 else 6,room=f'教学楼 A{100+i}',status='open'))
    # Another delivery of CS201 deliberately conflicts with offering 3.
    db.session.add(Offering(id=11,course_id=2,term_id=2,professor_id=None,day=3,start=1,end=2,room='教学楼 B201',status='open'))
    db.session.add_all([Offering(id=101,course_id=1,term_id=1,professor_id=101,day=1,start=1,end=2,room='A101',status='closed'),
        Offering(id=102,course_id=1,term_id=1,professor_id=102,day=2,start=1,end=2,room='A102',status='closed')])
    for prof in [101,102,103]:
        for c in range(1,11): db.session.add(Eligibility(professor_id=prof,course_id=c))
    db.session.flush()
    for i in range(1,13):
        s=Schedule(student_id=200+i,term_id=1,submitted=True)
        db.session.add(s)
        db.session.flush()
        oid=101 if i<=10 else 102
        db.session.add(Choice(schedule_id=s.id,offering_id=oid,kind='primary',rank=0,status='enrolled'))
        db.session.add(Grade(student_id=200+i,offering_id=oid,value='A' if i%2 else 'B'))
    for sid in [202,203,204]:
        s=Schedule(student_id=sid,term_id=2,submitted=True)
        db.session.add(s)
        db.session.flush()
        for rank,oid in enumerate([2,3,4,5,6,7]):
            db.session.add(Choice(schedule_id=s.id,offering_id=oid,kind='primary' if rank<4 else 'alternate',rank=rank%4,status='enrolled' if rank<4 else 'selected'))
    db.session.commit()
    if db.engine.dialect.name=='postgresql':
        # Explicit fixture IDs must not leave SERIAL sequences behind.
        for table in ['user','term','course','offering']:
            db.session.execute(text(f"SELECT setval(pg_get_serial_sequence('\"{table}\"','id'), (SELECT MAX(id) FROM \"{table}\"))"))
        db.session.commit()
    print('Demo initialized. Login: admin / professor01 / student01. Password: Demo2026!')

if __name__=='__main__':
    with create_app().app_context(): seed()
