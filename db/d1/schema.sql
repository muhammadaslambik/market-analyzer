-- Skema Cloudflare D1 (SQLite). Aman dijalankan berulang kali (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS latest_price (
  market    TEXT NOT NULL,
  symbol    TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  close     REAL NOT NULL,
  asof      TEXT NOT NULL,
  source    TEXT NOT NULL,
  PRIMARY KEY (market, symbol, timeframe)
);

CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Disiapkan untuk fase berikutnya
CREATE TABLE IF NOT EXISTS latest_forecast (
  market        TEXT,
  symbol        TEXT,
  horizon       TEXT,
  p_up          REAL,
  q10           REAL,
  q50           REAL,
  q90           REAL,
  confidence    TEXT,
  status        TEXT,
  model_version TEXT,
  asof          TEXT,
  PRIMARY KEY (market, symbol, horizon)
);

CREATE TABLE IF NOT EXISTS latest_indicators (
  market    TEXT,
  symbol    TEXT,
  timeframe TEXT,
  indicator TEXT,
  signal    TEXT,
  weight    REAL,
  value     REAL,
  asof      TEXT,
  PRIMARY KEY (market, symbol, timeframe, indicator)
);
