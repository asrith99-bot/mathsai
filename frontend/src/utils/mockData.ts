/**
 * Realistic mock / demo data for all pages.
 * Used when the backend has no signals yet (market closed, first run, etc.)
 * All prices are realistic NSE values as of late 2026.
 */
import type { Signal, ScannerRow, OHLCVBar, BacktestResult, ModelVersion, DashboardStats } from '../types';

const now = new Date();
const ts  = (minutesAgo: number) => new Date(now.getTime() - minutesAgo * 60_000).toISOString();

// ─── Mock Signals ────────────────────────────────────────────
export const MOCK_SIGNALS: Signal[] = [
  { id:1,  symbol:'RELIANCE',  signal_type:'BUY',  confidence:0.82, entry_price:1342,   stop_loss:1318,   target_price:1390,  rr_ratio:2.0, risk_per_share:24,  reward_per_share:48,  rsi:48.2, macd:3.4,  atr:18.5, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(4)  },
  { id:2,  symbol:'TCS',       signal_type:'SELL', confidence:0.76, entry_price:2410,   stop_loss:2450,   target_price:2330,  rr_ratio:2.0, risk_per_share:40,  reward_per_share:80,  rsi:72.1, macd:-5.2, atr:28.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(7)  },
  { id:3,  symbol:'INFY',      signal_type:'BUY',  confidence:0.71, entry_price:1144,   stop_loss:1122,   target_price:1188,  rr_ratio:2.0, risk_per_share:22,  reward_per_share:44,  rsi:44.8, macd:1.8,  atr:15.2, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(12) },
  { id:4,  symbol:'HDFCBANK',  signal_type:'HOLD', confidence:0.63, entry_price:806,    stop_loss:790,    target_price:838,   rr_ratio:2.0, risk_per_share:16,  reward_per_share:32,  rsi:53.5, macd:0.5,  atr:11.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(15) },
  { id:5,  symbol:'ICICIBANK', signal_type:'BUY',  confidence:0.79, entry_price:1586,   stop_loss:1554,   target_price:1650,  rr_ratio:2.0, risk_per_share:32,  reward_per_share:64,  rsi:41.3, macd:4.1,  atr:22.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(18) },
  { id:6,  symbol:'BHARTIARTL',signal_type:'BUY',  confidence:0.74, entry_price:2108,   stop_loss:2066,   target_price:2192,  rr_ratio:2.0, risk_per_share:42,  reward_per_share:84,  rsi:46.0, macd:6.2,  atr:30.5, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(22) },
  { id:7,  symbol:'WIPRO',     signal_type:'SELL', confidence:0.68, entry_price:195,    stop_loss:201,    target_price:183,   rr_ratio:2.0, risk_per_share:6,   reward_per_share:12,  rsi:68.4, macd:-2.1, atr:4.2,  model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(25) },
  { id:8,  symbol:'SBIN',      signal_type:'BUY',  confidence:0.77, entry_price:1082,   stop_loss:1060,   target_price:1126,  rr_ratio:2.0, risk_per_share:22,  reward_per_share:44,  rsi:40.1, macd:3.8,  atr:16.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(30) },
  { id:9,  symbol:'TITAN',     signal_type:'SELL', confidence:0.72, entry_price:4848,   stop_loss:4944,   target_price:4656,  rr_ratio:2.0, risk_per_share:96,  reward_per_share:192, rsi:71.8, macd:-8.5, atr:68.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(35) },
  { id:10, symbol:'LT',        signal_type:'BUY',  confidence:0.80, entry_price:4146,   stop_loss:4062,   target_price:4314,  rr_ratio:2.0, risk_per_share:84,  reward_per_share:168, rsi:43.5, macd:5.0,  atr:60.0, model_version:'xgboost_demo', data_source:'yahoo', freshness:'DELAYED', is_active:true, generated_at:ts(40) },
];

