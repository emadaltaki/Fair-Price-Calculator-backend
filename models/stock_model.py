from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ProfileResponse(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    marketCap: Optional[int] = None


class QuoteResponse(BaseModel):
    price: Optional[float] = None
    pe: Optional[float] = None
    eps: Optional[float] = None
    volume: Optional[int] = None


class GrowthResponse(BaseModel):
    epsGrowth: Optional[float] = None


class PricesResponse(BaseModel):
    prices: List[Dict[str, Any]]


class IntrinsicValueRequest(BaseModel):
    eps: float
    growth: float
    pe: float
    years: int


class IntrinsicValueResponse(BaseModel):
    intrinsicValue: float


class EpsGrowthForecastRequest(BaseModel):
    ticker: str
    years: int = 5


class EpsGrowthForecastResponse(BaseModel):
    eps_expected_growth_5y: List[float]
