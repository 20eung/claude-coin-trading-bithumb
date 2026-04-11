-- 암호화폐 자동매매 시스템 SQLite 스키마
-- Supabase → SQLite 마이그레이션용

-- 1. 매매 결정 기록
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  market TEXT NOT NULL DEFAULT 'KRW-BTC',
  decision TEXT NOT NULL CHECK (decision IN ('매수', '매도', '관망')),
  confidence REAL,
  reason TEXT NOT NULL,
  market_data_snapshot TEXT,
  fear_greed_value INTEGER,
  rsi_value REAL,
  current_price INTEGER,
  sma20_price INTEGER,
  trade_amount INTEGER,
  trade_volume REAL,
  executed INTEGER DEFAULT 0,
  execution_result TEXT,
  profit_loss REAL,
  created_at TEXT DEFAULT (datetime('now', '+9 hours'))
);

CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_market ON decisions(market);
CREATE INDEX IF NOT EXISTS idx_decisions_decision ON decisions(decision);

-- 2. 포트폴리오 스냅샷
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
  id TEXT PRIMARY KEY,
  total_krw INTEGER NOT NULL,
  total_crypto_value INTEGER NOT NULL,
  total_value INTEGER NOT NULL,
  holdings TEXT NOT NULL,
  daily_return REAL,
  cumulative_return REAL,
  created_at TEXT DEFAULT (datetime('now', '+9 hours'))
);

CREATE INDEX IF NOT EXISTS idx_portfolio_created_at ON portfolio_snapshots(created_at DESC);

-- 3. 시장 데이터 기록
CREATE TABLE IF NOT EXISTS market_data (
  id TEXT PRIMARY KEY,
  market TEXT NOT NULL DEFAULT 'KRW-BTC',
  price INTEGER NOT NULL,
  volume_24h REAL,
  change_rate_24h REAL,
  fear_greed_value INTEGER,
  fear_greed_class TEXT,
  rsi_14 REAL,
  sma_20 INTEGER,
  news_sentiment TEXT,
  created_at TEXT DEFAULT (datetime('now', '+9 hours'))
);

CREATE INDEX IF NOT EXISTS idx_market_data_created_at ON market_data(created_at DESC);

-- 4. 사용자 피드백
CREATE TABLE IF NOT EXISTS feedback (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('parameter_change', 'behavior_change', 'one_time', 'general')),
  content TEXT NOT NULL,
  applied INTEGER DEFAULT 0,
  applied_at TEXT,
  expires_at TEXT,
  created_at TEXT DEFAULT (datetime('now', '+9 hours'))
);

CREATE INDEX IF NOT EXISTS idx_feedback_applied ON feedback(applied);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(type);

-- 5. 실행 로그
CREATE TABLE IF NOT EXISTS execution_logs (
  id TEXT PRIMARY KEY,
  execution_mode TEXT NOT NULL CHECK (execution_mode IN ('analyze', 'execute', 'dry_run')),
  decision_id TEXT,
  duration_ms INTEGER,
  data_sources TEXT,
  errors TEXT,
  raw_output TEXT,
  created_at TEXT DEFAULT (datetime('now', '+9 hours')),
  FOREIGN KEY (decision_id) REFERENCES decisions(id)
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at DESC);

-- 6. 전략 변경 이력
CREATE TABLE IF NOT EXISTS strategy_history (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  content TEXT NOT NULL,
  change_summary TEXT,
  changed_by TEXT DEFAULT 'user',
  created_at TEXT DEFAULT (datetime('now', '+9 hours'))
);

CREATE INDEX IF NOT EXISTS idx_strategy_history_version ON strategy_history(version DESC);
