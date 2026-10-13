"""Persistence model. Monetary values are integer cents; course data is a local read-only snapshot."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(80), default="计算机科学与技术")
    birth_date = db.Column(db.String(10), default="")
    graduation_date = db.Column(db.String(10), default="")
    identity_number = db.Column(db.String(30), default="")
    status = db.Column(db.String(20), default="active", nullable=False)
    __table_args__ = (db.CheckConstraint("role in ('student','professor','registrar')"),
                      db.CheckConstraint("status in ('active','inactive','deleted')"))


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    state = db.Column(db.String(20), nullable=False, default="open")
    current = db.Column(db.Boolean, nullable=False, default=False)
    __table_args__ = (db.CheckConstraint("state in ('open','closed')"),)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    fee_cents = db.Column(db.Integer, nullable=False)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey("course.id"))


class Offering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    day = db.Column(db.Integer, nullable=False)
    start = db.Column(db.Integer, nullable=False)
    end = db.Column(db.Integer, nullable=False)
    room = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    course = db.relationship(Course)
    professor = db.relationship(User)
    __table_args__ = (db.CheckConstraint("day between 1 and 7"),
                      db.CheckConstraint('"start" >= 1 AND "end" >= "start" AND "end" <= 12'),
                      db.CheckConstraint("status in ('open','closed','cancelled')"))


class Eligibility(db.Model):
    professor_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), primary_key=True)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    submitted = db.Column(db.Boolean, default=False, nullable=False)
    __table_args__ = (db.UniqueConstraint("student_id", "term_id"),)


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id", ondelete="CASCADE"), nullable=False)
    offering_id = db.Column(db.Integer, db.ForeignKey("offering.id"), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="selected")
    offering = db.relationship(Offering)
    __table_args__ = (db.UniqueConstraint("schedule_id", "offering_id"),
                      db.CheckConstraint("kind in ('primary','alternate')"),
                      db.CheckConstraint("status in ('selected','enrolled','cancelled')"))


class Grade(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    offering_id = db.Column(db.Integer, db.ForeignKey("offering.id"), primary_key=True)
    value = db.Column(db.String(1), nullable=False)
    __table_args__ = (db.CheckConstraint("value in ('A','B','C','D','F','I')"),)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.String(200), default="")
    next_attempt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint("student_id", "term_id"),)


class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
