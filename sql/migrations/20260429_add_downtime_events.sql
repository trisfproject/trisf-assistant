CREATE TABLE IF NOT EXISTS downtime_events (
 id INT AUTO_INCREMENT PRIMARY KEY,
 chat_id BIGINT NOT NULL,
 service VARCHAR(255) NOT NULL,
 note TEXT NULL,
 reported_by BIGINT NOT NULL,
 resolved_by BIGINT NULL,
 started_at DATETIME NOT NULL,
 ended_at DATETIME NULL,
 status VARCHAR(20) DEFAULT 'open',
 INDEX(chat_id),
 INDEX(service),
 INDEX(status)
);