// ─── Mock Scanner Rows ───────────────────────────────────────
export const MOCK_SCANNER_ROWS: ScannerRow[] = [
  { symbol:'RELIANCE',   name:'Reliance Industries',          sector:'Energy',         ltp:1339.7,   change_pct:0.02,  volume:512357,  rsi:48.2, macd:3.4,  signal_type:'BUY',  confidence:0.82, entry_price:1342,  stop_loss:1318,  target_price:1390, freshness:'DELAYED' },
  { symbol:'TCS',        name:'Tata Consultancy Services',    sector:'Technology',     ltp:2407.5,   change_pct:-1.43, volume:87081,   rsi:72.1, macd:-5.2, signal_type:'SELL', confidence:0.76, entry_price:2410,  stop_loss:2450,  target_price:2330, freshness:'DELAYED' },
  { symbol:'INFY',       name:'Infosys Ltd',                  sector:'Technology',     ltp:1141.5,   change_pct:-0.84, volume:392643,  rsi:44.8, macd:1.8,  signal_type:'BUY',  confidence:0.71, entry_price:1144,  stop_loss:1122,  target_price:1188, freshness:'DELAYED' },
  { symbol:'HDFCBANK',   name:'HDFC Bank Ltd',                sector:'Banking',        ltp:804.0,    change_pct:-1.02, volume:1362429, rsi:53.5, macd:0.5,  signal_type:'HOLD', confidence:0.63, entry_price:806,   stop_loss:790,   target_price:838,  freshness:'DELAYED' },
  { symbol:'ICICIBANK',  name:'ICICI Bank Ltd',               sector:'Banking',        ltp:1583.6,   change_pct:-0.40, volume:1347798, rsi:41.3, macd:4.1,  signal_type:'BUY',  confidence:0.79, entry_price:1586,  stop_loss:1554,  target_price:1650, freshness:'DELAYED' },
  { symbol:'SBIN',       name:'State Bank of India',          sector:'Banking',        ltp:1080.0,   change_pct:-0.60, volume:372523,  rsi:40.1, macd:3.8,  signal_type:'BUY',  confidence:0.77, entry_price:1082,  stop_loss:1060,  target_price:1126, freshness:'DELAYED' },
  { symbol:'BHARTIARTL', name:'Bharti Airtel Ltd',            sector:'Telecom',        ltp:2106.0,   change_pct:0.48,  volume:490256,  rsi:46.0, macd:6.2,  signal_type:'BUY',  confidence:0.74, entry_price:2108,  stop_loss:2066,  target_price:2192, freshness:'DELAYED' },
  { symbol:'ITC',        name:'ITC Ltd',                      sector:'FMCG',           ltp:285.0,    change_pct:0.33,  volume:257944,  rsi:55.2, macd:1.1,  signal_type:'HOLD', confidence:0.58, entry_price:285,   stop_loss:279,   target_price:297,  freshness:'DELAYED' },
  { symbol:'LT',         name:'Larsen & Toubro Ltd',          sector:'Infrastructure', ltp:4143.8,   change_pct:-0.37, volume:20128,   rsi:43.5, macd:5.0,  signal_type:'BUY',  confidence:0.80, entry_price:4146,  stop_loss:4062,  target_price:4314, freshness:'DELAYED' },
  { symbol:'AXISBANK',   name:'Axis Bank Ltd',                sector:'Banking',        ltp:1331.0,   change_pct:-0.89, volume:195506,  rsi:38.9, macd:2.3,  signal_type:'BUY',  confidence:0.69, entry_price:1333,  stop_loss:1306,  target_price:1387, freshness:'DELAYED' },
  { symbol:'KOTAKBANK',  name:'Kotak Mahindra Bank',          sector:'Banking',        ltp:488.5,    change_pct:-0.38, volume:403068,  rsi:50.1, macd:-0.8, signal_type:'HOLD', confidence:0.55, entry_price:490,   stop_loss:480,   target_price:510,  freshness:'DELAYED' },
  { symbol:'BAJFINANCE', name:'Bajaj Finance Ltd',            sector:'Finance',        ltp:1117.0,   change_pct:0.18,  volume:229604,  rsi:47.5, macd:2.9,  signal_type:'BUY',  confidence:0.70, entry_price:1120,  stop_loss:1097,  target_price:1166, freshness:'DELAYED' },
  { symbol:'MARUTI',     name:'Maruti Suzuki India',          sector:'Automobile',     ltp:12854.0,  change_pct:-1.31, volume:12010,   rsi:36.2, macd:8.5,  signal_type:'BUY',  confidence:0.73, entry_price:12880, stop_loss:12622, target_price:13396,freshness:'DELAYED' },
  { symbol:'SUNPHARMA',  name:'Sun Pharma Industries',        sector:'Pharma',         ltp:1880.0,   change_pct:-0.27, volume:285263,  rsi:51.0, macd:1.2,  signal_type:'HOLD', confidence:0.60, entry_price:1882,  stop_loss:1844,  target_price:1958, freshness:'DELAYED' },
  { symbol:'TITAN',      name:'Titan Company Ltd',            sector:'Consumer',       ltp:4844.9,   change_pct:-1.56, volume:22753,   rsi:71.8, macd:-8.5, signal_type:'SELL', confidence:0.72, entry_price:4848,  stop_loss:4944,  target_price:4656, freshness:'DELAYED' },
  { symbol:'WIPRO',      name:'Wipro Ltd',                    sector:'Technology',     ltp:194.6,    change_pct:-0.82, volume:384208,  rsi:68.4, macd:-2.1, signal_type:'SELL', confidence:0.68, entry_price:195,   stop_loss:201,   target_price:183,  freshness:'DELAYED' },
  { symbol:'HCLTECH',    name:'HCL Technologies Ltd',         sector:'Technology',     ltp:1378.0,   change_pct:-0.20, volume:130410,  rsi:49.3, macd:0.9,  signal_type:'HOLD', confidence:0.57, entry_price:1380,  stop_loss:1352,  target_price:1436, freshness:'DELAYED' },
  { symbol:'TECHM',      name:'Tech Mahindra Ltd',            sector:'Technology',     ltp:1764.0,   change_pct:-0.56, volume:53709,   rsi:45.6, macd:3.2,  signal_type:'BUY',  confidence:0.65, entry_price:1766,  stop_loss:1730,  target_price:1838, freshness:'DELAYED' },
  { symbol:'NTPC',       name:'NTPC Ltd',                     sector:'Energy',         ltp:319.1,    change_pct:-1.21, volume:272410,  rsi:37.8, macd:1.4,  signal_type:'BUY',  confidence:0.67, entry_price:320,   stop_loss:313,   target_price:334,  freshness:'DELAYED' },
  { symbol:'POWERGRID',  name:'Power Grid Corporation',       sector:'Energy',         ltp:257.4,    change_pct:-0.77, volume:759448,  rsi:42.1, macd:0.8,  signal_type:'BUY',  confidence:0.64, entry_price:258,   stop_loss:253,   target_price:268,  freshness:'DELAYED' },
  { symbol:'ONGC',       name:'Oil & Natural Gas Corp',       sector:'Energy',         ltp:225.0,    change_pct:0.22,  volume:474996,  rsi:52.4, macd:1.0,  signal_type:'HOLD', confidence:0.59, entry_price:225,   stop_loss:220,   target_price:235,  freshness:'DELAYED' },
  { symbol:'TATASTEEL',  name:'Tata Steel Ltd',               sector:'Metals',         ltp:186.7,    change_pct:-0.70, volume:574602,  rsi:34.5, macd:2.1,  signal_type:'BUY',  confidence:0.71, entry_price:187,   stop_loss:183,   target_price:195,  freshness:'DELAYED' },
  { symbol:'JSWSTEEL',   name:'JSW Steel Ltd',                sector:'Metals',         ltp:1348.0,   change_pct:-0.30, volume:99666,   rsi:40.0, macd:3.5,  signal_type:'BUY',  confidence:0.66, entry_price:1350,  stop_loss:1323,  target_price:1404, freshness:'DELAYED' },
  { symbol:'HINDALCO',   name:'Hindalco Industries',          sector:'Metals',         ltp:943.6,    change_pct:-2.12, volume:121332,  rsi:29.8, macd:4.2,  signal_type:'BUY',  confidence:0.75, entry_price:945,   stop_loss:925,   target_price:985,  freshness:'DELAYED' },
  { symbol:'GRASIM',     name:'Grasim Industries',            sector:'Diversified',    ltp:3034.0,   change_pct:-2.60, volume:28077,   rsi:31.4, macd:5.1,  signal_type:'BUY',  confidence:0.70, entry_price:3040,  stop_loss:2978,  target_price:3164, freshness:'DELAYED' },
  { symbol:'ULTRACEMCO', name:'UltraTech Cement',             sector:'Cement',         ltp:12100.0,  change_pct:-1.92, volume:9172,    rsi:33.2, macd:7.8,  signal_type:'BUY',  confidence:0.68, entry_price:12120, stop_loss:11878, target_price:12604,freshness:'DELAYED' },
  { symbol:'ASIANPAINT', name:'Asian Paints Ltd',             sector:'Consumer',       ltp:2550.0,   change_pct:0.53,  volume:48958,   rsi:58.3, macd:-1.5, signal_type:'HOLD', confidence:0.55, entry_price:2552,  stop_loss:2501,  target_price:2654, freshness:'DELAYED' },
  { symbol:'NESTLEIND',  name:'Nestle India Ltd',             sector:'FMCG',           ltp:1263.2,   change_pct:0.18,  volume:98527,   rsi:56.7, macd:0.6,  signal_type:'HOLD', confidence:0.57, entry_price:1264,  stop_loss:1239,  target_price:1314, freshness:'DELAYED' },
  { symbol:'DRREDDY',    name:"Dr Reddy's Laboratories",     sector:'Pharma',         ltp:1380.0,   change_pct:-0.48, volume:60447,   rsi:45.9, macd:2.2,  signal_type:'BUY',  confidence:0.65, entry_price:1382,  stop_loss:1354,  target_price:1438, freshness:'DELAYED' },
  { symbol:'CIPLA',      name:'Cipla Ltd',                    sector:'Pharma',         ltp:1391.8,   change_pct:-1.17, volume:50727,   rsi:36.0, macd:3.8,  signal_type:'BUY',  confidence:0.69, entry_price:1394,  stop_loss:1366,  target_price:1450, freshness:'DELAYED' },
  { symbol:'APOLLOHOSP', name:'Apollo Hospitals',             sector:'Healthcare',     ltp:8526.0,   change_pct:0.13,  volume:7921,    rsi:62.1, macd:-4.2, signal_type:'SELL', confidence:0.66, entry_price:8528,  stop_loss:8698,  target_price:8188, freshness:'DELAYED' },
  { symbol:'EICHERMOT',  name:'Eicher Motors Ltd',            sector:'Automobile',     ltp:7650.0,   change_pct:1.34,  volume:18352,   rsi:65.4, macd:-6.5, signal_type:'SELL', confidence:0.67, entry_price:7652,  stop_loss:7805,  target_price:7346, freshness:'DELAYED' },
  { symbol:'DLF',        name:'DLF Ltd',                      sector:'Real Estate',    ltp:758.8,    change_pct:-1.37, volume:48925,   rsi:32.5, macd:3.1,  signal_type:'BUY',  confidence:0.70, entry_price:760,   stop_loss:745,   target_price:790,  freshness:'DELAYED' },
  { symbol:'INDUSINDBK', name:'IndusInd Bank',                sector:'Banking',        ltp:914.4,    change_pct:-1.82, volume:25731,   rsi:28.4, macd:4.8,  signal_type:'BUY',  confidence:0.74, entry_price:916,   stop_loss:898,   target_price:952,  freshness:'DELAYED' },
  { symbol:'BANKBARODA', name:'Bank of Baroda',               sector:'Banking',        ltp:273.8,    change_pct:-0.84, volume:319614,  rsi:39.6, macd:1.6,  signal_type:'BUY',  confidence:0.63, entry_price:274,   stop_loss:268,   target_price:286,  freshness:'DELAYED' },
  { symbol:'PNB',        name:'Punjab National Bank',         sector:'Banking',        ltp:142.8,    change_pct:0.72,  volume:407997,  rsi:57.2, macd:0.3,  signal_type:'HOLD', confidence:0.54, entry_price:143,   stop_loss:140,   target_price:149,  freshness:'DELAYED' },
  { symbol:'CANBK',      name:'Canara Bank',                  sector:'Banking',        ltp:130.9,    change_pct:-1.57, volume:2031180, rsi:33.8, macd:2.4,  signal_type:'BUY',  confidence:0.65, entry_price:131,   stop_loss:128,   target_price:137,  freshness:'DELAYED' },
  { symbol:'COALINDIA',  name:'Coal India Ltd',               sector:'Energy',         ltp:403.5,    change_pct:-0.20, volume:73956,   rsi:50.3, macd:0.4,  signal_type:'HOLD', confidence:0.56, entry_price:404,   stop_loss:396,   target_price:420,  freshness:'DELAYED' },
  { symbol:'GODREJCP',   name:'Godrej Consumer Products',     sector:'FMCG',           ltp:870.8,    change_pct:-0.66, volume:14323,   rsi:44.2, macd:1.9,  signal_type:'BUY',  confidence:0.62, entry_price:872,   stop_loss:854,   target_price:908,  freshness:'DELAYED' },
  { symbol:'SBILIFE',    name:'SBI Life Insurance',           sector:'Insurance',      ltp:1789.9,   change_pct:-1.63, volume:15930,   rsi:30.1, macd:5.6,  signal_type:'BUY',  confidence:0.72, entry_price:1792,  stop_loss:1756,  target_price:1864, freshness:'DELAYED' },
  { symbol:'HDFCLIFE',   name:'HDFC Life Insurance',          sector:'Insurance',      ltp:592.2,    change_pct:-0.93, volume:144099,  rsi:35.5, macd:2.7,  signal_type:'BUY',  confidence:0.66, entry_price:593,   stop_loss:581,   target_price:617,  freshness:'DELAYED' },
  { symbol:'TRENT',      name:'Trent Ltd',                    sector:'Retail',         ltp:3165.2,   change_pct:-0.47, volume:30270,   rsi:48.8, macd:1.3,  signal_type:'HOLD', confidence:0.58, entry_price:3168,  stop_loss:3104,  target_price:3296, freshness:'DELAYED' },
  { symbol:'BEL',        name:'Bharat Electronics',           sector:'Defence',        ltp:400.9,    change_pct:-0.98, volume:188707,  rsi:38.0, macd:2.0,  signal_type:'BUY',  confidence:0.68, entry_price:401,   stop_loss:393,   target_price:417,  freshness:'DELAYED' },
  { symbol:'ADANIPORTS', name:'Adani Ports & SEZ',            sector:'Infrastructure', ltp:1903.3,   change_pct:-1.38, volume:33485,   rsi:36.4, macd:4.3,  signal_type:'BUY',  confidence:0.69, entry_price:1906,  stop_loss:1868,  target_price:1982, freshness:'DELAYED' },
  { symbol:'DIVISLAB',   name:"Divi's Laboratories",         sector:'Pharma',         ltp:11442.0,  change_pct:-0.37, volume:37343,   rsi:52.6, macd:-0.9, signal_type:'HOLD', confidence:0.56, entry_price:11450, stop_loss:11222, target_price:11906,freshness:'DELAYED' },
  { symbol:'M&M',        name:'Mahindra & Mahindra',          sector:'Automobile',     ltp:3333.0,   change_pct:-1.94, volume:154404,  rsi:32.0, macd:6.4,  signal_type:'BUY',  confidence:0.76, entry_price:3338,  stop_loss:3271,  target_price:3472, freshness:'DELAYED' },
  { symbol:'HINDUNILVR', name:'Hindustan Unilever',           sector:'FMCG',           ltp:1992.9,   change_pct:0.96,  volume:261042,  rsi:60.5, macd:-2.8, signal_type:'SELL', confidence:0.65, entry_price:1994,  stop_loss:2034,  target_price:1914, freshness:'DELAYED' },
  { symbol:'TATAMOTORS', name:'Tata Motors Ltd',              sector:'Automobile',     ltp:812.5,    change_pct:-1.10, volume:0,       rsi:35.2, macd:3.9,  signal_type:'BUY',  confidence:0.70, entry_price:814,   stop_loss:797,   target_price:848,  freshness:'DELAYED' },
  { symbol:'LTIM',       name:'LTIMindtree Ltd',              sector:'Technology',     ltp:7320.0,   change_pct:-0.65, volume:0,       rsi:46.5, macd:2.1,  signal_type:'HOLD', confidence:0.56, entry_price:7325,  stop_loss:7178,  target_price:7619, freshness:'DELAYED' },
  { symbol:'ZOMATO',     name:'Zomato Ltd',                   sector:'Consumer Tech',  ltp:286.5,    change_pct:1.80,  volume:0,       rsi:62.8, macd:-3.1, signal_type:'SELL', confidence:0.64, entry_price:287,   stop_loss:293,   target_price:275,  freshness:'DELAYED' },
];

