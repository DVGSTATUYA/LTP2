PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  fio TEXT NOT NULL,
  phone TEXT,
  login TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL -- Менеджер, Специалист, Оператор, Заказчик
);

CREATE TABLE IF NOT EXISTS requests (
  request_id INTEGER PRIMARY KEY,
  start_date TEXT NOT NULL,
  climate_tech_type TEXT NOT NULL,
  climate_tech_model TEXT,
  problem_description TEXT,
  request_status TEXT NOT NULL,
  completion_date TEXT,
  repair_parts TEXT,
  master_id INTEGER,
  client_id INTEGER NOT NULL,
  FOREIGN KEY(master_id) REFERENCES users(user_id) ON DELETE SET NULL,
  FOREIGN KEY(client_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS comments (
  comment_id INTEGER PRIMARY KEY,
  message TEXT NOT NULL,
  master_id INTEGER,
  request_id INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(master_id) REFERENCES users(user_id) ON DELETE SET NULL,
  FOREIGN KEY(request_id) REFERENCES requests(request_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(request_status);
CREATE INDEX IF NOT EXISTS idx_requests_client ON requests(client_id);
CREATE INDEX IF NOT EXISTS idx_requests_master ON requests(master_id);
