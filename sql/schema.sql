CREATE TABLE saved_notes (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT,
 key_name VARCHAR(64),
 content TEXT,
 created_by BIGINT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME NULL,
 UNIQUE(chat_id,key_name)
);

CREATE TABLE approved_users (
 chat_id BIGINT,
 user_id BIGINT,
 username VARCHAR(64),
 full_name VARCHAR(128),
 approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(chat_id,user_id)
);

CREATE TABLE afk_status (
 chat_id BIGINT,
 user_id BIGINT,
 reason TEXT,
 since DATETIME,
 PRIMARY KEY(chat_id,user_id)
);

CREATE TABLE audit_log (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT,
 user_id BIGINT,
 action VARCHAR(32),
 target VARCHAR(128),
 metadata TEXT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reminders (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT,
 user_id BIGINT,
 message TEXT,
 remind_at DATETIME,
 sent BOOLEAN DEFAULT FALSE
);

CREATE TABLE todos (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT,
 task TEXT,
 created_by BIGINT,
 completed BOOLEAN DEFAULT FALSE,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE runbooks (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT,
 name VARCHAR(64),
 content TEXT,
 created_by BIGINT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(chat_id,name)
);

CREATE TABLE IF NOT EXISTS oncall_status (
 chat_id BIGINT PRIMARY KEY,
 user_id BIGINT,
 username TEXT,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS allowed_groups (
 chat_id BIGINT PRIMARY KEY,
 added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
