import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.stock_model import (
    ProfileResponse,
    QuoteResponse,
    GrowthResponse,
    PricesResponse,
    IntrinsicValueRequest,
    IntrinsicValueResponse,
    EpsGrowthForecastRequest,
    EpsGrowthForecastResponse,
)
from services import yahoo_service

app = FastAPI()

# Browsers (Flutter web / devtools) require CORS to read JSON; Postman does not.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Stock intrinsic value API"}


@app.get("/profile/{ticker}", response_model=ProfileResponse)
def profile(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_profile(ticker)


@app.get("/quote/{ticker}", response_model=QuoteResponse)
def quote(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_quote(ticker)


@app.get("/prices/{ticker}", response_model=PricesResponse)
def prices(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_prices(ticker)


@app.get("/financials/income/{ticker}")
def income(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_income_statement(ticker)


@app.get("/financials/cashflow/{ticker}")
def cashflow(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_cashflow(ticker)


@app.get("/financials/balance/{ticker}")
def balance(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_balance_sheet(ticker)


@app.get("/earnings/{ticker}")
def earnings(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_earnings(ticker)


@app.get("/growth/{ticker}", response_model=GrowthResponse)
def growth(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    return yahoo_service.get_growth(ticker)


@app.post("/eps-growth-forecast", response_model=EpsGrowthForecastResponse)
def eps_growth_forecast(payload: EpsGrowthForecastRequest):
    """Per-year EPS growth % (not decimals), derived from Yahoo growth/CAGR; proxy for AI forecast."""
    if payload.years <= 0 or payload.years > 30:
        raise HTTPException(status_code=400, detail="years must be 1–30")
    ticker = (payload.ticker or "").strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    raw = yahoo_service.get_growth(ticker)
    rate = raw.get("epsGrowth")
    if rate is None or (isinstance(rate, float) and (math.isnan(rate) or math.isinf(rate))):
        base_pct = 5.0
    else:
        try:
            base_pct = float(rate) * 100.0
        except (TypeError, ValueError):
            base_pct = 5.0
    base_pct = max(0.1, min(100.0, base_pct))
    values = [max(0.1, base_pct * (0.98**i)) for i in range(payload.years)]
    return {"eps_expected_growth_5y": values}


@app.post("/intrinsic-value", response_model=IntrinsicValueResponse)
def intrinsic_value(payload: IntrinsicValueRequest):
    if payload.years <= 0:
        raise HTTPException(status_code=400, detail="Years must be > 0")
    if payload.eps <= 0:
        raise HTTPException(status_code=400, detail="EPS must be > 0")
    future_eps = payload.eps * ((1 + payload.growth) ** payload.years)
    terminal_value = future_eps * payload.pe
    return {"intrinsicValue": terminal_value}
