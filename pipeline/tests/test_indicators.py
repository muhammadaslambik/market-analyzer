"""Tes tugas 1.3: indikator kausal (shift 1), warm-up NaN, tanpa look-ahead."""
import numpy as np
import pandas as pd

from analyzer.indicators import bollinger, build_features, macd, rsi, vwap


def make_ohlcv(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = 100.0 + np.cumsum(rng.normal(scale=1.0, size=n))
    spread = np.abs(rng.normal(scale=0.5, size=n)) + 0.1
    idx = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {
            "open": close - spread / 2,
            "high": close + spread / 2,
            "low": close - spread / 2,
            "close": close,
            "volume": rng.uniform(100, 1000, size=n),
        },
        index=idx,
    )


def rsi_unshifted_helper(close: pd.Series) -> pd.Series:
    """RSI tanpa shift, untuk verifikasi output rsi() memang di-shift 1."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.mask(avg_loss.eq(0) & avg_gain.gt(0) & avg_gain.notna(), 100.0)


class TestRSI:
    def test_warmup_is_nan(self):
        out = rsi(pd.Series(np.arange(1.0, 41.0)))
        # warm-up 14 bar + shift 1 → valid mulai index 15
        assert out.iloc[:15].isna().all()
        assert out.iloc[15:].notna().all()

    def test_bounded(self):
        out = rsi(make_ohlcv(200)["close"])
        valid = out.dropna()
        assert ((valid >= 0) & (valid <= 100)).all()

    def test_pure_uptrend_is_100_not_fake_fillna(self):
        out = rsi(pd.Series(np.linspace(100, 140, 60)))
        valid = out.dropna()
        assert (valid == 100.0).all()

    def test_pure_downtrend_is_0(self):
        out = rsi(pd.Series(np.linspace(140, 100, 60)))
        assert (out.dropna() == 0.0).all()

    def test_output_is_shifted(self):
        rng = np.random.default_rng(7)
        s = pd.Series(100 + np.cumsum(rng.normal(size=60)))
        out = rsi(s)
        manual = rsi_unshifted_helper(s)
        # out[t] == manual[t-1]  →  bandingkan out.shift(-1) dengan manual
        pd.testing.assert_series_equal(out.shift(-1).iloc[15:40],
                                       manual.iloc[15:40], check_names=False)


class TestMACD:
    def test_warmup_is_nan(self):
        out = macd(make_ohlcv(120)["close"])
        assert out["macd"].iloc[:26].isna().all()
        assert out["macd"].iloc[26:].notna().all()
        assert out["macd_signal"].iloc[:34].isna().all()
        assert out["macd_signal"].iloc[35:].notna().all()

    def test_columns(self):
        out = macd(make_ohlcv(120)["close"])
        assert set(out.columns) == {"macd", "macd_signal", "macd_hist"}


class TestBollinger:
    def test_warmup_is_nan(self):
        out = bollinger(make_ohlcv(120)["close"])
        assert out["bb_mid"].iloc[:20].isna().all()
        assert out["bb_mid"].iloc[20:].notna().all()

    def test_pct_b_bounded(self):
        out = bollinger(make_ohlcv(200)["close"])
        valid = out["bb_pct_b"].dropna()
        assert valid.abs().max() < 10.0

    def test_columns(self):
        out = bollinger(make_ohlcv(120)["close"])
        assert set(out.columns) == {
            "bb_mid", "bb_upper", "bb_lower", "bb_bandwidth", "bb_pct_b",
        }


class TestVWAP:
    def test_shifted_first_bar_nan(self):
        df = make_ohlcv(48)  # index per jam → 2 hari kalender
        out = vwap(df)
        assert pd.isna(out.iloc[0])  # shift → bar pertama NaN
        p0 = (df["high"].iloc[0] + df["low"].iloc[0] + df["close"].iloc[0]) / 3
        assert np.isclose(out.iloc[1], p0)

    def test_resets_at_new_day(self):
        df = make_ohlcv(48)
        out = vwap(df)
        # bar 24 = bar pertama hari ke-2; nilai shifted-nya = vwap
        # kumulatif seluruh hari 1 (bar 0..23)
        p = ((df["high"] + df["low"] + df["close"]) / 3).iloc[:24]
        v = df["volume"].iloc[:24]
        expected = (p * v).sum() / v.sum()
        assert np.isclose(out.iloc[24], expected)


class TestBuildFeatures:
    def test_columns_and_no_raw_price(self):
        feats = build_features(make_ohlcv(120))
        expected = {
            "rsi_14", "ret_1", "ret_6", "ret_24",
            "macd", "macd_signal", "macd_hist",
            "bb_mid", "bb_upper", "bb_lower", "bb_bandwidth", "bb_pct_b",
            "vwap_dist",
        }
        assert set(feats.columns) == expected
        for col in ["open", "high", "low", "close", "volume"]:
            assert col not in feats.columns

    def test_no_lookahead_in_returns(self):
        # ret_1 di bar t harus = (c[t-1]/c[t-2]) - 1 (dua kali shift)
        df = make_ohlcv(60)
        feats = build_features(df)
        c = df["close"]
        expected = c.shift(1) / c.shift(2) - 1.0
        pd.testing.assert_series_equal(feats["ret_1"], expected,
                                       check_names=False)

    def test_warmup_rows_are_nan_then_valid(self):
        feats = build_features(make_ohlcv(160))
        # warm-up terlama: macd_signal (slow+signal+shift) ≈ 35 bar
        assert feats.iloc[:34].isna().any(axis=1).all()
        assert feats.iloc[40:].notna().all().all()
