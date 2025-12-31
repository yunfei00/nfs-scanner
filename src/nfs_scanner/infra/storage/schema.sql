-- 扫描任务
CREATE TABLE IF NOT EXISTS scan_task (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,          -- created/running/done/failed
  config_json TEXT NOT NULL,     -- 保存本次任务使用的配置（JSON）
  note TEXT DEFAULT ''
);

-- 扫描点位（可先不存全量，后续量大可分文件存）
CREATE TABLE IF NOT EXISTS scan_point (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  x REAL NOT NULL,
  y REAL NOT NULL,
  z REAL NOT NULL,
  value REAL,                    -- 先存一个示例值（后续可扩展多 trace）
  FOREIGN KEY(task_id) REFERENCES scan_task(id)
);

CREATE INDEX IF NOT EXISTS idx_scan_point_task_id ON scan_point(task_id);
