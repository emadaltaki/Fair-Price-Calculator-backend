from __future__ import annotations

import math
from typing import Any, Dict
from datetime import datetime, timedelta

import yfinance as yf


def _sanitize_for_json(obj: Any) -> Any:
    """Make values JSON-serializable: NaN/Inf -> None, numpy scalars -> Python types."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {_json_dict_key(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, int) and not isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else obj
    try:
        import numpy as np

        if isinstance(obj, np.generic):
            if isinstance(obj, np.floating):
                val = float(obj)
                return None if math.isnan(val) or math.isinf(val) else val
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.bool_):
                return bool(obj)
    except ImportError:
        pass
    if hasattr(obj, "isoformat") and not isinstance(obj, str):
        try:
            return obj.isoformat()
        except (TypeError, ValueError, AttributeError):
            pass
    return obj


def _json_dict_key(k: Any) -> str:
    if isinstance(k, str):
        return k
    if hasattr(k, "isoformat"):
        try:
            return k.isoformat()
        except (TypeError, ValueError, AttributeError):
            pass
    return str(k)


_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = timedelta(minutes=10)


def _cache_key(prefix: str, ticker: str) -> str:
    return f"{prefix}:{ticker.upper()}"


def _get_cached(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at = entry.get("expires_at")
    if expires_at and expires_at < datetime.utcnow():
        _CACHE.pop(key, None)
        return None
    return entry.get("value")


def _set_cached(key: str, value: Any) -> None:
    _CACHE[key] = {
        "value": value,
        "expires_at": datetime.utcnow() + _CACHE_TTL,
    }


def _get_ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker.upper())


def get_profile(ticker: str) -> Dict[str, Any]:
    key = _cache_key("profile", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    info = _get_ticker(ticker).info or {}
    result = {
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "website": info.get("website"),
        "employees": info.get("fullTimeEmployees"),
        "marketCap": info.get("marketCap"),
    }
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_quote(ticker: str) -> Dict[str, Any]:
    key = _cache_key("quote", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    info = _get_ticker(ticker).info or {}
    result = {
        "price": info.get("currentPrice"),
        "pe": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
        "volume": info.get("volume"),
    }
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_prices(ticker: str) -> Dict[str, Any]:
    key = _cache_key("prices", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    history = _get_ticker(ticker).history(period="10y")
    result = {
        "prices": history.reset_index().to_dict(orient="records"),
    }
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_income_statement(ticker: str) -> Dict[str, Any]:
    key = _cache_key("income", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    income = _get_ticker(ticker).financials
    result = income.to_dict() if income is not None else {}
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_cashflow(ticker: str) -> Dict[str, Any]:
    key = _cache_key("cashflow", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    cashflow = _get_ticker(ticker).cashflow
    result = cashflow.to_dict() if cashflow is not None else {}
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_balance_sheet(ticker: str) -> Dict[str, Any]:
    key = _cache_key("balance", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    balance = _get_ticker(ticker).balance_sheet
    result = balance.to_dict() if balance is not None else {}
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_earnings(ticker: str) -> Dict[str, Any]:
    key = _cache_key("earnings", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    earnings = _get_ticker(ticker).earnings
    result = earnings.to_dict() if earnings is not None else {}
    _set_cached(key, result)
    return _sanitize_for_json(result)


def get_growth(ticker: str) -> Dict[str, Any]:
    key = _cache_key("growth", ticker)
    cached = _get_cached(key)
    if cached is not None:
        return _sanitize_for_json(cached)
    stock = _get_ticker(ticker)
    earnings = stock.earnings
    if earnings is None or earnings.empty:
        info = stock.info or {}
        result = {"epsGrowth": info.get("earningsGrowth")}
        _set_cached(key, result)
        return _sanitize_for_json(result)
    eps = earnings["Earnings"]
    if eps.empty:
        info = stock.info or {}
        result = {"epsGrowth": info.get("earningsGrowth")}
        _set_cached(key, result)
        return _sanitize_for_json(result)
    first = eps.iloc[0]
    last = eps.iloc[-1]
    years = len(eps)
    if first == 0 or years <= 1:
        info = stock.info or {}
        result = {"epsGrowth": info.get("earningsGrowth")}
        _set_cached(key, result)
        return _sanitize_for_json(result)
    cagr = (last / first) ** (1 / years) - 1
    result = {"epsGrowth": cagr}
    _set_cached(key, result)
    return _sanitize_for_json(result)
