CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, nim TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE found_items (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), item_name TEXT NOT NULL, category TEXT NOT NULL,
  description TEXT NOT NULL, location TEXT NOT NULL, date_found TEXT NOT NULL, time_found TEXT NOT NULL, photo TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Menunggu Penyerahan' CHECK (status IN ('Menunggu Penyerahan','Tersimpan di Satpam','Dikembalikan')),
  received_by INTEGER REFERENCES users(id), received_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE lost_items (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), item_name TEXT NOT NULL, category TEXT NOT NULL,
  description TEXT NOT NULL, location TEXT NOT NULL, date_lost TEXT NOT NULL, time_lost TEXT NOT NULL, photo TEXT,
  status TEXT NOT NULL DEFAULT 'Hilang' CHECK (status IN ('Hilang','Sudah Ditemukan')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE item_returns (id INTEGER PRIMARY KEY AUTOINCREMENT, found_item_id INTEGER NOT NULL UNIQUE REFERENCES found_items(id),
  owner_id INTEGER REFERENCES users(id), owner_name TEXT NOT NULL, owner_identity TEXT NOT NULL, proof_notes TEXT NOT NULL,
  officer_id INTEGER NOT NULL REFERENCES users(id), return_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Dikembalikan');
CREATE TABLE password_reset_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), token_hash TEXT NOT NULL UNIQUE,
  expires_at TEXT NOT NULL, used INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), sender_name TEXT NOT NULL, sender_email TEXT NOT NULL,
  category TEXT NOT NULL, subject TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, email_status TEXT NOT NULL DEFAULT 'pending');