// ─── Mock OHLCV candles (60 × 5-min bars for RELIANCE) ───────
function generateOHLCV(symbol: string, basePrice: number, count = 80): OHLCVBar[] {
  const bars: OHLCVBar[] = [];
  let price = basePrice;
  const baseTime = new Date(now.getTime() - count * 5 * 60_000);

  for (let i = 0; i < count; i++) {
    const change  = (Math.random() - 0.49) * basePrice * 0.004;
    const open    = price;
    price         = Math.max(price + change, basePrice * 0.85);
    const high    = Math.max(open, price) + Math.random() * basePrice * 0.002;
    const low     = Math.min(open, price) - Math.random() * basePrice * 0.002;
    const volume  = Math.floor(50_000 + Math.random() * 400_000);
    const ts      = new Date(baseTime.getTime() + i * 5 * 60_000).toISOString();
    bars.push({ symbol, timestamp: ts, open: +open.toFixed(2), high: +high.toFixed(2), low: +low.toFixed(2), close: +price.toFixed(2), volume, timeframe: '5m', data_source: 'demo' });
  }
  return bars;
}

export const MOCK_OHLCV: Record<string, OHLCVBar[]> = {
  RELIANCE:  generateOHLCV('RELIANCE',  1340),
  TCS:       generateOHLCV('TCS',       2410),
  INFY:      generateOHLCV('INFY',      1142),
  HDFCBANK:  generateOHLCV('HDFCBANK',  806),
  ICICIBANK: generateOHLCV('ICICIBANK', 1584),
  SBIN:      generateOHLCV('SBIN',      1080),
};

