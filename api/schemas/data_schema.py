"""api/schemas/data_schema.py – Pydantic models for data endpoints."""
from __future__ import annotations
from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DownloadRequest(BaseModel):
    tickers:    List[str]   = Field(..., min_length=1)
    start_date: str         = Field("2004-01-01")
    end_date:   str         = Field(default_factory=lambda: str(date.today()))
    force:      bool        = False

    @field_validator("tickers")
    @classmethod
    def tickers_upper(cls, v):
        return [t.upper().strip() for t in v]


class TickerInfo(BaseModel):
    ticker:    str
    rows:      int
    start:     Optional[str]
    end:       Optional[str]
    columns:   List[str]
    close_last:Optional[float]


class DownloadResponse(BaseModel):
    success:     List[str]
    failed:      List[str]
    total:       int
    message:     str


class OHLCVBar(BaseModel):
    date:   str
    open:   float
    high:   float
    low:    float
    close:  float
    volume: float


class PriceResponse(BaseModel):
    ticker:  str
    data:    List[OHLCVBar]
    rows:    int
    start:   Optional[str]
    end:     Optional[str]


class UniverseResponse(BaseModel):
    name:    str
    tickers: List[str]
    count:   int


class SectorBreakdownResponse(BaseModel):
    universe: str
    sectors:  Dict[str, List[str]]
