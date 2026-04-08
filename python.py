# app.py — ShopEasy Backend
# Requirements: pip install flask flask-cors pymysql bcrypt pyjwt stripe python-dotenv
 
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import bcrypt
import jwt
import stripe
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
 
load_dotenv()
 
app = Flask(__name__)
CORS(app)
 
# ── Config ────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY']    = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
stripe.api_key              = os.getenv('STRIPE_SECRET_KEY', 'sk_test_YOUR_STRIPE_SECRET_KEY')
 
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'shopeasy'),
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True,
}
 
# ── DB helper ─────────────────────────────────────────────────────────────────
def get_db():
    return pymysql.connect(**DB_CONFIG)
 
def query(sql, params=(), fetchone=False, fetchall=False):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetchone:  return cur.fetchone()
            if fetchall:  return cur.fetchall()
            return cur.lastrowid
    finally:
        conn.close()
 
# ── JWT auth decorator ────────────────────────────────────────────────────────
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth.split(' ')[1]
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated
 
def make_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
 
# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/auth/register', methods=['POST'])
def register():
    data     = request.json
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
 
    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
 
    existing = query('SELECT id FROM users WHERE email = %s', (email,), fetchone=True)
    if existing:
        return jsonify({'error': 'Email already registered'}), 400
 
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = query(
        'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
        (name, email, hashed)
    )
    token = make_token(user_id)
    return jsonify({'token': token, 'user': {'id': user_id, 'name': name, 'email': email}}), 201
 
 
@app.route('/auth/login', methods=['POST'])
def login():
    data     = request.json
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
 
    user = query('SELECT * FROM users WHERE email = %s', (email,), fetchone=True)
    if not user or not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return jsonify({'error': 'Invalid email or password'}), 401
 
    token = make_token(user['id'])
    return jsonify({'token': token, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}})
 
 
@app.route('/auth/me', methods=['GET'])
@require_auth
def me():
    user = query('SELECT id, name, email FROM users WHERE id = %s', (request.user_id,), fetchone=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user})
 
# ── Products routes ───────────────────────────────────────────────────────────
@app.route('/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    if category:
        products = query('SELECT * FROM products WHERE category = %s', (category,), fetchall=True)
    else:
        products = query('SELECT * FROM products', fetchall=True)
    return jsonify({'products': products})
 
 
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query('SELECT * FROM products WHERE id = %s', (product_id,), fetchone=True)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'product': product})
 
# ── Payment routes ────────────────────────────────────────────────────────────
@app.route('/payment/create-intent', methods=['POST'])
@require_auth
def create_payment_intent():
    data     = request.json
    amount   = data.get('amount', 0)        # in INR (e.g. 1500)
    currency = data.get('currency', 'inr')
 
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
 
    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),           # Stripe expects paise for INR
        currency=currency,
        automatic_payment_methods={'enabled': True},
    )
    return jsonify({'clientSecret': intent.client_secret})
 
# ── Orders routes ─────────────────────────────────────────────────────────────
@app.route('/orders', methods=['POST'])
@require_auth
def create_order():
    data       = request.json
    items      = data.get('items', [])
    total      = data.get('total', 0)
    address    = data.get('address', '')
    payment_id = data.get('payment_id', '')
 
    if not items:
        return jsonify({'error': 'No items in order'}), 400
 
    order_id = query(
        'INSERT INTO orders (user_id, total_amount, delivery_address, payment_id, status) VALUES (%s, %s, %s, %s, %s)',
        (request.user_id, total, address, payment_id, 'confirmed')
    )
 
    for item in items:
        query(
            'INSERT INTO order_items (order_id, product_id, product_name, price, quantity) VALUES (%s, %s, %s, %s, %s)',
            (order_id, item.get('id'), item.get('name'), item.get('price'), item.get('qty', 1))
        )
 
    return jsonify({'order_id': order_id, 'status': 'confirmed'}), 201
 
 
@app.route('/orders', methods=['GET'])
@require_auth
def get_orders():
    orders = query(
        'SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC',
        (request.user_id,), fetchall=True
    )
    for order in orders:
        order['items'] = query(
            'SELECT * FROM order_items WHERE order_id = %s',
            (order['id'],), fetchall=True
        )
    return jsonify({'orders': orders})
 
# ── Stripe webhook ────────────────────────────────────────────────────────────
@app.route('/payment/webhook', methods=['POST'])
def stripe_webhook():
    payload   = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
 
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify({'error': 'Invalid webhook'}), 400
 
    if event['type'] == 'payment_intent.succeeded':
        pi = event['data']['object']
        print(f"Payment succeeded: {pi['id']}, amount: {pi['amount_received'] / 100}")
 
    return jsonify({'received': True})
 
# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'ShopEasy backend running'})
 
 
if __name__ == '__main__':
    app.run(debug=True, port=5000)