// ─── Mock Backtest Result ────────────────────────────────────
function buildEquityCurve() {
  const curve = [];
  let eq = 100_000;
  const stocks = ['RELIANCE','TCS','INFY','HDFCBANK','ICICIBANK','SBIN','BHARTIARTL','ITC','LT','AXISBANK','KOTAKBANK','BAJFINANCE','MARUTI','SUNPHARMA','TITAN','WIPRO','HCLTECH','NTPC','ONGC','TATASTEEL'];
  for (const s of stocks) {
    eq += (Math.random() - 0.38) * 3200;
    curve.push({ date: s, equity: +eq.toFixed(2) });
  }
  return curve;
}

export const MOCK_BACKTEST: BacktestResult = {
  id: 1,
  model_version: 'xgboost_demo',
  run_at: ts(60),
  accuracy: 0.712,
  precision_buy:  0.681, recall_buy:  0.643, f1_buy:  0.661,
  precision_sell: 0.658, recall_sell: 0.612, f1_sell: 0.634,
  total_return:   0.1842,
  win_rate:       0.624,
  sharpe_ratio:   1.38,
  max_drawdown:  -0.0812,
  total_trades:   184,
  winning_trades: 115,
  losing_trades:  69,
  avg_profit:     1240,
  avg_loss:      -610,
  equity_curve:   buildEquityCurve(),
  per_stock_stats: {
    RELIANCE:  { trades:12, wins:8,  win_rate:0.667, total_pnl:4820  },
    TCS:       { trades:10, wins:6,  win_rate:0.600, total_pnl:3140  },
    INFY:      { trades:11, wins:7,  win_rate:0.636, total_pnl:2980  },
    HDFCBANK:  { trades:9,  wins:5,  win_rate:0.556, total_pnl:1620  },
    ICICIBANK: { trades:13, wins:9,  win_rate:0.692, total_pnl:5260  },
    SBIN:      { trades:8,  wins:6,  win_rate:0.750, total_pnl:3410  },
    BHARTIARTL:{ trades:10, wins:7,  win_rate:0.700, total_pnl:4100  },
    WIPRO:     { trades:9,  wins:4,  win_rate:0.444, total_pnl:-840  },
    TITAN:     { trades:11, wins:7,  win_rate:0.636, total_pnl:6320  },
    LT:        { trades:10, wins:8,  win_rate:0.800, total_pnl:7840  },
  },
};

