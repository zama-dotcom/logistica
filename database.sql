CREATE TYPE user_role AS ENUM ('BOSS', 'DISPATCH', 'PROMOTER', 'HELPER');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL, -- SHA-256 hash length is 64 hex characters
    role user_role NOT NULL
);

CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    lat DECIMAL(10, 8),
    lon DECIMAL(11, 8),
    phone VARCHAR(20),
    price_per_bag DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('PENDING', 'FINALIZED')) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    source VARCHAR(20) CHECK (source IN ('DISPATCH', 'PROMOTER')) NOT NULL
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(10, 2) NOT NULL,
    collector_name VARCHAR(100) NOT NULL,
    remaining_debt DECIMAL(10, 2) NOT NULL
);
