from fastapi import APIRouter, Depends

from app.backtest.gate import passes_expectancy_gate
from app.backtest.harness import run_backtest
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.backtest import BacktestRequest, BacktestResult

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResult)
def run_backtest_endpoint(body: BacktestRequest, user: User = Depends(get_current_user)) -> BacktestResult:
    scorecard = run_backtest(body.symbol, body.timeframe, body.start_date, body.end_date)
    ok, message = passes_expectancy_gate(scorecard)
    return BacktestResult(
        trades=[t.__dict__ for t in scorecard.trades],
        win_rate=scorecard.win_rate,
        avg_r_multiple=scorecard.avg_r_multiple,
        max_drawdown_r=scorecard.max_drawdown_r,
        expectancy_r=scorecard.expectancy_r,
        passes_gate=ok,
        gate_message=message,
    )
