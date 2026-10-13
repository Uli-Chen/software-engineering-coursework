"""Course registration HTTP API. Every change is committed as a single transaction."""
import os
import secrets
import time
from threading import Lock
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, g, jsonify, request, session
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Term, Course, Offering, Eligibility, Schedule, Choice, Grade, Invoice, Audit


class BusinessError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def fail(message, status=400):
    raise BusinessError(message, status)


def rows(model, **filters):
    return db.session.scalars(select(model).filter_by(**filters)).all()


def one(model, **filters):
    return db.session.scalar(select(model).filter_by(**filters))


def auth(*roles):
    def decorate(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            g.user = db.session.get(User, session.get('uid')) if session.get('uid') else None
            if not g.user or g.user.status != 'active':
                fail('请先登录有效账户', 401)
            if roles and g.user.role not in roles:
                fail('没有执行此操作的权限', 403)
            return f(*args, **kwargs)
        return wrapped
    return decorate


def current_term(lock=False, exclusive=False):
    term = one(Term, current=True)
    if not term:
        fail('当前学期尚未配置', 503)
    if lock and db.engine.dialect.name == 'postgresql':
        # Shared lock lets ordinary registration run concurrently. Closing refuses
        # to start while any registration transaction owns a shared lock.
        function = 'pg_try_advisory_xact_lock' if exclusive else 'pg_advisory_xact_lock_shared'
        acquired = db.session.scalar(text(f'SELECT {function}(:key)'), {'key': 700000 + term.id})
        if exclusive and not acquired:
            fail('仍有选课事务进行中，请稍后再关闭', 409)
        db.session.refresh(term)
    return term


def require_open(term):
    if term.state != 'open':
        fail('本学期选课已关闭', 409)


def audit(action, detail):
    db.session.add(Audit(actor_id=g.user.id, action=action, detail=detail))


def count(offering_id, exclude_schedule=None):
    stmt = select(func.count(Choice.id)).where(Choice.offering_id == offering_id, Choice.status == 'enrolled')
    if exclude_schedule is not None:
        stmt = stmt.where(Choice.schedule_id != exclude_schedule)
    return db.session.scalar(stmt)


def overlaps(a, b):
    return a.day == b.day and a.start <= b.end and b.start <= a.end


def passed(student_id, course_id):
    if not course_id:
        return True
    return bool(db.session.scalar(select(Grade.student_id).join(Offering, Grade.offering_id == Offering.id)
        .where(Grade.student_id == student_id, Offering.course_id == course_id, Grade.value.in_(['A','B','C','D']))))


def validate_offering(offering, student_id, accepted, schedule_id):
    if offering.status != 'open':
        return f'{offering.course.name}未开放'
    if count(offering.id, schedule_id) >= 10:
        return f'{offering.course.name}已满员，请重新选择'
    if not passed(student_id, offering.course.prerequisite_id):
        return f'{offering.course.name}的先修课程未通过'
    if any(overlaps(offering, other) for other in accepted):
        return f'{offering.course.name}与已选课程时间冲突'
    if any(offering.course_id == other.course_id for other in accepted):
        return '同一课程不能重复选择'
    return None


def user_json(u, private=False):
    result = dict(id=u.id, username=u.username, name=u.name, role=u.role, department=u.department, status=u.status)
    if private:
        result.update(birth_date=u.birth_date, graduation_date=u.graduation_date, identity_number=u.identity_number)
    return result


def offering_json(o):
    return dict(id=o.id, course_id=o.course_id, code=o.course.code, name=o.course.name,
        department=o.course.department, credits=o.course.credits, fee_cents=o.course.fee_cents,
        prerequisite_id=o.course.prerequisite_id, professor_id=o.professor_id,
        professor=o.professor.name if o.professor else '待安排', day=o.day, start=o.start, end=o.end,
        room=o.room, status=o.status, enrolled=count(o.id), capacity=10, term_id=o.term_id)


def schedule_json(s):
    if not s:
        return dict(submitted=False, choices=[])
    return dict(id=s.id, submitted=s.submitted, choices=[dict(kind=c.kind, rank=c.rank, status=c.status,
        offering=offering_json(c.offering)) for c in db.session.scalars(select(Choice).where(Choice.schedule_id == s.id)
        .order_by(Choice.kind.desc(), Choice.rank)).all()])


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        fail('请求必须为 JSON 对象')
    return data


def id_list(data, key, maximum):
    values = data.get(key, [])
    if not isinstance(values, list) or len(values) > maximum or any(type(v) is not int or v <= 0 for v in values):
        fail(f'{key}必须为最多 {maximum} 个有效编号组成的数组')
    if len(set(values)) != len(values):
        fail('不能重复选择教学班')
    return values


def create_app(config=None):
    app = Flask(__name__, static_folder='static', static_url_path='')
    catalog_cache = {'expires': 0, 'courses': []}
    catalog_lock = Lock()
    app.config.update(SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'postgresql+psycopg://course:course_demo_db_2026@localhost:55432/course'),
        SECRET_KEY=os.environ.get('SECRET_KEY', 'local-development-only-change-me'),
        SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
        SESSION_COOKIE_NAME='secd_session', SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1', PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        MAX_CONTENT_LENGTH=128*1024, CATALOG_URL=os.environ.get('CATALOG_URL','http://localhost:6000'),
        BILLING_URL=os.environ.get('BILLING_URL','http://localhost:6000'),
        MOCK_CONTROL_KEY=os.environ.get('MOCK_CONTROL_KEY','local-demo-adapter-key'))
    if config:
        app.config.update(config)
    db.init_app(app)

    @app.before_request
    def csrf():
        if request.method in ('POST','PUT','DELETE','PATCH'):
            expected = session.get('csrf')
            if not expected or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''), expected):
                fail('安全令牌已过期，请刷新页面', 403)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(BusinessError)
    def business_error(e):
        db.session.rollback()
        return jsonify(error=e.message), e.status

    @app.errorhandler(IntegrityError)
    def integrity_error(e):
        db.session.rollback()
        return jsonify(error='数据重复或有关联记录，操作未保存'), 409

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify(error=e.description), e.code

    @app.get('/')
    def index():
        return app.send_static_file('index.html')

    @app.get('/api/health')
    def health():
        db.session.execute(text('SELECT 1'))
        return jsonify(status='ok')

    @app.get('/api/session')
    def get_session():
        session.setdefault('csrf', secrets.token_hex(32))
        user = db.session.get(User, session.get('uid')) if session.get('uid') else None
        return jsonify(csrf=session['csrf'], user=user_json(user) if user and user.status == 'active' else None)

    @app.post('/api/login')
    def login():
        data = payload()
        if not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
            fail('请输入用户名和密码')
        user = one(User, username=data['username'])
        if not user or user.status != 'active' or not check_password_hash(user.password_hash, data['password']):
            fail('用户名或密码错误，或账户已停用', 401)
        session.clear()
        session.update(uid=user.id, csrf=secrets.token_hex(32))
        session.permanent = True
        return jsonify(user=user_json(user), csrf=session['csrf'])

    @app.post('/api/logout')
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.get('/api/overview')
    @auth()
    def overview():
        term = current_term()
        return jsonify(term=dict(id=term.id,name=term.name,state=term.state),
            stats=dict(offerings=len(rows(Offering,term_id=term.id)), students=len(rows(User,role='student',status='active')),
                enrolled=db.session.scalar(select(func.count(Choice.id)).join(Schedule).where(Schedule.term_id==term.id,Choice.status=='enrolled')),
                pending_invoices=len(rows(Invoice,term_id=term.id,status='pending'))))

    @app.get('/api/catalog')
    @auth()
    def catalog():
        metadata={}
        if not app.config.get('SKIP_EXTERNAL'):
            try:
                with catalog_lock:
                    if time.monotonic()>=catalog_cache['expires']:
                        response = requests.get(app.config['CATALOG_URL']+'/catalog', timeout=3)
                        response.raise_for_status()
                        courses=response.json().get('courses')
                        if not isinstance(courses,list): raise ValueError('invalid catalog')
                        catalog_cache.update(courses=courses,expires=time.monotonic()+5)
                    metadata={c['id']:c for c in catalog_cache['courses']}
            except (requests.RequestException, ValueError, KeyError, TypeError):
                fail('课程目录服务暂时不可用，请稍后重试', 503)
        result=[]
        for o in rows(Offering,term_id=current_term().id):
            item=offering_json(o)
            # The legacy interface is read-only. Registration data remains local.
            if o.course_id in metadata:
                for key in ['code','name','department','credits','fee_cents','prerequisite_id']:
                    item[key]=metadata[o.course_id][key]
            result.append(item)
        return jsonify(offerings=result)

    @app.get('/api/schedule')
    @auth('student')
    def get_schedule():
        return jsonify(schedule_json(one(Schedule,student_id=g.user.id,term_id=current_term().id)))

    @app.put('/api/schedule')
    @auth('student')
    def put_schedule():
        data = payload()
        primary, alternate = id_list(data,'primary',4), id_list(data,'alternate',2)
        submit = data.get('submit', False)
        if type(submit) is not bool:
            fail('submit必须为布尔值')
        if set(primary) & set(alternate):
            fail('主选和备选不能重复')
        term = current_term(lock=True)
        require_open(term)
        db.session.execute(select(User).where(User.id==g.user.id).with_for_update()).scalar_one()
        s = one(Schedule,student_id=g.user.id,term_id=term.id)
        if submit and (not primary or (not s or not s.submitted) and (len(primary)!=4 or len(alternate)!=2)):
            fail('首次提交需要 4 门主选和 2 门备选；提交后可在选课期内退改选')
        old = rows(Choice,schedule_id=s.id) if s else []
        if not submit and s and s.submitted:
            fail('已提交课表请使用“提交选课”保存修改，以保持选课名额一致')
        all_ids = sorted(set(primary+alternate+[c.offering_id for c in old]))
        offerings = {o.id:o for o in db.session.scalars(select(Offering).where(Offering.id.in_(all_ids))
            .order_by(Offering.id).with_for_update()).all()}
        if any(i not in offerings or offerings[i].term_id!=term.id for i in primary+alternate):
            fail('存在无效教学班')
        course_ids = [offerings[i].course_id for i in primary+alternate]
        if len(course_ids)!=len(set(course_ids)):
            fail('主选及备选不能重复选择同一课程')
        if submit:
            accepted=[]
            for i in primary:
                error=validate_offering(offerings[i],g.user.id,accepted,s.id if s else None)
                if error: fail(error,409)
                accepted.append(offerings[i])
        if not s:
            s=Schedule(student_id=g.user.id,term_id=term.id)
            db.session.add(s)
            db.session.flush()
        for c in old: db.session.delete(c)
        db.session.flush()
        s.submitted=submit
        for kind, ids in [('primary',primary),('alternate',alternate)]:
            for rank,i in enumerate(ids):
                db.session.add(Choice(schedule_id=s.id,offering_id=i,kind=kind,rank=rank,
                    status='enrolled' if submit and kind=='primary' else 'selected'))
        audit('schedule.submit' if submit else 'schedule.save',f'schedule={s.id}')
        db.session.commit()
        return jsonify(schedule_json(s))

    @app.delete('/api/schedule')
    @auth('student')
    def delete_schedule():
        term=current_term(lock=True)
        require_open(term)
        db.session.execute(select(User).where(User.id==g.user.id).with_for_update()).scalar_one()
        s=one(Schedule,student_id=g.user.id,term_id=term.id)
        if not s: fail('没有可删除的课表',404)
        ids=[c.offering_id for c in rows(Choice,schedule_id=s.id)]
        db.session.execute(select(Offering).where(Offering.id.in_(ids)).order_by(Offering.id).with_for_update()).all()
        for c in rows(Choice,schedule_id=s.id): db.session.delete(c)
        db.session.delete(s)
        audit('schedule.delete',f'student={g.user.id}')
        db.session.commit()
        return jsonify(ok=True)

    @app.get('/api/report-card')
    @auth('student')
    def report_card():
        previous=db.session.scalar(select(Term).where(Term.id<current_term().id).order_by(Term.id.desc()))
        if not previous: return jsonify(term='',grades=[])
        enrolled=db.session.scalars(select(Choice).join(Schedule).where(Schedule.student_id==g.user.id,
            Schedule.term_id==previous.id,Choice.status=='enrolled')).all()
        return jsonify(term=previous.name, grades=[dict(course=c.offering.course.name,code=c.offering.course.code,
            credits=c.offering.course.credits,value=(db.session.get(Grade,(g.user.id,c.offering_id)).value
                if db.session.get(Grade,(g.user.id,c.offering_id)) else '待录入')) for c in enrolled])

    @app.get('/api/teaching')
    @auth('professor')
    def teaching():
        term=current_term()
        eligible={x.course_id for x in rows(Eligibility,professor_id=g.user.id)}
        return jsonify(eligible=[offering_json(o) for o in rows(Offering,term_id=term.id) if o.course_id in eligible],
            mine=[offering_json(o) for o in rows(Offering,professor_id=g.user.id)])

    @app.put('/api/teaching')
    @auth('professor')
    def put_teaching():
        ids=id_list(payload(),'offering_ids',20)
        term=current_term(lock=True)
        require_open(term)
        db.session.execute(select(User).where(User.id==g.user.id).with_for_update()).scalar_one()
        old=rows(Offering,professor_id=g.user.id,term_id=term.id)
        locked=db.session.scalars(select(Offering).where(Offering.id.in_(sorted(set(ids+[o.id for o in old]))))
            .order_by(Offering.id).with_for_update().execution_options(populate_existing=True)).all()
        mapping={o.id:o for o in locked}
        eligible={e.course_id for e in rows(Eligibility,professor_id=g.user.id)}
        chosen=[]
        for i in ids:
            o=mapping.get(i)
            if not o or o.term_id!=term.id or o.course_id not in eligible: fail('存在无授课资格的教学班',403)
            if o.professor_id not in (None,g.user.id): fail('该教学班已有其他教师',409)
            if any(overlaps(o,x) for x in chosen): fail('授课时间冲突',409)
            chosen.append(o)
        for o in locked:
            if o.id in ids: o.professor_id=g.user.id
            elif o.professor_id==g.user.id: o.professor_id=None
        audit('teaching.update',f'offerings={ids}')
        db.session.commit()
        return jsonify(ok=True)

    @app.get('/api/offerings/<int:oid>/roster')
    @auth('professor')
    def roster(oid):
        o=db.session.get(Offering,oid)
        if not o or o.professor_id!=g.user.id: fail('仅可查看本人授课名单',403)
        students=db.session.scalars(select(User).join(Schedule,Schedule.student_id==User.id).join(Choice)
            .where(Choice.offering_id==oid,Choice.status=='enrolled').order_by(User.id)).all()
        return jsonify(offering=offering_json(o), can_grade=o.term_id<current_term().id and o.status=='closed',
            students=[dict(id=u.id,name=u.name,username=u.username,grade=(db.session.get(Grade,(u.id,oid)).value
            if db.session.get(Grade,(u.id,oid)) else '')) for u in students])

    @app.put('/api/offerings/<int:oid>/grades')
    @auth('professor')
    def grades(oid):
        o=db.session.scalar(select(Offering).where(Offering.id==oid).with_for_update())
        if not o or o.professor_id!=g.user.id: fail('仅任课教师可录入该班成绩',403)
        if o.term_id>=current_term().id or o.status!='closed': fail('只能录入已结束学期的成绩',409)
        data=payload().get('grades')
        if not isinstance(data,list) or len(data)>10: fail('成绩必须为最多 10 条记录组成的数组')
        seen=set()
        for item in data:
            if not isinstance(item,dict) or type(item.get('student_id')) is not int: fail('无效学生编号')
            sid,value=item['student_id'],item.get('value')
            if sid in seen: fail('学生编号重复')
            seen.add(sid)
            if value not in ['','A','B','C','D','F','I']: fail('成绩仅允许 A、B、C、D、F、I 或留空')
            enrolled=db.session.scalar(select(Choice.id).join(Schedule).where(Schedule.student_id==sid,
                Choice.offering_id==oid,Choice.status=='enrolled'))
            if not enrolled: fail('学生未选修该教学班',400)
            if value=='': continue
            grade=db.session.get(Grade,(sid,oid))
            if grade: grade.value=value
            else: db.session.add(Grade(student_id=sid,offering_id=oid,value=value))
        audit('grades.update',f'offering={oid}; count={len(data)}')
        db.session.commit()
        return jsonify(ok=True)

    @app.get('/api/users')
    @auth('registrar')
    def users():
        return jsonify(users=[user_json(u,True) for u in db.session.scalars(select(User)
            .where(User.role!='registrar',User.status!='deleted').order_by(User.id)).all()])

    def assign_user(u,data,new=False):
        for key,limit in [('name',80),('department',80),('identity_number',30),('birth_date',10),('graduation_date',10)]:
            value=data.get(key, getattr(u,key) or '')
            if not isinstance(value,str) or len(value)>limit: fail(f'{key}格式错误')
            if key in ('name','department') and not value.strip(): fail('姓名和院系不能为空')
            if key.endswith('_date') and value:
                try: date.fromisoformat(value)
                except ValueError: fail('日期格式必须为 YYYY-MM-DD')
            setattr(u,key,value.strip())
        status=data.get('status','active')
        if status not in ('active','inactive'): fail('无效账户状态')
        u.status=status
        password=data.get('password','')
        if not isinstance(password,str): fail('密码格式错误')
        if new or password:
            if len(password)<8 or len(password)>100: fail('密码长度为 8 至 100 位')
            u.password_hash=generate_password_hash(password)

    @app.post('/api/users')
    @auth('registrar')
    def add_user():
        data=payload()
        if data.get('role') not in ('student','professor'): fail('仅可创建学生或教师')
        username=data.get('username','')
        if not isinstance(username,str) or not 3<=len(username)<=50 or not username.isascii() or not username.replace('_','').isalnum():
            fail('用户名为 3 至 50 位英文字母、数字或下划线')
        u=User(username=username,role=data['role'])
        assign_user(u,data,True)
        db.session.add(u)
        db.session.flush()
        audit('user.create',f'user={u.id}')
        db.session.commit()
        return jsonify(user=user_json(u,True)),201

    @app.put('/api/users/<int:uid>')
    @auth('registrar')
    def update_user(uid):
        current_term(lock=True)
        u=db.session.scalar(select(User).where(User.id==uid).with_for_update())
        if not u or u.role=='registrar' or u.status=='deleted': fail('未找到可维护的用户',404)
        assign_user(u,payload())
        audit('user.update',f'user={uid}')
        db.session.commit()
        return jsonify(user=user_json(u,True))

    @app.delete('/api/users/<int:uid>')
    @auth('registrar')
    def delete_user(uid):
        term=current_term(lock=True)
        u=db.session.scalar(select(User).where(User.id==uid).with_for_update())
        if not u or u.role=='registrar' or u.status=='deleted': fail('用户不存在',404)
        if one(Offering,professor_id=uid,term_id=term.id) or one(Schedule,student_id=uid,term_id=term.id):
            fail('该用户仍关联当前学期课表或授课任务，请先解除关联',409)
        u.status='deleted'  # Retain historical grades and audit references.
        audit('user.delete',f'user={uid}')
        db.session.commit()
        return jsonify(ok=True)

    @app.put('/api/users/<int:uid>/eligibility')
    @auth('registrar')
    def eligibility(uid):
        term=current_term(lock=True)
        require_open(term)
        u=db.session.scalar(select(User).where(User.id==uid).with_for_update())
        if not u or u.role!='professor' or u.status=='deleted': fail('教师不存在',404)
        ids=id_list(payload(),'course_ids',50)
        if any(not db.session.get(Course,i) for i in ids): fail('课程不存在')
        if any(o.course_id not in ids for o in rows(Offering,professor_id=uid,term_id=term.id)):
            fail('需先取消对应教学班授课，再撤销资格',409)
        for e in rows(Eligibility,professor_id=uid): db.session.delete(e)
        db.session.flush()
        for i in ids: db.session.add(Eligibility(professor_id=uid,course_id=i))
        audit('eligibility.update',f'professor={uid};courses={ids}')
        db.session.commit()
        return jsonify(ok=True)

    @app.get('/api/users/<int:uid>/eligibility')
    @auth('registrar')
    def get_eligibility(uid):
        return jsonify(course_ids=[e.course_id for e in rows(Eligibility,professor_id=uid)])

    @app.post('/api/registration/close')
    @auth('registrar')
    def close_registration():
        if payload().get('confirm') is not True: fail('请确认关闭选课')
        term=current_term(lock=True,exclusive=True)
        require_open(term)
        offerings=rows(Offering,term_id=term.id)
        submitted=rows(Schedule,term_id=term.id,submitted=True)
        cancelled=[]
        # Cancel teacherless offerings before trying ordered substitutes.
        for o in offerings:
            if o.professor_id is None:
                o.status='cancelled'
                for c in rows(Choice,offering_id=o.id): c.status='cancelled'
        db.session.flush()
        initially_viable={o.id for o in offerings if o.professor_id and count(o.id)>=3}
        for s in sorted(submitted,key=lambda x:x.id):
            choices=rows(Choice,schedule_id=s.id)
            retained=[c for c in choices if c.status=='enrolled']
            committed=[c for c in retained if c.offering_id in initially_viable]
            replaceable=sorted([c for c in retained if c.offering_id not in initially_viable],key=lambda c:c.rank)
            for c in sorted([x for x in choices if x.kind=='alternate'],key=lambda x:x.rank):
                if len(committed)>=4: break
                replacement=replaceable[0] if replaceable else None
                other=[x.offering for x in retained if x is not replacement]
                if len(other)>=4: break
                if not validate_offering(c.offering,s.student_id,other,s.id):
                    if replacement:
                        replacement.status='selected'
                        retained.remove(replacement)
                        replaceable.remove(replacement)
                    c.status='enrolled'
                    retained.append(c)
                    committed.append(c)
                    db.session.flush()
        # Evaluate final sizes only after all replacement attempts.
        for o in offerings:
            o.status='closed' if o.professor_id and count(o.id)>=3 else 'cancelled'
            if o.status=='cancelled':
                cancelled.append(o.id)
                for c in rows(Choice,offering_id=o.id): c.status='cancelled'
        db.session.flush()
        for s in submitted:
            final=[c.offering for c in rows(Choice,schedule_id=s.id) if c.status=='enrolled']
            amount=sum(o.course.fee_cents for o in final)
            db.session.add(Invoice(student_id=s.student_id,term_id=term.id,amount_cents=amount,
                payload=dict(student_id=s.student_id,term=term.name,amount_cents=amount,
                             courses=[dict(id=o.id,name=o.course.name) for o in final])))
        term.state='closed'
        audit('registration.close',f'cancelled={cancelled};invoices={len(submitted)}')
        db.session.commit()
        return jsonify(ok=True,cancelled=cancelled,invoices=len(submitted))

    @app.get('/api/invoices')
    @auth('registrar')
    def invoices():
        return jsonify(invoices=[dict(id=i.id,student=db.session.get(User,i.student_id).name,
            amount_cents=i.amount_cents,status=i.status,attempts=i.attempts,last_error=i.last_error,
            courses=i.payload['courses']) for i in rows(Invoice,term_id=current_term().id)])

    @app.get('/api/audit')
    @auth('registrar')
    def audits():
        return jsonify(events=[dict(id=a.id,actor=db.session.get(User,a.actor_id).name if a.actor_id else '系统',
            action=a.action,detail=a.detail,created_at=a.created_at.isoformat())
            for a in db.session.scalars(select(Audit).order_by(Audit.id.desc()).limit(100)).all()])

    @app.route('/api/integrations',methods=['GET','PUT'])
    @auth('registrar')
    def integrations():
        try:
            if request.method=='PUT':
                data=payload()
                if set(data)!={'catalog_available','billing_available'} or any(type(v) is not bool for v in data.values()):
                    fail('请输入两个布尔类型的服务状态')
                result=requests.put(app.config['BILLING_URL']+'/control',json=data,
                    headers={'X-Control-Key':app.config['MOCK_CONTROL_KEY']},timeout=3)
                audit('integration.simulate',str(data))
                db.session.commit()
            else:
                result=requests.get(app.config['BILLING_URL']+'/control',headers={'X-Control-Key':app.config['MOCK_CONTROL_KEY']},timeout=3)
            result.raise_for_status()
            return jsonify(result.json())
        except requests.RequestException:
            fail('模拟外部服务不可达',503)

    return app
