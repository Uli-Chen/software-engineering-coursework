"""Transactional outbox: persistent retries, capped delay, idempotent delivery."""
import time
from datetime import datetime, timezone, timedelta
import requests
from sqlalchemy import select
from app import create_app
from models import db, Invoice


def deliver_batch(app):
    with app.app_context():
        now=datetime.now(timezone.utc)
        invoices=db.session.scalars(select(Invoice).where(Invoice.status=='pending',Invoice.next_attempt<=now)
            .order_by(Invoice.id).limit(10).with_for_update(skip_locked=True)).all()
        for invoice in invoices:
            invoice.attempts+=1
            try:
                response=requests.post(app.config['BILLING_URL']+'/invoices',json=invoice.payload,
                    headers={'Idempotency-Key':f'course-{invoice.term_id}-{invoice.student_id}'},timeout=3)
                response.raise_for_status()
                invoice.status='sent'
                invoice.last_error=''
            except requests.RequestException as e:
                invoice.last_error=type(e).__name__
                invoice.next_attempt=now+timedelta(seconds=min(60,3*2**min(invoice.attempts,5)))
        db.session.commit()
        return len(invoices)

if __name__=='__main__':
    application=create_app()
    while True:
        try: deliver_batch(application)
        except Exception:
            application.logger.exception('Billing retry cycle failed')
        time.sleep(3)
