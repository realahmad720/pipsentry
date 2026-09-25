export type Watchlist = {
  id: string;
  symbol: string;
  timeframe: string;
  active: boolean;
  forward_test_status: "not_started" | "running" | "passed" | "failed";
  forward_test_started_at: string | null;
  forward_test_ends_at: string | null;
};

export type ExecutionZones = {
  entry_range: [number, number];
  suggested_entry: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_reward_ratio: string;
};

export type AdvisoryPayload = {
  timestamp: string;
  user_id: string;
  symbol: string;
  timeframe: string;
  action: string;
  bias: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence_score: number;
  conflict_status: "NONE" | "CONFLICTED_REDUCED_SIZE";
  position_size_multiplier: number;
  execution_zones: ExecutionZones | null;
  rationale: {
    technical: string;
    macro_fundamental: string;
    strategy_match: string;
  };
  warnings: string[];
  disclaimer: string;
};

export type Advisory = {
  id: string;
  symbol: string;
  timeframe: string;
  action: string;
  confidence_score: number;
  payload_json: AdvisoryPayload;
  outcome: "open" | "tp1" | "tp2" | "sl" | "expired";
  outcome_at: string | null;
  delivered_at: string;
};

export type IngestedSourceStatus = "pending" | "indexed" | "failed";
export type IngestedSourceType = "youtube" | "pdf" | "txt";

export type IngestedSource = {
  id: string;
  source_type: IngestedSourceType;
  source_url: string | null;
  title: string | null;
  tags: string[];
  chunk_count: number;
  vector_collection_name: string;
  status: IngestedSourceStatus;
  created_at: string;
};

export type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

export type CalendarEvent = {
  title: string;
  country: string;
  impact: "Holiday" | "Low" | "Medium" | "High";
  event_time: string;
  forecast: number | null;
  previous: number | null;
  actual: number | null;
};

export type SentimentScore = {
  currency: string;
  score: number;
};

export type CurrencyStrength = Record<string, number>;

export type CorrelationMatrix = {
  pairs: string[];
  matrix: Record<string, Record<string, number>>;
};

export type SessionInfo = { name: string; open_hour_utc: number; close_hour_utc: number };

export type SessionClock = {
  utc_time: string;
  open_sessions: string[];
  overlaps: string[];
  sessions: SessionInfo[];
};

export type CotPositioning = {
  currency: string;
  market_name: string;
  report_date: string;
  noncommercial_long: number;
  noncommercial_short: number;
  noncommercial_net: number;
  commercial_long: number;
  commercial_short: number;
  open_interest: number;
};

export type BacktestTrade = {
  index: number;
  direction: string;
  entry: number;
  stop_loss: number;
  outcome: string;
  r_multiple: number;
};

export type BacktestResult = {
  trades: BacktestTrade[];
  win_rate: number;
  avg_r_multiple: number;
  max_drawdown_r: number;
  expectancy_r: number;
  passes_gate: boolean;
  gate_message: string;
};

export type Connector = {
  id: string;
  name: string;
  endpoint_url: string;
  category: "market_data" | "broker_readonly" | "news" | "custom";
  status: "unverified" | "healthy" | "unreachable" | "unauthorized";
  discovered_tools: { name: string; description: string | null }[];
  last_health_check_at: string | null;
  created_at: string;
};

export type TradeJournalEntry = {
  id: string;
  advisory_id: string | null;
  symbol: string;
  direction: "long" | "short";
  entry_price: number;
  exit_price: number | null;
  size: number;
  stop_loss: number | null;
  take_profit: number | null;
  pnl: number | null;
  notes: string | null;
  opened_at: string;
  closed_at: string | null;
};

export type Account = {
  id: string;
  email: string;
  plan_tier: string;
  telegram_linked: boolean;
  subscription: {
    plan: string;
    status: string;
    renewal_date: string | null;
    monthly_token_budget: number;
  } | null;
  month_to_date_tokens: number;
  today_usage: {
    usage_date: string;
    tokens_used: number;
    api_calls_made: number;
    cost_estimate_usd: number;
  } | null;
};