// ─── Mock Model Version ──────────────────────────────────────
export const MOCK_MODEL: ModelVersion = {
  id: 1,
  model_name: 'xgboost',
  version: 'xgboost_demo',
  trained_at: ts(120),
  features: ['rsi_14','macd','macd_signal','macd_hist','sma_5','sma_10','sma_20','sma_50','ema_9','ema_21','atr_14','bb_width','bb_position','vwap_diff','volume_ratio','momentum_5','volatility','change_1','change_3','change_5','close_vs_sma20','close_vs_ema21','candle_body','candle_upper_sh','candle_lower_sh','candle_bullish','hour','minute','day_of_week','close','open','high','low','volume'],
  feature_importances: {
    rsi_14:0.142, macd:0.118, momentum_5:0.098, atr_14:0.087, vwap_diff:0.082,
    bb_position:0.075, volume_ratio:0.068, close_vs_sma20:0.062, macd_hist:0.055,
    change_1:0.048, change_3:0.041, ema_9:0.036, volatility:0.030, hour:0.024, candle_body:0.021,
  },
  val_accuracy:  0.728,
  val_f1:        0.694,
  test_accuracy: 0.712,
  test_f1:       0.681,
  prediction_distribution: { BUY: 342, SELL: 298, HOLD: 11608 },
  training_samples: 81420,
  is_active: true,
};

// ─── Mock Dashboard Stats ────────────────────────────────────
export const MOCK_DASHBOARD: DashboardStats = {
  total_stocks:  50,
  buy_count:     28,
  sell_count:    9,
  hold_count:    13,
  bullish_count: 28,
  bearish_count: 9,
  market_status: 'CLOSED',
  last_update:   ts(2),
  top_buy_signals:  MOCK_SIGNALS.filter(s => s.signal_type === 'BUY').slice(0, 5),
  top_sell_signals: MOCK_SIGNALS.filter(s => s.signal_type === 'SELL').slice(0, 4),
  recent_signals:   MOCK_SIGNALS.slice(0, 8),
};
