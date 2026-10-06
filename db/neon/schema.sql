-- Skema Neon (Postgres). Aman dijalankan berulang kali (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS candles (
  market      text             NOT NULL,           -- 'crypto'
  symbol      text             NOT NULL,           -- mis. 'BTCUSDT'
  timeframe   text             NOT NULL,           -- '1h' atau '1d'
  ts          timestamptz      NOT NULL,           -- waktu BUKA candle, UTC
  open        double precision NOT NULL,
  high        double precision NOT NULL,
  low         double precision NOT NULL,
  close       double precision NOT NULL,
  volume      double precision NOT NULL,
  source      text             NOT NULL,
  ingested_at timestamptz      NOT NULL DEFAULT now(),
  PRIMARY KEY (market, symbol, timeframe, ts)
);

CREATE TABLE IF NOT EXISTS ingest_runs (
  id           bigserial PRIMARY KEY,
  job          text        NOT NULL,
  started_at   timestamptz NOT NULL,
  finished_at  timestamptz,
  status       text        NOT NULL,               -- 'ok', 'partial', atau 'error'
  rows_written integer     NOT NULL DEFAULT 0,
  api_calls    integer     NOT NULL DEFAULT 0,
  error        text
);

CREATE TABLE IF NOT EXISTS data_quality_log (
  id        bigserial PRIMARY KEY,
  market    text,
  symbol    text,
  timeframe text,
  ts        timestamptz,
  issue     text        NOT NULL,                  -- gap, duplicate, ohlc_invalid, outlier, not_closed
  detail    jsonb,
  logged_at timestamptz NOT NULL DEFAULT now()
);

-- Disiapkan untuk Fase 1 (dibuat sekarang, belum diisi)
CREATE TABLE IF NOT EXISTS predictions (
  id            bigserial PRIMARY KEY,
  market        text,
  symbol        text,
  horizon       text,
  issued_at     timestamptz,
  due_at        timestamptz,
  p_up          double precision,
  q10           double precision,
  q50           double precision,
  q90           double precision,
  model_version text,
  features_hash text
);

CREATE TABLE IF NOT EXISTS outcomes (
  prediction_id   bigint PRIMARY KEY REFERENCES predictions(id),
  realized_return double precision,
  direction_hit   boolean,
  interval_hit    boolean,
  scored_at       timestamptz
);

CREATE TABLE IF NOT EXISTS model_runs (
  version      text,
  market       text,
  horizon      text,
  metrics_json jsonb,
  passed_gate  boolean,
  created_at   timestamptz DEFAULT now()
);
ALTER TABLE model_runs ADD COLUMN IF NOT EXISTS symbol text;
ALTER TABLE model_runs ADD COLUMN IF NOT EXISTS timeframe text;
ALTER TABLE model_runs ADD COLUMN IF NOT EXISTS artifact jsonb;
CREATE UNIQUE INDEX IF NOT EXISTS predictions_uniq
  ON predictions (market, symbol, horizon, issued_at, model_version);
CREATE INDEX IF NOT EXISTS predictions_due ON predictions (due_at);
