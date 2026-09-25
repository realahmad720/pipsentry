from pydantic import BaseModel


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    start_date: str  # "YYYY-MM-DD"
    end_date: str


class GradedTradeOut(BaseModel):
    index: int
    direction: str
    entry: float
    stop_loss: float
    outcome: str
    r_multiple: float


class BacktestResult(BaseModel):
    trades: list[GradedTradeOut]
    win_rate: float
    avg_r_multiple: float
    max_drawdown_r: float
    expectancy_r: float
    passes_gate: bool
    gate_message: str
