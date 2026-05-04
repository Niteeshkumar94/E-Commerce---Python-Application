-- ============================================================
--  ShopEasy — MySQL Database Schema
--  Run this file once:  mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS shopeasy;
USE shopeasy;

-- ── Users ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- ── Products ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150)   NOT NULL,
    description TEXT,
    price       DECIMAL(10,2)  NOT NULL,
    category    VARCHAR(80)    NOT NULL,
    icon        VARCHAR(10)    DEFAULT '📦',
    rating      VARCHAR(30)    DEFAULT '4.0',
    stock       INT            DEFAULT 100,
    created_at  DATETIME       DEFAULT CURRENT_TIMESTAMP
);

-- ── Orders ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT            NOT NULL,
    total_amount      DECIMAL(10,2)  NOT NULL,
    delivery_address  TEXT           NOT NULL,
    payment_id        VARCHAR(255),
    status            ENUM('pending','confirmed','shipped','delivered','cancelled')
                      DEFAULT 'pending',
    created_at        DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ── Order Items ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT            NOT NULL,
    product_id   INT,
    product_name VARCHAR(150)   NOT NULL,
    price        DECIMAL(10,2)  NOT NULL,
    quantity     INT            NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- ── Sample Products ────────────────────────────────────────
INSERT INTO products (name, description, price, category, icon, rating) VALUES
('Wireless Headphones',  'Over-ear noise cancelling headphones', 2499, 'Electronics', '🎧', '4.3 (1.2k)'),
('Laptop Stand',         'Adjustable aluminium laptop stand',    899,  'Electronics', '💻', '4.5 (876)'),
('Bluetooth Speaker',    'Portable waterproof speaker',          1799, 'Electronics', '🔊', '4.1 (543)'),
('USB-C Hub',            '7-in-1 USB-C hub with HDMI',           1299, 'Electronics', '🔌', '4.4 (321)'),
('Phone Case',           'Shockproof clear phone case',          299,  'Mobiles',     '📱', '4.2 (2.1k)'),
('Fast Charger 65W',     'GaN 65W fast charger',                 699,  'Mobiles',     '⚡', '4.6 (1.4k)'),
('Power Bank 20000mAh',  'Slim 20000mAh power bank',             1499, 'Mobiles',     '🔋', '4.3 (765)'),
('Cotton T-Shirt',       '100% organic cotton round neck',       499,  'Clothing',    '👕', '4.4 (3.2k)'),
('Denim Jeans',          'Slim fit stretch denim',               1299, 'Clothing',    '👖', '4.2 (1.8k)'),
('Running Sneakers',     'Lightweight running shoes',            2999, 'Clothing',    '👟', '4.5 (987)'),
('Coffee Mug 350ml',     'Ceramic mug with lid',                 349,  'Kitchen',     '☕', '4.6 (4.5k)'),
('Stainless Water Bottle','1L insulated bottle',                 599,  'Kitchen',     '🍶', '4.4 (2.3k)'),
('Yoga Mat 6mm',         'Non-slip TPE yoga mat',                699,  'Sports',      '🧘', '4.3 (1.5k)'),
('Dumbbells 5kg Pair',   'Rubber coated dumbbell set',           999,  'Sports',      '🏋️', '4.4 (987)'),
('Atomic Habits',        'James Clear — habits guide',           449,  'Books',       '📘', '4.9 (8.2k)'),
('Clean Code',           'Robert C. Martin — coding best practices', 599, 'Books',   '📗', '4.8 (5.6k)'),
('LEGO Classic Set',     '500-piece creative building set',      1999, 'Toys',        '🧱', '4.7 (2.3k)'),
('Sunscreen SPF50',      'Lightweight daily sunscreen',          399,  'Beauty',      '🧴', '4.4 (3.2k)');

