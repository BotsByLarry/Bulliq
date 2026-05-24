# Day Trader AI — Complete Thinking Layer Architecture
### Master System Design Document
**Version 1.0 | Multi-Asset Intraday Intelligence Platform**

---

## Table of Contents

1. [Architecture Philosophy](#architecture-philosophy)
2. [Layer 1 — Real-Time Market Intake](#layer-1)
3. [Layer 2 — Day Trader Profile Engine](#layer-2)
4. [Layer 3 — Intraday Market Regime Detection](#layer-3)
5. [Layer 4 — Multi-Timeframe Technical Analysis](#layer-4)
6. [Layer 5 — Real-Time News and Sentiment Engine](#layer-5)
7. [Layer 6 — Signal Scoring and Confidence Engine](#layer-6)
8. [Layer 7 — Intraday Risk Management Engine](#layer-7)
9. [Layer 8 — Trade Plan Generation](#layer-8)
10. [Layer 9 — Explainability, Alerts, and Self-Correction](#layer-9)
11. [Layer 10 — Anti-Error and System Integrity Framework](#layer-10)
12. [Data Flow Summary](#data-flow-summary)
13. [Confidence Scoring Reference](#confidence-scoring-reference)
14. [Invalidation Triggers Reference](#invalidation-triggers)
15. [Section 15 — Development Roadmap and Implementation Strategy](#section-15)

---

## Architecture Philosophy {#architecture-philosophy}

Most trading systems fail for one of three reasons: they use the same strategy regardless of market conditions, they rely on a single signal without cross-validation, or they have no mechanism to stop themselves when they are wrong. This architecture is built to solve all three.

The system does not predict prices. It builds probability distributions, assigns confidence scores, validates signals across multiple independent layers, and only generates an actionable output when the totality of evidence clears a high threshold. Every signal must earn its way through nine sequential gates.

### Core Design Principles

**Probability over prediction.** No layer ever claims certainty. Every output is a weighted probability. The goal is to be right 65–70% of the time with excellent risk/reward on winners, not to be right 100% of the time.

**Regime-first thinking.** The first question is always: what kind of market is this right now? A strategy that works brilliantly in a trending market destroys capital in a choppy one. Regime detection runs before any trade logic.

**Cross-layer validation.** A signal produced by Layer 4 is not acted upon until it passes Layers 5, 6, and 7 independently. No single layer has override authority.

**Asymmetric risk design.** The system is tuned to find trades where the maximum loss is small and the potential gain is large. An R:R below 1.5:1 never fires, regardless of confidence.

**The circuit breaker principle.** The system can always refuse to trade. Silence is a valid output. Forcing a trade when conditions are poor is how most systems destroy capital.

---

## Layer 1 — Real-Time Market Intake {#layer-1}

**Purpose:** Build a clean, validated, timestamped representation of current market state across all relevant dimensions. Every layer above reads from this bus. No layer ever accesses raw feeds directly.

**Update frequency:** 250–500ms polling for most signals. Tick-by-tick for order flow.

---

### 1.1 Price Action Stream

The raw price nervous system. Consumed continuously, not only at candle close.

**Tick data** is every individual transaction. A 5-minute candle may contain 600–2000 ticks. The AI uses tick data to detect micro-momentum shifts, order absorption, and stop hunts before they are visible on any candle.

**Candle data** is built simultaneously at six resolutions:

| Resolution | Primary Use |
|---|---|
| 1m | Entry precision, noise detection, scalp triggers |
| 3m | Intermediate momentum reads, momentum divergences |
| 5m | Primary working timeframe for most day trades |
| 15m | Trade direction confirmation, swing structure |
| 1h | Session-level structural bias (do not fight this) |
| Daily | Prior day levels, overnight context |

**VWAP** resets every session at market open and is the most important intraday reference level. Institutional orders are benchmarked against VWAP, meaning large players defend and respond to it.

The AI tracks at all times:
- Live VWAP value updated every tick
- Whether price is above, below, or touching VWAP
- VWAP slope — direction and steepness indicates trending vs flat sessions
- Standard deviation bands at ±1σ and ±2σ (the "VWAP envelope")
- VWAP reclaim attempts — when price falls below VWAP and tries to recapture it

**Prior day and pre-market levels** are loaded before session open:
- Prior day high (PDH), prior day low (PDL), prior day close (PDC)
- Prior day VWAP (acts as extended reference)
- Pre-market high and low where available
- Opening range (first 15-minute high/low) — built live, becomes a key level

---

### 1.2 Order Flow Stream

Price shows what happened. Order flow shows why. This is where institutional intent leaks through.

**Level 2 Order Book (Market Depth)** shows all pending buy and sell orders stacked at every price level.

Key signals extracted continuously:
- **Depth ratio** — total bid volume vs total ask volume in the top 5–10 price levels
- **Liquidity pull** — sudden removal of a large bid or ask without a trade. This often precedes a sharp move in the opposite direction because the "wall" providing support/resistance has disappeared
- **Stacking** — rapid accumulation of new orders on one side at a specific level, suggesting an institution is defending a price
- **Spoofing detection** (pattern flagged, not acted upon) — large orders placed and immediately cancelled, intended to create false perception of demand/supply

**Bid/Ask Volume Imbalance** is calculated per tick and on a rolling basis:

```
buy_pressure = buy_volume / (buy_volume + sell_volume)
```

A reading above 0.70 over the last 500 ticks means aggressive buyers dominate. This is a directional signal independent of price movement, and it often leads price by a few candles.

**Time and Sales Tape** is the raw transaction log. The AI flags:
- Large single prints above X shares/lots (institutional-size trades)
- Rapid sequences of same-direction prints (momentum acceleration)
- Trades printing on the offer (aggressive buying) vs on the bid (aggressive selling)

**Iceberg Order Detection** watches for large hidden orders. An iceberg manifests as a bid or ask that consistently refreshes at the same price after each fill. A 200-lot bid that fills 200 lots but immediately reappears has a hidden reserve. The AI marks this price level as "strongly defended" and will not generate shorts against it.

**Cumulative Delta** (belongs in both order flow and volume intelligence) is the running total of buy volume minus sell volume from session open. The slope and divergences from price are among the highest-quality intraday signals available.

---

### 1.3 Volume Intelligence

Volume is the most under-analyzed dimension in retail trading. Price without volume context is incomplete.

**Cumulative Volume Delta (CVD):**

| Price Action | CVD Direction | Interpretation |
|---|---|---|
| Rising | Rising | Healthy trend, buyers in control |
| Rising | Flat | Trend slowing, potential exhaustion |
| Rising | Falling | Bearish divergence — sellers absorbing the move |
| Falling | Falling | Healthy downtrend |
| Falling | Rising | Bullish divergence — buyers stepping in |

**Volume vs Time-of-Day Average** — volume is not constant through the day. Opening 30 minutes are always high-volume. Midday (12:00–1:30pm IST) is the "dead zone." The last hour surges again. The AI compares each candle's volume against the expected volume for that time of day, not the all-day average. A breakout candle at 2pm with 2.5× the typical 2pm volume is significant. The same volume at 9:20am is unremarkable.

**Volume Profile** is a histogram of volume traded at each price level throughout the session so far:

- **Point of Control (POC):** The price level with the most traded volume. Acts as a magnet — price tends to return to it.
- **Value Area High (VAH) and Value Area Low (VAL):** The price range containing 70% of the session's volume. Price outside the value area statistically tends to return inside.
- **High Volume Nodes (HVN):** Dense volume clusters — act as strong support/resistance.
- **Low Volume Nodes (LVN):** Sparse volume zones — price tends to move through these quickly (gaps in the volume profile = fast-move zones).

**Delivery Volume (India Equity):** The proportion of traded volume resulting in actual share delivery vs same-day squaring off. High delivery at support = genuine accumulation by investors. Low delivery = speculative intraday activity that will not sustain.

---

### 1.4 Derived Real-Time Signals

Pre-calculated signals that all upstream layers consume directly.

**Live ATR** — Average True Range calculated on current session's candles, not historical. Intraday ATR determines stop loss distance and position sizing. Recalculated every 5m candle close.

**Tick Velocity** — price movement speed measured as points-per-second over a 30-second rolling window. A sudden spike in tick velocity (3–4× baseline) indicates an emerging momentum move. The AI uses this for early-detection of breakouts and stop cascades before they fully develop on any candle.

**Rolling Momentum Score** — composite of rate-of-change across three windows (5, 15, 30 candles). Outputs a continuous score from -100 (strong bearish) to +100 (strong bullish). Feeds directly into Layer 6 signal scoring.

**Spread Ratio** — current bid-ask spread as a percentage of price, divided by the instrument's normal spread baseline. A ratio above 2.0 means liquidity is deteriorating. The AI reduces position size and raises confidence thresholds when the spread ratio is elevated.

---

### 1.5 Global Context Feed

The Indian market opens having already processed 12+ hours of global price action. Ignoring this is an error.

**SGX Nifty (Nifty futures trading in Singapore)** is the primary overnight Nifty proxy. The AI reads SGX Nifty direction and gap magnitude before 9:15am to establish session bias and opening gap type (gap-and-go vs gap-fill scenario).

**US Futures (Dow, S&P 500, NASDAQ)** — during the Indian session (9:15am–3:30pm IST), US pre-market futures are live from approximately 7pm IST the prior evening. A sharp move in NASDAQ futures at 1:30pm IST will affect Indian IT stocks within 10–15 minutes. The AI monitors these continuously during the session.

**Key macro feeds monitored intraday:**

| Feed | Why It Matters |
|---|---|
| DXY (Dollar Index) | Rising DXY → pressure on emerging markets and FII outflows |
| Crude oil spot | Affects inflation expectations, OMCs, aviation stocks |
| Gold spot | Risk sentiment indicator; rising gold = risk-off |
| India VIX | Below 14 = calm/trending; Above 20 = fear, reduce size |
| 10-year bond yield | Rising yields = pressure on high-PE stocks |
| USD/INR | Currency pressure affects FII sentiment and IT exports |

**India VIX is given special weight.** The AI tracks both the absolute VIX level and its intraday direction. A rising VIX during a market rally is a warning signal — the options market is buying protection despite rising prices, suggesting smart money expects reversal.

---

### 1.6 Event and Calendar Feed

This sub-system functions as a risk filter. Its job is to tell the AI when trading is dangerous, not when to trade.

**Pre-session event load (executed before 9:00am IST):**
- All scheduled macro events for the day (domestic and global)
- Earnings releases scheduled during or after market hours
- F&O expiry dates (weekly and monthly)
- RBI monetary policy decision dates
- FOMC meeting dates and minutes release times
- Any stock-specific corporate events (board meetings, AGMs, record dates)

**Event impact classification:**

| Impact Level | Examples | AI Behavior |
|---|---|---|
| Critical | RBI rate decision, FOMC | Pause all signals on affected instruments 30 min before and 15 min after |
| High | CPI/WPI release, Q results | Flag as elevated risk, require extra confirmation |
| Medium | PMI data, FII flows report | Reduce position size on correlated instruments |
| Low | Minor economic data | Note in context, no behavior change |

**F&O specific monitoring:**
- F&O ban list (stocks where no new derivative positions can be taken)
- Rollover activity in index futures (heavy rollover = market sentiment signal)
- Significant options strikes approaching (massive OI at a strike = price magnet near expiry)
- Gamma squeeze risk on weekly expiry Thursdays

---

### 1.7 Data Quality and Latency Monitor

The invisible but most critical sub-system. Corrupted data fed to downstream layers produces confidently wrong decisions.

**Latency monitoring:** Every data point is timestamped. The AI tracks data age per feed:
- Green: data < 1 second old
- Yellow: data 1–3 seconds old (flag, reduce confidence slightly)
- Red: data > 3 seconds old (freeze dependent signals, trigger failover)

**Outlier and spike filter:** Every tick is validated against a statistical range. A tick more than 5× the recent ATR from the last valid price is held as a probable feed error before being used. Corporate action adjustments (splits, bonuses, dividends) are auto-detected and applied to historical data to prevent discontinuities.

**Source failover:** The system runs at least two independent data feeds simultaneously. If the primary feed goes silent or shows anomalous latency, the secondary feed takes over automatically. A day trader's AI going blind for 20 seconds mid-trade can cause catastrophic loss.

**Missing candle detection:** If a candle fails to form at the expected time (network issue, exchange halt), downstream indicator calculations are paused rather than run on stale or incomplete data.

**Exchange halt and circuit breaker detection:** Automatic detection of:
- Stock-level circuit breakers (upper/lower limit locks)
- Index-level circuit breakers (10%, 15%, 20% moves)
- Exchange technical halts (rare but critical to detect immediately)

---

### Layer 1 Output Object

```json
{
  "timestamp": "2025-05-24T09:47:23.412Z",
  "instrument": "RELIANCE",
  "last_price": 2487.50,
  "vwap": 2472.30,
  "price_vs_vwap": "above",
  "vwap_slope": "rising",
  "atr_5m": 14.2,
  "tick_velocity": 1.8,
  "cvd_slope": "positive",
  "cvd_divergence": false,
  "buy_pressure_ratio": 0.64,
  "volume_vs_avg": 1.42,
  "spread_ratio": 1.1,
  "data_quality": "green",
  "latency_ms": 180,
  "event_risk": "low",
  "india_vix": 13.4,
  "vix_direction": "falling",
  "sgx_nifty_bias": "bullish",
  "global_context": "neutral_positive"
}
```

---

## Layer 2 — Day Trader Profile Engine {#layer-2}

**Purpose:** Establish who the trader is before analyzing any market signal. Two traders looking at identical market conditions may need completely different outputs. The profile gates every downstream layer.

---

### 2.1 Profile Parameters

**Trading style** determines which signal types are activated:

| Style | Signal Focus | Timeframe Emphasis | Risk Per Trade |
|---|---|---|---|
| Scalper | Tick momentum, order flow, spread | 1m/3m primary | 0.25–0.5% |
| Momentum day trader | Breakouts, volume surges, trend following | 5m/15m primary | 0.75–1.5% |
| Reversal trader | Exhaustion signals, divergences, mean-reversion | 5m/15m primary | 0.5–1.0% |
| Range trader | VWAP bounce, support/resistance fades | 5m primary | 0.5–1.0% |
| News trader | Event-driven, tape reading, catalyst plays | 1m/3m primary | 0.5–1.0% |

**Risk appetite:** Conservative (max 0.5% per trade), Moderate (max 1%), Aggressive (max 2%). This is a hard cap — not a guideline.

**Capital size and position limits:**
- Total portfolio capital (determines position sizing in rupee terms)
- Maximum simultaneous open positions (prevents correlation overload)
- Maximum total exposure at any time (e.g. 30% of capital across all open trades)

**Experience level** affects output verbosity and signal filtering:
- Beginner: Only highest-confidence signals (>75%), simpler explanations, tighter risk parameters
- Intermediate: Signals above 60% confidence, standard detail level
- Advanced: All signals above 55%, full technical detail, alternative scenarios included

**Emotional behavior flags** (set during onboarding and updated via behavioral tracking):
- FOMO tendency → the AI adds a delay/confirmation requirement before any "chasing" entry
- Panic selling tendency → the AI includes a volatility spike warning with every stop loss level
- Overtrading tendency → daily trade count limit enforced, signals throttled after X trades
- Revenge trading risk → if previous trade was a loss, the AI increases the confidence threshold for the next signal by 10 percentage points

---

### 2.2 Profile Output Object

```json
{
  "style": "momentum_day_trader",
  "risk_per_trade_pct": 1.0,
  "max_daily_loss_pct": 3.0,
  "capital": 500000,
  "max_open_positions": 3,
  "max_total_exposure_pct": 40,
  "experience_level": "intermediate",
  "min_confidence_threshold": 62,
  "rr_minimum": 1.8,
  "emotional_flags": ["fomo_tendency"],
  "preferred_instruments": ["large_cap_equities", "nifty_options"],
  "preferred_session": "morning_only",
  "previous_trade_result": "loss",
  "adjusted_confidence_threshold": 72
}
```

The `adjusted_confidence_threshold` is the real operative value. If the prior trade was a loss, the threshold rises automatically to prevent revenge-trade impulses from finding expression through the AI.

---

## Layer 3 — Intraday Market Regime Detection {#layer-3}

**Purpose:** Determine the character of the market before selecting any strategy. This is the most critical yet most commonly skipped layer in retail systems. An AI that uses the same strategy in a trending market as in a choppy one will eventually destroy capital.

The regime is re-evaluated every 15 minutes throughout the session and can change.

---

### 3.1 Regime Types

**Strongly Trending (Bullish or Bearish)**
- ADX above 28, price moving in one direction with periodic shallow pullbacks
- VWAP slope is steep and consistent
- Volume confirms direction on trend candles; low volume on pullbacks
- AI behavior: Follow momentum, trail stops loosely, bias toward breakout entries, give trades more time to work

**Weakly Trending**
- ADX between 18–28, directional bias exists but conviction is low
- Price occasionally crosses VWAP and reclaims it
- AI behavior: Reduced position sizes, tighter targets, confirm each entry with volume

**Ranging / Choppy**
- ADX below 18, price moving sideways within a defined band
- Multiple failed breakout attempts
- High-low range narrow relative to prior sessions
- AI behavior: Fade extremes of the range, use VWAP as midpoint, target 60–70% of the range width, do not use momentum strategies — they get chopped apart

**Breakout Forming (Pre-Breakout)**
- Price compressing in a tight range with declining volume (Bollinger squeeze)
- ATR at a multi-session low
- AI behavior: Alert to the compression, wait for volume expansion, prepare breakout entry plan, do not enter before confirmation

**News-Driven / Event Spike**
- Sudden volume surge (5× or greater average) often on no visible technical reason
- Tick velocity spike
- Wide spread expansion
- AI behavior: Pause standard signals entirely. Assess whether the move is a catalyst continuation or a trap. Wait for 2–3 candles of stabilization before any entry.

**Low Liquidity / Dead Zone**
- Typically 12:00pm–1:30pm IST
- Volume < 40% of morning session average
- Spread widening
- AI behavior: Reduce position sizes by 50%, raise confidence threshold by 15 points, avoid all breakout signals (false breakouts are extremely common in this window)

**Gap Session (Up-Gap or Down-Gap)**
- Session opens more than 0.5% from prior close
- First 5 minutes are critical: is the gap being held (gap-and-go) or filled (gap-fill)?
- AI behavior: Wait for opening range formation (first 15 minutes), then assess gap type before generating signals

---

### 3.2 Regime Inputs

**Trend strength indicators:**
- ADX (14-period, 15m chart) — the primary trend strength gauge
- EMA alignment: Is the EMA 9 > EMA 21 > EMA 50 (bullish stack) or inverted (bearish stack)?
- VWAP slope angle — measured as rise/run over the last 30 minutes

**Market breadth (for index instruments):**
- Advance/decline ratio across Nifty 50 constituents
- How many Nifty stocks are above their own VWAP (breadth participation)
- Sector rotation signals: which sectors are leading vs lagging

**Volatility assessment:**
- India VIX absolute level and intraday change
- Current-session ATR vs 10-session average ATR
- Bollinger Band width relative to 20-period average (squeeze detection)

**Session timing context:**
- Pre-market (before 9:15): Assessment mode only
- Opening 30 minutes (9:15–9:45): High energy, high opportunity, high risk — all signals marked as elevated-risk
- Mid-morning (9:45–12:00): Highest quality trending signals
- Dead zone (12:00–1:30): Heavily filtered
- Afternoon (1:30–3:00): Second wind, news/global catalyst driven
- Closing 30 minutes (3:00–3:30): Markup/markdown activity, avoid new entries

---

### 3.3 Regime Output Object

```json
{
  "regime": "weakly_trending_bullish",
  "adx_strength": 22,
  "trend_direction": "bullish",
  "vwap_relationship": "price_above_rising_vwap",
  "volatility_state": "normal",
  "session_phase": "mid_morning",
  "breadth_participation": 68,
  "gap_type": "small_gap_up_held",
  "strategy_bias": "momentum_with_caution",
  "position_size_modifier": 0.8,
  "confidence_threshold_modifier": "+5",
  "preferred_strategy_types": ["vwap_pullback", "breakout_with_volume"],
  "avoid_strategy_types": ["reversal", "counter_trend"]
}
```

The `position_size_modifier` and `confidence_threshold_modifier` are applied to the profile parameters before signal evaluation. A choppy regime might apply a 0.5 size modifier, meaning all positions are half their normal size regardless of signal confidence.

---

## Layer 4 — Multi-Timeframe Technical Analysis {#layer-4}

**Purpose:** Build a complete technical picture of the asset across three aligned timeframes. Signals only generate when timeframe alignment is confirmed. Fighting the 1h bias on the 5m chart is the most common technical trading mistake.

---

### 4.1 Timeframe Alignment Logic

Before running any indicator, the AI establishes bias on each timeframe independently:

| Timeframe | Bullish Bias Requirements |
|---|---|
| 1h (context) | Price above EMA 21, MACD histogram positive, prior structure of higher highs |
| 15m (direction) | Price above VWAP, EMA 9 > EMA 21, RSI above 50 |
| 5m (entry) | Specific entry pattern forming (pullback, breakout, reversal signal) |

**Alignment scores:**
- All three timeframes aligned: +25 points to confidence score
- Two of three aligned: +12 points
- Only one aligned: Signal suppressed entirely — do not trade against two timeframes

---

### 4.2 Trend Analysis

**EMA Stack Analysis** (run on 5m and 15m):

The AI uses a three-EMA system: EMA 9 (fast), EMA 21 (medium), EMA 50 (slow).

- Perfect bull stack: EMA 9 > EMA 21 > EMA 50 with price above all three. Strong trend condition.
- Bull stack with price pullback to EMA 21 in an uptrend: Primary long entry zone.
- Bear stack: EMA 9 < EMA 21 < EMA 50. No long entries in any condition.
- Tangled EMAs (crossing and uncrossing repeatedly): Choppy regime confirmed — no trend-following trades.

**MACD (12, 26, 9 settings on 5m chart):**
- Histogram direction: Expanding histogram = strengthening momentum, shrinking = weakening
- Zero-line cross: Significant momentum shift
- Divergence: MACD making lower highs while price makes higher highs = bearish divergence (strong warning signal)
- Signal line cross: Entry timing confirmation (not used alone)

**VWAP Relationship:**
- Price above rising VWAP: Bull bias
- Price below falling VWAP: Bear bias
- Price at VWAP in sideways session: Neutral — wait for direction
- VWAP reclaim (price falls below VWAP then closes back above): Potential long setup
- VWAP rejection (price rises to VWAP from below, fails): Potential short setup

---

### 4.3 Momentum Analysis

**RSI (14-period on 5m and 15m):**

The AI uses RSI contextually, not as overbought/oversold in isolation. In strong trends, RSI can stay above 70 for hours. Key uses:

- RSI above 50 in an uptrend with a pullback to 50: Momentum healthy, buy-the-dip setup
- RSI divergence: Most powerful use — price makes a new high but RSI makes a lower high = bearish divergence, warning signal
- RSI failure swing (RSI falls from above 70, rallies but fails to reach 70 again, then breaks below the prior RSI swing low): High-probability reversal signal

**Volume Rate of Change:**
- Volume accelerating on trend candles and decelerating on pullback candles: Healthy trend, continue following
- Volume accelerating on a candle against the trend: Warning — possible reversal

**Stochastic RSI (3, 3, 14, 14 settings):**
- Used primarily for short-term entry timing
- Cross above 20 in an uptrend context: Entry trigger
- Cross below 80 in a downtrend context: Short entry trigger
- Never used in isolation as the sole signal

---

### 4.4 Candlestick Pattern Recognition

Patterns are scored by quality, not treated as binary signals.

**Reversal patterns at key levels (scored 1–5):**

| Pattern | Score | Notes |
|---|---|---|
| Engulfing candle with volume | 5 | Strongest single-candle reversal signal |
| Pin bar / hammer at support | 4 | Requires high volume for full score |
| Morning / evening star | 5 | Three-candle confirmation |
| Bullish/bearish harami | 3 | Requires next-candle confirmation |
| Doji at key level | 3 | Context-dependent; higher score at VWAP or major S/R |

**Continuation patterns:**

| Pattern | Score | Notes |
|---|---|---|
| Bull flag (tight consolidation after strong move) | 5 | Break of flag high with volume = entry |
| Inside bar breakout | 4 | Parent bar high/low as entry/stop |
| Marubozu (full-body candle, no wicks) | 4 | Indicates strong directional conviction |
| Three white soldiers / three black crows | 4 | Trend continuation with volume |

**Pattern invalidation:** Any pattern that forms with below-average volume has its score reduced by 2. A pin bar with 50% of average volume is a score-1 signal and will not pass Layer 6 thresholds.

---

### 4.5 Volatility Analysis

**ATR Utilization:**
- ATR determines stop loss distance (typically 1.0–1.5× ATR from entry)
- ATR expansion (current ATR > 20-session average): Widen stops, reduce position size
- ATR contraction (Bollinger squeeze): Low volatility coil — anticipate breakout, do not enter until it fires
- ATR used to assess whether a target is realistic within the remaining session time

**Bollinger Bands (20, 2.0 settings on 5m):**
- Band squeeze (bands narrowing significantly): High-probability breakout setup forming
- Price touching upper/lower band in a ranging market: Fade entry opportunity
- Price riding the upper band with consistent candle closes: Strong trend (do not fade in a trending regime)

---

### 4.6 Key Level Mapping

Before every session, the AI maps all significant price levels on the instruments being tracked. These are loaded into the system as reference points that signals are evaluated against.

**Pre-mapped daily levels:**
- Prior day high (PDH), prior day low (PDL), prior day close (PDC)
- Prior day VWAP
- Weekly open (Monday's open price — major reference)
- Monthly open (first trading day's open — longer-term reference)
- Major psychological round numbers (every 50 and 100 points on Nifty; every round 100/500 on large cap stocks)

**Intraday dynamic levels (updated live):**
- Current session VWAP
- Opening range high and low (9:15–9:30am range)
- Session high and low so far
- Point of Control from volume profile
- High Volume Nodes from volume profile
- Any obvious horizontal support/resistance from 15m or 1h chart

**Level proximity scoring:** When a signal forms near a key level, the quality score increases:
- Signal at confluence of 3+ levels: +15 to confidence score
- Signal at 1–2 levels: +8 to confidence score
- Signal with no nearby level: Score unchanged (no structural backing)

---

### 4.7 Layer 4 Output Object

```json
{
  "instrument": "RELIANCE",
  "1h_bias": "bullish",
  "15m_bias": "bullish",
  "5m_bias": "bullish_pullback",
  "timeframe_alignment": "strong",
  "alignment_score": 25,
  "ema_stack_5m": "bull_stack",
  "ema_stack_15m": "bull_stack",
  "vwap_relationship": "above_rising",
  "macd_5m": "positive_histogram_expanding",
  "rsi_5m": 54,
  "rsi_divergence": false,
  "momentum_score": 72,
  "pattern_detected": "bull_flag",
  "pattern_score": 5,
  "pattern_volume_confirmed": true,
  "pattern_level": "vwap_support",
  "key_level_confluence": 3,
  "atr_5m": 14.2,
  "volatility_state": "normal",
  "bollinger_state": "mid_band",
  "technical_score": 78
}
```

---

## Layer 5 — Real-Time News and Sentiment Engine {#layer-5}

**Purpose:** Monitor all non-price information that moves markets. A technically perfect setup on a stock reporting earnings in 20 minutes is a dangerous trade. A technically mediocre setup on a stock with massive positive news is a high-probability trade. News and sentiment modify, amplify, or kill technical signals.

---

### 5.1 News Monitoring and Processing

**News source hierarchy (by reliability and speed):**

1. Exchange feeds (BSE/NSE announcements) — the authoritative source for corporate events
2. Wire services (Reuters, Bloomberg terminals)
3. Financial news portals (Moneycontrol, Economic Times, Mint)
4. Social media and communities (StockTwits, Twitter/X, Telegram) — sentiment signal only, not fact source

**News classification:**

Every news item is classified before being used:

| Category | Examples | Impact Duration |
|---|---|---|
| Earnings beat/miss | Quarterly results | 1–3 sessions |
| Merger/acquisition | Deal announcement | Multi-session |
| Management change | CEO/CFO resignation/appointment | 1–2 sessions |
| Regulatory action | SEBI order, government policy | Varies widely |
| Product/contract win | Large order, new product launch | 1 session |
| Macro surprise | RBI rate decision surprise | Same session to multi-day |
| Index inclusion/exclusion | Nifty 50 rejig | Multi-session pre-announcement drift |

**Sentiment scoring per news item:**
- Positive/negative/neutral classification
- Magnitude: Minor, moderate, significant, extreme
- Novelty: Is this news already known (priced in) or genuinely new information?
- Credibility: Source reliability score

A news item scores highest when it is: positive/negative, significant magnitude, genuinely new information, from a reliable source.

---

### 5.2 Options Market Sentiment (Highly Important for India)

The options market is where institutional and smart-money participants express their views with size. For Nifty and BankNifty, this data is extremely valuable.

**Put/Call Ratio (PCR):**
- PCR above 1.2: Significant put buying → fear, potential bullish contrarian signal (market tends to bottom when everyone is hedged)
- PCR below 0.7: Significant call buying → complacency, potential bearish contrarian signal
- PCR moving sharply in one direction intraday: Directional sentiment shift in progress

**Open Interest (OI) Analysis:**
- Call OI buildup at a strike: That strike becomes resistance — market makers will defend it
- Put OI buildup at a strike: That strike becomes support — market makers will defend it
- Max pain level: The expiry price at which the maximum number of options expire worthless. Price is observed to gravitate toward max pain as expiry approaches (Thursday for weekly options)

**OI interpretation table:**

| Price Direction | OI Direction | Interpretation |
|---|---|---|
| Rising price | Rising OI | New longs entering — trend strong |
| Rising price | Falling OI | Short covering rally — trend weak, reversal risk |
| Falling price | Rising OI | New shorts entering — trend strong |
| Falling price | Falling OI | Long unwinding — temporary dip, watch for recovery |

**Gamma Exposure (GEX):** On days with high concentrated gamma (particularly weekly expiry Thursdays), market makers are forced to hedge their books by selling as price rises and buying as price falls (negative gamma = volatility amplification). The AI flags high-GEX days as elevated volatility risk.

**IV (Implied Volatility) levels:** IV crush after events means options bought before an event lose value rapidly after it resolves, even if the price moves correctly. The AI tracks IV percentile rank and warns when IV is historically elevated (>80th percentile) — options buying is expensive and directional trades in options require larger price moves to profit.

---

### 5.3 Institutional Flow Data

**FII (Foreign Institutional Investor) and DII (Domestic Institutional Investor) data:**

Published by exchanges after market close but available intraday in provisional form. The AI uses this to assess whether institutional participants are net buyers or sellers in the current period:

- Sustained FII buying over 3–5 sessions: Bullish structural tailwind
- FII selling with DII buying: Offsetting flows, market finding support
- Both FII and DII selling: High-risk environment, reduce all exposures

**Block deal and bulk deal monitoring:**
- Block deals (trades above ₹5cr executed in the pre-open or on a single ticket): Signals large institutional conviction
- Bulk deals (any entity trading more than 0.5% of outstanding shares in a day): Ownership change signal
- Insider filing activity: Directors/promoters buying or selling their own stock

---

### 5.4 Social Sentiment Tracking

Social sentiment is a secondary signal — it confirms or adds context to technical and news-based signals. It is never a primary trade reason.

**What the AI tracks:**
- Mention velocity: How rapidly a stock or index is being mentioned compared to its baseline
- Sentiment direction: Net positive vs negative tone in mentions
- Source quality weighting: Analyst commentary > verified accounts > general public
- Trending themes: What sectors or stocks dominate discussion

**Behavioral signals to detect:**
- Retail mania: Sudden explosion in mentions with positive sentiment + price already extended = late-stage move, do not chase
- Panic indicators: Spike in fear-language mentions during a price drop = potential bottoming signal
- Informed commentary: Specific fundamental or technical analysis in social mentions adds weight to the signal

---

### 5.5 Sentiment Output Object

```json
{
  "news_sentiment": "positive",
  "news_magnitude": "moderate",
  "news_novelty": "new_information",
  "news_risk_flag": false,
  "event_in_next_30min": false,
  "pcr": 0.88,
  "pcr_interpretation": "neutral_slightly_bullish",
  "call_oi_resistance": 2500,
  "put_oi_support": 2450,
  "max_pain": 2480,
  "oi_interpretation": "new_longs_entering",
  "fii_flow_5d": "net_buyers",
  "dii_flow_5d": "net_buyers",
  "institutional_bias": "bullish",
  "social_sentiment_score": 68,
  "retail_mania_flag": false,
  "sentiment_score": 72
}
```

---

## Layer 6 — Signal Scoring and Confidence Engine {#layer-6}

**Purpose:** Convert all upstream layer outputs into a single weighted confidence score with a clear directional call. This is the decision layer. Every input has a weight. Weights adjust dynamically based on regime.

---

### 6.1 Base Scoring Weights

| Factor | Base Weight | What it Measures |
|---|---|---|
| Multi-TF technical alignment | 28% | EMA stack, MACD, RSI, VWAP alignment |
| Momentum strength | 20% | Volume delta, tick velocity, momentum score |
| Volume confirmation | 15% | Volume vs average, CVD direction |
| Sentiment and news | 12% | Options data, FII flows, news sentiment |
| Key level confluence | 12% | Number of overlapping support/resistance levels |
| Market regime fit | 8% | How well the signal type fits the current regime |
| Pattern quality | 5% | Candlestick pattern score |

**Total: 100%**

---

### 6.2 Dynamic Weight Adjustments

Weights shift based on market regime to reflect which factors are most informative in current conditions:

**Strong trending regime:** Technical alignment weight rises to 35%, sentiment drops to 8%. In a strong trend, price action and momentum dominate.

**Choppy/ranging regime:** Key level confluence weight rises to 20%, momentum drops to 12%. In a range, level proximity matters more than momentum.

**News-driven spike:** Sentiment and news weight rises to 25%, technical alignment drops to 18%. When a catalyst is driving price, fundamentals and news matter most.

**Pre-expiry (Wednesday/Thursday for weekly options):** Options OI and max pain weight increases substantially as expiry dynamics start to dominate.

---

### 6.3 Confidence Score Calculation

Each factor generates a sub-score from 0–100. The weighted average produces the overall confidence score.

**Example calculation:**

| Factor | Sub-Score | Weight | Contribution |
|---|---|---|---|
| Technical alignment | 78 | 28% | 21.84 |
| Momentum | 72 | 20% | 14.40 |
| Volume | 65 | 15% | 9.75 |
| Sentiment | 70 | 12% | 8.40 |
| Level confluence | 80 | 12% | 9.60 |
| Regime fit | 75 | 8% | 6.00 |
| Pattern | 90 | 5% | 4.50 |
| **Total** | | | **74.49** |

**Confidence = 74% → Signal quality: GOOD → Proceed to Layer 7**

---

### 6.4 Confidence Thresholds and Actions

| Confidence Score | Signal Quality | Action |
|---|---|---|
| Below 55% | Poor | No signal generated |
| 55–62% | Weak | Signal flagged as informational only, no trade |
| 62–70% | Moderate | Trade at 60% of normal position size |
| 70–80% | Good | Trade at full position size |
| 80–90% | Strong | Trade at full size, slightly wider targets allowed |
| Above 90% | Exceptional | Full size, note as high-conviction setup |

**Threshold adjustments (cumulative):**
- Regime is choppy: +8 points required
- Previous trade was a loss: +10 points required
- News event within 30 minutes: +15 points required
- India VIX above 20: +10 points required
- Spread ratio above 2.0: +12 points required

---

### 6.5 Directional Probability Output

The confidence score is also decomposed into directional probabilities:

```json
{
  "signal_direction": "long",
  "confidence_score": 74,
  "bullish_probability": 74,
  "bearish_probability": 26,
  "signal_quality": "good",
  "factor_breakdown": {
    "technical": 78,
    "momentum": 72,
    "volume": 65,
    "sentiment": 70,
    "levels": 80,
    "regime_fit": 75,
    "pattern": 90
  },
  "weakest_factor": "volume",
  "weakest_factor_note": "Volume is confirming but not exceptional",
  "threshold_after_modifiers": 62,
  "pass": true
}
```

The weakest factor annotation is passed directly to the explainability layer so the AI can tell the trader what the signal's most vulnerable point is.

---

## Layer 7 — Intraday Risk Management Engine {#layer-7}

**Purpose:** This layer can kill any trade that passed Layers 1–6. A high-confidence signal that fails risk parameters does not become a trade. Risk management is non-negotiable and has no override.

---

### 7.1 Position Sizing

Position size is calculated, not guessed. The AI uses the following formula:

```
position_size = (capital × risk_per_trade_pct) / (stop_loss_distance_in_points × lot_value)
```

**Example:**
- Capital: ₹5,00,000
- Risk per trade: 1% → ₹5,000 maximum loss
- Stop loss distance: 15 points on a stock trading at ₹2,480
- Position size: ₹5,000 / 15 = 333 shares (rounded to board lot)

**ATR adjustment:** If current ATR is 1.5× the historical average, position size is reduced by 33% automatically. Higher volatility means wider natural swings, requiring smaller positions to keep the rupee risk constant.

**Portfolio exposure cap:** If existing open positions already represent 30% of capital, new positions are capped at a size that keeps total exposure below 40% regardless of the position sizing formula output.

---

### 7.2 Stop Loss Placement

Stop losses are placed at technically meaningful levels, never at arbitrary distances.

**Methods (in priority order):**

1. **Below last swing low / above last swing high** — the most structurally sound stop. If a bullish trade invalidates when price breaks a specific swing low, the stop goes just below that level.

2. **ATR-based:** `stop = entry_price - (ATR × 1.25)` for longs. Ensures the stop is outside normal candle noise. Tightened to 1.0× ATR for scalps; widened to 1.5× ATR for swing-day trades.

3. **Below key level:** Below VWAP, below POC, below prior day's low, depending on the trade type.

**Stop loss rules:**
- Stops are never moved further away from entry to "give a trade more room." This is the most common retail mistake.
- Stops can be moved closer to entry (trailed) as the trade profits.
- If the technical reason for the trade is violated before the stop is hit (e.g. MACD crosses bearish, volume disappears), the AI recommends early exit regardless of stop distance.

---

### 7.3 Reward-to-Risk (R:R) Gate

This is a hard filter. The R:R gate does not negotiate.

| R:R | Action |
|---|---|
| Below 1.5:1 | Trade rejected entirely — no signal output |
| 1.5:1 – 1.9:1 | Trade flagged as marginal, position size halved |
| 2.0:1 – 2.9:1 | Trade accepted, normal parameters |
| 3.0:1 and above | High-quality setup, full parameters |

**Target placement:**
- T1 (first target) is set at the first significant resistance level above entry
- T2 (second target) is set at the next resistance or at 2× the stop distance from entry
- The AI recommends scaling out: 50–60% of position at T1, trail stop to breakeven, let remainder run to T2

---

### 7.4 Daily Circuit Breakers

These cannot be overridden under any circumstances. If a circuit breaker fires, the AI stops generating trade signals for the remainder of that session.

| Circuit Breaker | Trigger |
|---|---|
| Daily loss limit | P&L reaches -3% of capital (or the trader's configured maximum) |
| Consecutive loss limit | Three consecutive losing trades in one session |
| Drawdown velocity | 2% loss in under 30 minutes (indicates a fast-moving adverse market) |
| Maximum trade count | More than the trader's configured maximum trades per session |

The purpose of the daily circuit breaker is not to protect from any single trade — the stop loss does that. It protects against the compounding psychological and financial damage of continuing to trade after the mental edge is compromised.

---

### 7.5 Correlation and Concentration Checks

**Correlation check:** If the trader already has an open long position in Stock A, and Stock B is highly correlated (e.g. two large-cap banks, or two IT companies), a new long in Stock B is treated as doubling the same position. The AI either reduces the new position size by 50% or flags the correlation risk prominently.

**Sector concentration:** Maximum 40% of open positions in any single sector.

**Market direction concentration:** If all open positions are long and the Nifty is suddenly falling sharply, the AI flags the total directional exposure and recommends a hedge or reduction.

---

### 7.6 Liquidity Gate

Before any position size is approved, the AI verifies the instrument can handle the order.

- **Average daily volume check:** Position size must not exceed 0.5–1% of the average daily volume to avoid significant market impact
- **Spread check:** If the current spread is more than 2× the instrument's normal spread, position size is reduced (slippage cost rises significantly)
- **Thin order book detection:** If Level 2 shows insufficient orders to fill the position within an acceptable range, position is rejected

---

### 7.7 Risk Engine Output Object

```json
{
  "trade_approved": true,
  "position_size_shares": 320,
  "position_size_pct_capital": 6.4,
  "max_rupee_risk": 4800,
  "risk_pct_of_capital": 0.96,
  "stop_loss": 2442.00,
  "stop_type": "below_swing_low",
  "atr_stop_crosscheck": 2443.50,
  "stop_vs_atr": "consistent",
  "target_1": 2558.00,
  "target_2": 2635.00,
  "risk_reward": 2.31,
  "rr_gate": "passed",
  "correlation_risk": "low",
  "daily_loss_remaining_pct": 2.1,
  "circuit_breaker_status": "clear",
  "liquidity_gate": "passed"
}
```

---

## Layer 8 — Trade Plan Generation {#layer-8}

**Purpose:** Convert all upstream analysis into a complete, unambiguous, actionable trade plan. "Buy RELIANCE" is not a trade plan. The output of Layer 8 is.

---

### 8.1 Complete Trade Plan Structure

```
INSTRUMENT: Reliance Industries (NSE: RELIANCE)
ACTION: LONG (momentum breakout)
CONFIDENCE: 74%
REGIME: Weakly trending bullish

ENTRY:
  Zone: ₹2,480 – ₹2,510
  Trigger: 5m candle close above ₹2,512 with volume > 1.4× average
  Type: Buy on confirmation (not limit order — wait for close)

POSITION:
  Size: 320 shares
  Capital deployed: ~₹7,95,000 (~6.4%)
  Max risk: ₹4,800 (0.96% of capital)

STOP LOSS: ₹2,442
  Type: Below swing low formed at 10:22am
  Confirmation: ATR crosscheck also places stop at ₹2,443 — consistent

TARGETS:
  T1: ₹2,558 — prior resistance level
  Action at T1: Sell 160 shares, move stop to entry (₹2,512)
  T2: ₹2,635 — prior session high + 2R target
  Action at T2: Sell remaining 160 shares

RISK:REWARD:
  To T1: 1.62:1
  To T2 (blended on full position): 2.31:1

TIME PARAMETERS:
  Maximum hold time: Do not hold past 2:45pm
  Review checkpoint: If not at T1 by 1:30pm, evaluate exit

WHY THIS TRADE:
  - Bull flag pattern completing on 5m with volume buildup
  - All three timeframes (5m, 15m, 1h) showing bullish bias
  - Price at VWAP support after orderly pullback
  - Institutional buying detected in tape (3 large prints on ask in last 10 min)
  - Options: Put OI defending ₹2,450 level strongly
  - FII net buyers for 4 consecutive sessions

INVALIDATION CONDITIONS (exit immediately if any occur):
  1. 5m candle closes below ₹2,442 (stop loss hit)
  2. MACD crosses bearish before trade reaches T1
  3. India VIX spikes above 18 intraday
  4. Nifty breaks below its own session VWAP (market headwind)
  5. Volume dries up completely (less than 30% average) — no follow-through

RISK FLAGS:
  - Session phase is mid-morning (favorable)
  - No major events in next 2 hours (favorable)
  - Spread normal (favorable)
  - Previous trade was neutral (no confidence modifier applied)
```

---

### 8.2 Trade Type Variants

The trade plan structure adapts by trade type:

**Scalp trade:** Entry and stop are tighter (0.5× ATR), targets are smaller (T1 only, typically 1–1.5%), hold time measured in minutes. Maximum 3 scalps per hour.

**VWAP bounce trade:** Entry specifically at or within 0.1% of VWAP, stop just below VWAP, target at VWAP +1σ band. Validity tied to VWAP holding.

**Opening range breakout (ORB):** Entry at a close above the opening range high (9:15–9:30am range), stop just below the opening range low, target at 2× the opening range width projected up.

**News-driven trade:** Entry only after 2–3 candles of stabilization post-news, no momentum chasing during the initial spike, wider stops to account for elevated volatility.

---

## Layer 9 — Explainability, Alerts, and Self-Correction {#layer-9}

**Purpose:** Communicate every signal clearly, build a record of every output, and continuously improve accuracy through post-trade analysis.

---

### 9.1 Alert Format

**Mobile push notification (brevity required):**
```
📈 RELIANCE LONG | ₹2,480–2,510
SL: ₹2,442 | T1: ₹2,558 | T2: ₹2,635
Conf: 74% | R:R 2.3:1
Wait for 5m close confirmation
```

**In-app detailed view:** Full Layer 8 trade plan displayed with annotated chart overlay (entry zone, stop, targets drawn on the live chart), confidence breakdown by factor, and live P&L tracking once the trade is entered.

**Alert classification:**
- Priority alerts: High-confidence signals (>70%) in the trader's preferred instruments — push notification
- Watch alerts: Signal forming but confirmation pending — in-app notification only
- Risk alerts: Invalidation condition triggered, stop approaching, circuit breaker activating — push notification always, regardless of settings

---

### 9.2 Post-Trade Performance Tracking

Every signal generated by the AI is recorded, whether the trader acts on it or not.

**Data captured per signal:**

| Field | Description |
|---|---|
| Signal timestamp | When the signal was generated |
| Instrument | What was recommended |
| Direction | Long or short |
| Confidence score at generation | The score when fired |
| Regime at generation | What the market was doing |
| Entry price | Actual entry if taken |
| Exit price | Actual exit price |
| Stop hit / target hit / manual exit | How the trade ended |
| Weakest factor at generation | Which factor scored lowest |
| Time of day | Which session phase |
| Trade type | Breakout, reversal, VWAP bounce, etc. |

---

### 9.3 Self-Correction Loop

This is what separates an adaptive system from a static one.

**Accuracy tracking by dimension:**

| Dimension | Why It Matters |
|---|---|
| By instrument | Some assets are more predictable than others |
| By regime type | Identify which strategies fail in which conditions |
| By session phase | Opening signals may underperform afternoon signals |
| By trade type | Reversals may underperform breakouts for a given trader |
| By news environment | Signals near news events may consistently fail |
| By weekday | Options expiry Thursdays may behave differently |

**Weight adjustment protocol:**

When a factor's accuracy falls below its expected level:

- If a factor underperforms by more than 10 percentage points over 20+ signals, its weight is reduced by 15–20% and reallocated to outperforming factors
- If a strategy type has a below-50% win rate over 30+ signals in a specific regime, that strategy is suspended in that regime until recalibration
- Changes to weights are gradual (no single adjustment exceeds 20%) and require minimum sample sizes to prevent overfit to noise

**Accuracy targets by confidence band:**

| Confidence Band | Target Win Rate |
|---|---|
| 55–62% | 50–55% |
| 62–70% | 55–60% |
| 70–80% | 60–68% |
| 80–90% | 68–75% |
| 90%+ | 72–80% |

When actual win rates fall significantly below targets for a sustained period, the confidence thresholds for all signal bands are temporarily raised by 5–8 points (the system becomes more conservative) until accuracy recovers.

---

## Layer 10 — Anti-Error and System Integrity Framework {#layer-10}

**Purpose:** This layer does not generate signals. It exists to make the system as hard to fool, corrupt, and break as possible. Standard trading AI fails primarily in four ways: bad data, false confidence, model overfitting, and cascading errors. Layer 10 addresses all four.

---

### 10.1 Data Integrity Protocols

**Multi-source cross-validation:** For every critical data point, the AI reads from at least two independent sources and compares them.

- If two price feeds show different last prices and the difference exceeds 0.05%, both are flagged and a tertiary source is consulted
- If tick data and candle data disagree (a candle high that is impossible given the observed ticks), the anomaly is logged and the affected candle is quarantined from indicator calculations

**Statistical anomaly detection:**

Every incoming data point is tested against a rolling statistical model of what normal data looks like for that instrument:

- Price ticks outside ±5× ATR from the last valid price: Held as probable error
- Volume prints at zero or at 100× average: Flagged as bad data
- Timestamps that are out of sequence or duplicated: Filtered
- Any data point arriving with latency >5 seconds is considered stale and marked as such

**Exchange halt and suspension monitoring:**

The AI subscribes to exchange administrative feeds. If a stock is suspended, placed on the F&O ban list, or subject to a surveillance action, it is immediately removed from the active watchlist. Attempting to trade a suspended stock is a catastrophic error type.

---

### 10.2 Signal False Positive Reduction

**The five-gate confirmation framework:**

A signal must independently pass five gates before being output. No gate shares logic with another gate — they are genuinely independent tests.

| Gate | Tests |
|---|---|
| Technical gate | Technical score above threshold with minimum 2/3 timeframes aligned |
| Volume gate | Volume confirming the technical signal |
| Sentiment gate | No contradicting news or sentiment |
| Regime gate | Signal type is appropriate for current regime |
| Risk gate | Position survives all Layer 7 checks |

Failure in any single gate suppresses the signal entirely. There is no averaging, no partial credit, and no override.

**Cross-asset sanity check:**

Before outputting a bullish signal on an individual stock, the AI checks:
- Is the overall Nifty trend at this moment bullish, neutral, or bearish?
- Is the sector the stock belongs to performing in line with or better than the index?
- A bullish individual stock signal in a rapidly declining Nifty is marked with a HIGH CAUTION flag and position size is halved

**Pattern failure database:**

The system maintains a continuously updated database of conditions where specific patterns have historically failed. If the current setup matches a high-frequency failure pattern (e.g. "bull flag in ADX < 15 conditions has a 38% win rate in our historical data"), the signal confidence is reduced accordingly rather than being given the pattern's average score.

---

### 10.3 Market Manipulation Detection

High-frequency trading and algorithmic manipulation create patterns that look like legitimate signals but are specifically designed to trap retail traders.

**Stop hunt detection:**

A stop hunt is a brief, sharp price move below a well-known support level (where retail stops are clustered) followed by an immediate reversal. The AI detects this by:
- Identifying prior swing lows and round numbers where stops are likely to cluster
- Watching for wick candles that briefly pierce these levels on low volume
- Checking whether the "break" was absorbed and reversed within 1–2 candles
- If a stop hunt is detected below a support that was previously bullish, it may actually be a high-quality long entry (the stops have been cleared)

**Fake breakout detection:**

Many breakouts reverse within 2–3 candles. The AI requires confirmation — a breakout signal is not fired on the breakout candle alone. It requires:
- The candle to close above the breakout level (not just print through it intraday)
- Volume to be at least 1.3× average on the breakout candle
- The next candle to open above the breakout level (no immediate reversal)

**Thin market exploitation warning:**

During low-liquidity periods, a single large order can move the price significantly, creating a false signal. The AI applies the spread ratio and volume checks from Layer 1 particularly aggressively in these windows. Any signal generated in the dead zone (12–1:30pm) requires an additional 10-point confidence buffer.

---

### 10.4 Model Overfitting Safeguards

An AI that has been fine-tuned too aggressively on historical data will perform brilliantly in backtests and poorly in live trading. This is the most dangerous silent failure mode.

**Out-of-sample validation:**

When the self-correction loop adjusts factor weights, those weights are never validated on the same dataset that generated the adjustment. A holdout period of at least 10 trading sessions is required before confirming that a weight change improved performance.

**Minimum sample size enforcement:**

No weight change is made based on fewer than 30 signals in the relevant condition. Small sample sizes produce noisy results. The system is patient — it waits for statistical significance before modifying weights.

**Recency bias limits:**

The recency of a trade outcome affects how much it influences weight adjustments, but with a floor. Even very old signals carry some weight. This prevents the system from overreacting to a recent run of good or bad luck in a particular condition.

**Model freeze under market stress:**

When volatility is extreme (India VIX > 30 intraday) or when market conditions are unprecedented (more than 3 standard deviations from normal on multiple metrics simultaneously), the self-correction loop is frozen. Extreme events are not representative of normal conditions and should not permanently change how the system behaves in normal conditions.

---

### 10.5 Psychological Error Mitigation

The most sophisticated market analysis is meaningless if the trader doesn't follow the signals. The AI is designed to work with human psychology, not against it.

**FOMO protection:**

If a trade was signaled and the trader did not take it, and the price subsequently moved in the predicted direction, the AI does NOT show the missed profit prominently. Showing unrealized missed profits encourages traders to chase the next signal — exactly the behavior FOMO-prone traders need to avoid.

**Loss aversion override:**

The AI tracks whether a trader has a pattern of exiting winning trades too early (loss aversion causing premature profit-taking). If this pattern is detected, the AI sends a specific alert when a trade is approaching T1 ahead of schedule: "Trade performing well. Consider holding to target rather than taking early profit."

**Overconfidence check:**

After a sequence of winning trades (4 or more consecutive wins), the AI adds a visible banner: "Note: Recent win streak. Maintain normal position sizing. Markets are random sequences and a winning streak does not increase future accuracy."

**No second-guessing window:**

Once a trade is entered, the AI does not generate a new opposing signal on the same instrument for at least 30 minutes (unless an invalidation condition is triggered). This prevents the AI from confusing the trader with contradictory signals and encouraging reactive over-trading.

---

### 10.6 System Health Monitoring

**Real-time system diagnostics:**

| Metric | Normal Range | Alert Threshold |
|---|---|---|
| Data feed latency | < 500ms | > 2,000ms |
| Feed source agreement | Within 0.02% | Divergence > 0.1% |
| Signal generation rate | 2–8 signals/session | > 15 signals/session (overtrading flag) |
| Indicator calculation time | < 100ms | > 500ms |
| Daily layer error count | 0 | Any error in risk layers |

**Signal rate monitoring:**

If the system is generating more than 12–15 trade signals in a single session, something is wrong. Either the thresholds have drifted, market conditions have made everything appear like a signal, or there is a data quality problem making indicators behave abnormally. Excess signal generation triggers an automatic audit of the confidence thresholds and data quality checks.

**Daily system diagnostic report:**

At session end (3:30pm IST), the system compiles:
- Total signals generated today
- Signals that passed all gates vs were filtered
- Live accuracy vs expected accuracy by confidence band
- Any data quality events that occurred
- Any circuit breakers triggered
- Factor performance vs recent historical average
- Recommended weight adjustments for review (executed after minimum sample confirmation)

---

## Data Flow Summary {#data-flow-summary}

```
MARKET (exchanges, feeds, news, options)
         ↓
LAYER 1: Real-time market intake
(price, order flow, volume, global context, events, data quality)
         ↓
LAYER 2: Trader profile engine
(personalization, risk parameters, emotional flags applied)
         ↓
LAYER 3: Market regime detection
(trending/ranging/breakout/news-driven — strategy filter applied)
         ↓
LAYER 4: Multi-timeframe technical analysis
(EMA, MACD, RSI, volume, patterns, key levels → technical_score)
         ↓
LAYER 5: News and sentiment engine
(news, options OI, FII flows, social → sentiment_score)
         ↓
LAYER 6: Signal scoring and confidence engine
(weighted ensemble → confidence%, directional probability)
         ↓ [threshold check — reject if below modified minimum]
LAYER 7: Risk management engine
(position size, stop loss, R:R gate, circuit breakers, liquidity)
         ↓ [R:R gate — reject if below 1.5:1]
LAYER 8: Trade plan generation
(complete entry/exit/invalidation plan produced)
         ↓
LAYER 9: Explainability and alerts
(push notification, chart annotation, plain-English reasoning)
         ↓
LAYER 10: Anti-error framework (runs continuously across all layers)
(data integrity, false positive reduction, manipulation detection,
 model safeguards, psychological error mitigation, system health)
         ↑
SELF-CORRECTION LOOP (post-trade outcome feeds back into Layer 6 weights)
```

---

## Confidence Scoring Reference {#confidence-scoring-reference}

### Factor Sub-Score Rubric

**Technical Alignment (max 100):**
- All 3 timeframes aligned, strong signals: 85–100
- 2 of 3 timeframes aligned, moderate signals: 60–84
- 2 of 3 aligned, weak signals: 40–59
- Only 1 timeframe aligned: 0–39 (signal suppressed)

**Momentum (max 100):**
- CVD rising + tick velocity elevated + momentum score > 60: 80–100
- CVD rising + normal velocity: 60–79
- Flat CVD, low velocity: 30–59
- CVD declining (divergence with price): 0–29

**Volume (max 100):**
- Volume > 2× average on signal candle, confirming direction: 85–100
- Volume 1.3–2× average: 65–84
- Volume near average: 45–64
- Volume below average: 0–44

**Sentiment (max 100):**
- Strong positive news + institutional buying + bullish options data: 85–100
- Mild positive or neutral: 55–75
- Mixed signals: 35–54
- Contradictory (negative news vs bullish technicals): 0–34

**Key Level Confluence (max 100):**
- 4+ levels overlapping: 90–100
- 3 levels overlapping: 75–89
- 2 levels overlapping: 55–74
- 1 level: 35–54
- No major level nearby: 15–34

---

## Invalidation Triggers Reference {#invalidation-triggers}

Every trade generated by the system comes with a predefined set of invalidation conditions. If any trigger fires after trade entry, the AI sends an immediate exit alert.

**Universal invalidation triggers (apply to all trades):**
- Stop loss level hit
- India VIX spikes intraday by more than 30% of its opening level
- Nifty breaks below its session VWAP in a confirmed way (2+ candle closes below)
- Volume disappears — three consecutive candles with less than 30% of average volume (price is drifting, not trending)
- The news environment changes materially (a significant negative headline drops during the trade)

**Bullish trade specific invalidations:**
- EMA 9 crosses below EMA 21 on the 5m chart
- MACD histogram turns negative on the 15m chart
- Price closes below the entry candle's low
- Buy pressure ratio drops below 0.40 (sellers have taken over)
- High-volume candle forms in the opposite direction (counter-trend institutional activity)

**Breakout trade specific invalidations:**
- Price reclaims back inside the breakout level on a volume candle
- Opening range low broken (for ORB trades)
- Failed follow-through after 3 candles (price not progressing toward T1)

**Reversal trade specific invalidations:**
- Prior low broken (the bottom was not in)
- RSI continues to make lower lows (no momentum divergence forming)
- Volume picks up in the direction of the original trend (sellers returning)

---

*Document version 1.0 — This is a living document. All layer parameters should be reviewed and calibrated against live performance data on a monthly basis. Confidence thresholds and factor weights are starting-point recommendations and should be adjusted based on the self-correction loop's output over the first 200+ live signals.*

---
**END OF DOCUMENT**


---

# Section 15 — Development Roadmap and Implementation Strategy {#section-15}

**Purpose:** Define the staged implementation process for transforming the architecture into a reliable, production-ready AI investment and trading intelligence platform. This section focuses on execution order, infrastructure priorities, safety-first development, and practical system scaling.

---

## 15.1 Development Philosophy

Most AI trading systems fail because they start with:
- Large AI models
- Price prediction attempts
- Fancy dashboards
- Over-optimized backtests

before building:
- Reliable data infrastructure
- Risk systems
- Decision logic
- Explainability
- Market regime understanding

This architecture follows the opposite approach.

### Core Principle

The system must first become:
1. Reliable
2. Explainable
3. Risk-aware
4. Consistent

before becoming:
- Autonomous
- Predictive
- Aggressively optimized

The foundation is a financial decision engine — not a chatbot.

---

## 15.2 Phase 1 — Define the MVP

### Objective

Reduce system scope to a manageable and testable Version 1.

The complete vision is institutional-scale. Attempting to build all layers simultaneously creates excessive complexity, debugging difficulty, and unreliable outputs.

---

### Recommended V1 Scope

#### Supported Assets
- Stocks
- Crypto
- Nifty/Sensex

#### Deferred Assets
- Forex
- Futures
- Complex options strategies
- Commodities

These can be integrated after the core engine becomes stable.

---

### Recommended Initial Trading Styles

Focus initially on:
- Long-term investing
- Swing trading

Avoid:
- High-frequency scalping
- Ultra-low latency day trading

### Why

These strategies:
- Require lower execution speed
- Are easier to model probabilistically
- Have cleaner signal structures
- Reduce infrastructure complexity
- Produce more reliable early-stage outputs

---

## 15.3 Phase 2 — Build the Data Infrastructure

**This is the most important stage of the entire project.**

The system's intelligence quality is directly limited by:
- Data quality
- Latency
- Coverage
- Reliability

---

### Core Pipelines

#### Market Data Pipeline
Collect:
- OHLCV
- Tick data
- Volume
- Order flow
- Market depth
- Technical indicators

Suggested providers:
- Polygon.io
- Finnhub
- Alpha Vantage
- Binance API

---

#### News Pipeline

Track:
- Earnings
- Financial news
- Government announcements
- Macroeconomic events
- Corporate filings

Suggested sources:
- Reuters
- NewsAPI
- GDELT

---

#### Sentiment Pipeline

Analyze:
- X/Twitter
- Reddit
- StockTwits
- Telegram communities

Convert sentiment into:
- Bullish score
- Fear score
- Momentum sentiment
- Retail mania indicators

---

#### Portfolio Pipeline

Track:
- Holdings
- P&L
- Cash reserves
- Exposure
- Sector allocation
- Correlation risk

---

#### Macro Pipeline

Track:
- Interest rates
- CPI
- Bond yields
- Dollar Index (DXY)
- Oil prices
- VIX
- Central bank events

---

## 15.4 Phase 3 — Build the Decision Engine

### Important Principle

Do NOT start with AI prediction models.

The system should initially operate using:
- Rule-based logic
- Scoring systems
- Probability frameworks
- Regime filters

---

### Example

Instead of:
“AI predicts BTC will rise.”

Use:
- BTC above 200 EMA
- ETF inflows positive
- Macro environment risk-on
- Momentum healthy

Then:
Generate bullish probability.

---

### Why Rule-Based Systems First

Benefits:
- Easier debugging
- Safer outputs
- Explainable reasoning
- Better risk management
- Faster iteration cycles

Machine learning should enhance the system later — not define its foundation.

---

## 15.5 Phase 4 — Build the Scoring System

Everything in the system should eventually become:
- Quantified
- Weighted
- Explainable

---

### Example Weighted Engine

| Engine | Score |
|---|---|
| Technical | 82 |
| Fundamentals | 76 |
| Sentiment | 68 |
| Macro | 71 |
| Risk | 80 |

These scores combine into:
- Weighted confidence
- Directional probability
- Trade quality grading

---

### Why This Matters

A scoring architecture creates:
- Transparency
- Explainability
- Measurability
- Continuous optimization capability

This becomes the central reasoning engine of the system.

---

## 15.6 Phase 5 — Market Regime Engine

Before generating any recommendation, the AI must classify market conditions.

---

### Regime Types

- Bullish trending
- Bearish trending
- Sideways/choppy
- High volatility
- Risk-on
- Risk-off
- News-driven

---

### Why Regime Detection Matters

Different strategies fail in different conditions.

Examples:
- Momentum strategies fail in sideways markets
- Mean reversion strategies fail during strong trends

Regime detection dramatically improves:
- Signal quality
- Trade filtering
- Risk-adjusted returns

---

## 15.7 Phase 6 — Portfolio Intelligence Layer

The AI must understand the trader before recommending trades.

---

### Before Any Recommendation

The system checks:
- Existing holdings
- Sector exposure
- Correlation risk
- Portfolio volatility
- Available cash
- Risk tolerance

---

### Example

Instead of simply recommending:
“Buy Reliance”

The AI evaluates:
- Does the user already hold energy stocks?
- Is portfolio concentration already high?
- Does this fit the user's strategy and volatility profile?

This transforms the system from a signal generator into a portfolio intelligence engine.

---

## 15.8 Phase 7 — Explainability Framework

Trust is one of the platform's biggest competitive advantages.

Every recommendation should explain:
- Why the trade exists
- What supports it
- What risks exist
- What invalidates the setup

---

### Example Output

Action: BUY

Confidence: 74%

Reasons:
- Bullish macro environment
- Institutional accumulation
- Positive earnings momentum

Risks:
- High volatility
- Upcoming Fed meeting

Invalidation:
- Break below support
- Negative macro surprise

---

## 15.9 Phase 8 — Backtesting and Validation

Before deployment:
- Every strategy must be tested across multiple market environments

---

### Required Test Environments

- Bull markets
- Bear markets
- Sideways periods
- Volatility spikes
- Crisis events
- News-heavy sessions

---

### Core Metrics

#### Performance Metrics
- Win rate
- CAGR
- Profit factor
- Sharpe ratio
- Max drawdown

#### Reliability Metrics
- Accuracy by regime
- Accuracy by asset
- Accuracy by timeframe
- Accuracy by strategy type

---

## 15.10 Phase 9 — AI and Machine Learning Integration

Only after:
- Data systems
- Risk systems
- Decision logic
- Scoring engines
- Backtesting

are stable should advanced AI models be introduced.

---

### Recommended AI Uses

Use AI for:
- Pattern recognition
- Sentiment understanding
- Dynamic weighting
- Strategy adaptation
- Context reasoning

Avoid:
- Blind price prediction
- Black-box trading decisions

---

### Suggested Models

- LSTM
- Transformers
- XGBoost
- Reinforcement learning

These should function as enhancement layers rather than the system core.

---

## 15.11 Phase 10 — Memory and Personalization System

The AI should continuously remember and adapt to:
- User preferences
- Trading history
- Risk tolerance
- Behavioral tendencies
- Portfolio evolution

This creates:
- Personalization
- Adaptive risk management
- Better recommendations over time

---

## 15.12 Phase 11 — Safety and Guardrail Systems

The AI must sometimes refuse to generate trades.

This is a feature — not a weakness.

---

### Safety Controls

Prevent:
- Excessive leverage
- Emotional overtrading
- Portfolio overconcentration
- Correlated exposure overload
- Volatility overexposure

---

### Example Output

“NO TRADE RECOMMENDED”

Reasons:
- Market regime unstable
- Risk/reward insufficient
- Portfolio overexposed
- Volatility elevated

A disciplined no-trade decision is often higher quality than forcing activity.

---

## 15.13 Phase 12 — UI and User Experience

The platform should prioritize:
- Clarity
- Simplicity
- Explainability
- Actionability

Avoid:
- Excessive indicators
- Overwhelming dashboards
- Complex institutional jargon

Users should immediately understand:
- What the AI recommends
- Why it recommends it
- How risky it is
- What invalidates it

---

## 15.14 Suggested Technology Stack

| Component | Recommended Stack |
|---|---|
| Backend | Python + FastAPI |
| AI/ML | PyTorch, TensorFlow |
| Data Processing | Pandas, NumPy |
| Streaming | Apache Kafka (later stage) |
| Database | PostgreSQL |
| Caching | Redis |
| Vector Memory | Pinecone / Weaviate |
| Frontend | React + Next.js + Tailwind |
| Charts | TradingView Lightweight Charts |

---

## 15.15 MVP Functional Requirements

The first working version should successfully:
- Understand user profile
- Detect market regime
- Analyze technical structure
- Analyze macro/sentiment context
- Score opportunities
- Evaluate portfolio fit
- Generate risk-managed trade plans
- Explain decisions clearly

This alone is already a highly advanced platform.

---

## 15.16 Final Design Principle

The system's greatest strength should not be:
- Perfect predictions
- Extreme complexity
- Massive AI models

Its greatest strength should be:

### Rational Decision Quality

The platform should consistently feel:
- Intelligent
- Disciplined
- Explainable
- Risk-aware
- Trustworthy

Institutional-level trust and consistency matter more than unrealistic prediction accuracy.
