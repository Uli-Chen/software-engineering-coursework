"""Local simulation only. Catalog is read-only; billing deduplicates persistent invoice keys."""
import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request
from catalog_data import catalog

app=Flask(__name__)
path=os.environ.get('MOCK_DATABASE','/data/mock.sqlite')
Path(path).parent.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(path) as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, catalog_available INTEGER, billing_available INTEGER)')
    conn.execute('INSERT OR IGNORE INTO settings VALUES (1,1,1)')
    conn.execute('CREATE TABLE IF NOT EXISTS receipts (key TEXT PRIMARY KEY, payload TEXT NOT NULL)')

@app.get('/catalog')
def get_catalog():
    with sqlite3.connect(path) as conn:
        available=conn.execute('SELECT catalog_available FROM settings WHERE id=1').fetchone()[0]
    return (jsonify(courses=catalog()),200) if available else (jsonify(error='Legacy catalog unavailable'),503)

@app.post('/invoices')
def invoice():
    key=request.headers.get('Idempotency-Key')
    if not key: return jsonify(error='Missing idempotency key'),400
    with sqlite3.connect(path) as conn:
        if not conn.execute('SELECT billing_available FROM settings WHERE id=1').fetchone()[0]:
            return jsonify(error='Billing unavailable'),503
        conn.execute('INSERT OR IGNORE INTO receipts VALUES (?,?)',(key,request.get_data(as_text=True)))
    return jsonify(receipt=key)

@app.route('/control',methods=['GET','PUT'])
def control():
    if request.headers.get('X-Control-Key')!=os.environ.get('MOCK_CONTROL_KEY','local-demo-adapter-key'):
        return jsonify(error='Forbidden'),403
    with sqlite3.connect(path) as conn:
        if request.method=='PUT':
            data=request.get_json()
            conn.execute('UPDATE settings SET catalog_available=?,billing_available=? WHERE id=1',
                         (bool(data['catalog_available']),bool(data['billing_available'])))
        row=conn.execute('SELECT catalog_available,billing_available FROM settings WHERE id=1').fetchone()
        total=conn.execute('SELECT count(*) FROM receipts').fetchone()[0]
    return jsonify(catalog_available=bool(row[0]),billing_available=bool(row[1]),receipts=total)
