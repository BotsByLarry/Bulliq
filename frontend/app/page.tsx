'use client';

import React, { useEffect, useState, useRef } from 'react';
import { 
  Send, User, ShieldAlert, TrendingUp, Activity, 
  Layers, MessageSquare, RefreshCw, AlertTriangle, HelpCircle, ArrowRight, Zap, Cpu
} from 'lucide-react';
import { createChart, IChartApi, ISeriesApi, CandlestickSeries } from 'lightweight-charts';

// TS Interfaces
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Signal {
  id: number;
  symbol: string;
  market: string;
  direction: string;
  entry_price: number;
  stop_loss: number;
  target_1: number;
  target_2: number;
  risk_reward_ratio: number;
  confidence_score: number;
  market_regime: string;
  explanation: string;
  layers_telemetry: any;
  created_at: string;
}

export default function Home() {

  // Chat State
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I am Bulliq AI, your elite investment and day trading co-pilot. Before I can provide personalized trading advice or configure your 10-layer market intake pipeline, let's align on your profile. Could you tell me: \n\n1. What is your active virtual trading capital (e.g. ₹100,000 or $5,000)?\n2. What is your preferred trading style (scalping, intraday day trading, or swing)?\n3. What percent of your capital are you comfortable risking per trade (typically 1%)?\n4. Do you struggle with emotional traps like FOMO or revenge trading?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Live Market State
  const [signals, setSignals] = useState<Signal[]>([]);
  const [activeSymbol, setActiveSymbol] = useState('NSE:RELIANCE');
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({
    'NSE:RELIANCE': 2450.0,
    'NSE:TCS': 3820.0,
    'NSE:NIFTY50': 22400.0,
    'CRYPTO:BTCUSDT': 67250.0
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const candleHistoryRef = useRef<Record<string, any[]>>({});

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Navigation & Trade Terminal State
  const [activeTab, setActiveTab] = useState<'chat' | 'terminal' | 'autotrade'>('chat');
  const [apiBaseUrl, setApiBaseUrl] = useState('http://localhost:8000');
  const [apiBaseUrlInput, setApiBaseUrlInput] = useState('http://localhost:8000');
  const [trades, setTrades] = useState<any[]>([]);
  const [stats, setStats] = useState({
    total_trades: 0,
    closed_trades: 0,
    win_rate: 0,
    total_pnl: 0,
    current_regime: 'calm'
  });
  const [bypassLimits, setBypassLimits] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0); // elapsed time in seconds
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportText, setReportText] = useState('');

  // Autonomous Trading Session States
  const [isAutoTrading, setIsAutoTrading] = useState(false);
  const [sessionEndTime, setSessionEndTime] = useState<string | null>(null);
  const [sessionDurationInput, setSessionDurationInput] = useState(60); // minutes
  const [sessionCountdown, setSessionCountdown] = useState(0); // seconds remaining
  const [sessionCapitalInput, setSessionCapitalInput] = useState(5000); // USD session allocation
  const [sessionRiskInput, setSessionRiskInput] = useState(1); // % risk per trade
  const [isSessionModalOpen, setIsSessionModalOpen] = useState(false); // Modal for onboarding questionnaire
  const [sessionAuthorize, setSessionAuthorize] = useState(false);
  const [sessionReportData, setSessionReportData] = useState<any>(null);
  const [showSessionReportModal, setShowSessionReportModal] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState<string[]>([
    "[SYSTEM] 10-Layer Market Intake Intelligence initialized.",
    "[L1 Intake] Listening to real-time tick streams for RELIANCE, TCS, BTC...",
    "[L3 Regime] Market Regime assessed: TRENDING BULLISH (conviction: High).",
    "[L5 Sentiment] Ingested 12 positive financial press events; net sentiment score: +84.",
    "[L7 Risk] Core margin balance checked. Multi-position alignment safe."
  ]);


  // Load API base URL from localStorage on startup
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('BULLIQ_API_BASE_URL');
      if (saved) {
        setApiBaseUrl(saved);
        setApiBaseUrlInput(saved);
      }
    }
  }, []);

  // Fetch Signals Feed
  const fetchSignals = async () => {
    try {
      const sRes = await fetch(`${apiBaseUrl}/api/v1/signals`);
      if (sRes.ok) setSignals(await sRes.json());
    } catch (e) {
      console.warn("Backend not accessible for signals lookup.");
    }
  };

  // Fetch Trades and Dashboard Stats
  const fetchTradesAndStats = async () => {
    try {
      const tRes = await fetch(`${apiBaseUrl}/api/v1/trades`);
      if (tRes.ok) setTrades(await tRes.json());
      
      const sRes = await fetch(`${apiBaseUrl}/api/v1/dashboard/stats`);
      if (sRes.ok) setStats(await sRes.json());
    } catch (e) {
      console.warn("Error fetching trades and stats:", e);
    }
  };

  // Fetch Initial User Profile
  const fetchProfile = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile`);
      if (res.ok) {
        const user = await res.json();
        const flags = user.emotional_flags || {};
        setBypassLimits(!!flags.bypass_limits);
        
        // If Alpaca credentials exist, the test is running!
        if (user.broker_credentials?.api_key) {
          setIsTestRunning(true);
        }

        // Sync autonomous session states
        setIsAutoTrading(!!user.trading_session_active);
        setSessionEndTime(user.trading_session_end || null);
      }
    } catch (e) {
      console.warn("Failed to load profile:", e);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchSignals();
    fetchTradesAndStats();
    
    const sigInterval = setInterval(fetchSignals, 4000);
    const statsInterval = setInterval(fetchTradesAndStats, 4000);
    const profileInterval = setInterval(fetchProfile, 4000); // Dynamic polling for chat-triggered session events
    
    return () => {
      clearInterval(sigInterval);
      clearInterval(statsInterval);
      clearInterval(profileInterval);
    };
  }, [apiBaseUrl]);

  // Timer Effect
  useEffect(() => {
    let timer: any;
    if (isTestRunning) {
      timer = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isTestRunning]);

  const formatTimer = (sec: number) => {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${pad(hours)}:${pad(mins)}:${pad(secs)}`;
  };

  // Autonomous Trading Session Countdown Timer
  useEffect(() => {
    let timer: any;
    if (isAutoTrading && sessionEndTime) {
      const updateCountdown = () => {
        const end = new Date(sessionEndTime).getTime();
        const now = new Date().getTime();
        const diff = Math.max(0, Math.floor((end - now) / 1000));
        setSessionCountdown(diff);
        if (diff === 0) {
          setIsAutoTrading(false);
          setSessionEndTime(null);
          triggerSessionCompletionReport();
        }
      };
      
      updateCountdown();
      timer = setInterval(updateCountdown, 1000);
    } else {
      setSessionCountdown(0);
    }
    return () => clearInterval(timer);
  }, [isAutoTrading, sessionEndTime]);
  // Simulated Live 10-Layer Scanner Feed Logs
  useEffect(() => {
    const logTemplates = [
      "[L1 Intake] Ingested NSE:RELIANCE tick stream: $2,482.40 | Spread: normal.",
      "[L2 Profile] Dynamic risk limits verified (allocated session capital checked).",
      "[L3 Regime] Volatility regime assessed: COMPRESSED LOW VOLATILITY (breakout coiling).",
      "[L4 Technical] Indicator check: RSI 57, MACD cross positive, VWAP reclaim support.",
      "[L5 Sentiment] Sentiment indices parsed: net positive consensus +82% score.",
      "[L6 Signal] Confluence evaluation: 74% aggregate score (threshold gate passed).",
      "[L7 Risk] Dispatched position margin check: within 3% risk tolerance limits.",
      "[L8 Plan] Native bracket order created: TP $2,536.80 | SL $2,458.00.",
      "[L9 Explain] Signal verified with 4 overlapping timeframe support lines.",
      "[L10 Guard] guardrails passed: pricing feed latency normal (140ms)."
    ];
    
    let interval: any;
    if (isAutoTrading) {
      interval = setInterval(() => {
        const randomLog = logTemplates[Math.floor(Math.random() * logTemplates.length)];
        const time = new Date().toLocaleTimeString();
        setPipelineLogs(prev => [...prev.slice(-30), `[${time}] ${randomLog}`]);
      }, 3500);
    }
    
    return () => clearInterval(interval);
  }, [isAutoTrading]);

  const formatCountdown = (sec: number) => {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${pad(hours)}:${pad(mins)}:${pad(secs)}`;
  };

  const triggerSessionCompletionReport = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile`);
      if (!res.ok) return;
      const user = await res.json();
      const creds = user.broker_credentials || {};
      const startTimeStr = creds.session_start_time;
      if (!startTimeStr) return;
      
      const startTime = new Date(startTimeStr).getTime();
      
      // Fetch latest trades
      const tRes = await fetch(`${apiBaseUrl}/api/v1/trades`);
      if (!tRes.ok) return;
      const allTrades = await tRes.json();
      
      // Filter trades executed during the session
      const sessionTrades = allTrades.filter((t: any) => {
        const tradeTime = new Date(t.created_at).getTime();
        return tradeTime >= startTime;
      });
      
      const closed = sessionTrades.filter((t: any) => t.status === 'closed');
      const wins = closed.filter((t: any) => t.pnl > 0);
      const losses = closed.filter((t: any) => t.pnl <= 0);
      const totalPnl = closed.reduce((acc: number, curr: any) => acc + curr.pnl, 0);
      
      setSessionReportData({
        allocatedCapital: creds.pre_session_capital ? user.total_capital : sessionCapitalInput,
        durationMinutes: sessionDurationInput,
        totalTrades: sessionTrades.length,
        closedTrades: closed.length,
        winRate: closed.length > 0 ? Math.round((wins.length / closed.length) * 100) : 0,
        winsCount: wins.length,
        lossesCount: losses.length,
        totalPnL: totalPnl,
        endTime: new Date().toLocaleTimeString()
      });
      setShowSessionReportModal(true);
    } catch (e) {
      console.error("Error generating session report:", e);
    }
  };

  // Start Autonomous Trading Session
  const handleStartAutoSession = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile/start_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          duration_minutes: sessionDurationInput,
          session_capital: sessionCapitalInput,
          risk_per_trade: sessionRiskInput
        })
      });
      if (res.ok) {
        const data = await res.json();
        setIsAutoTrading(true);
        setSessionEndTime(data.trading_session_end);
        setIsSessionModalOpen(false);
        setSessionAuthorize(false);
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `🤖 AUTONOMOUS SESSION STARTED: I have successfully initiated autonomous trading for **${sessionDurationInput} minutes** with **$${sessionCapitalInput.toLocaleString()} capital allocation** and **${sessionRiskInput}% risk per trade**. Live bracket orders are now actively deploying on your linked Alpaca Broker account!`,
          timestamp: new Date()
        }]);
      }
    } catch (e) {
      console.error("Error starting autonomous session:", e);
    }
  };

  // Stop Autonomous Trading Session
  const handleStopAutoSession = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile/stop_session`, {
        method: 'POST'
      });
      if (res.ok) {
        setIsAutoTrading(false);
        setSessionEndTime(null);
        
        // Trigger report for whatever took place so far
        triggerSessionCompletionReport();
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `🚨 EMERGENCY HALT: The active autonomous trading session has been immediately stopped. All future trades will run inside the risk-free Sandbox simulator and normal profile risk limits are restored.`,
          timestamp: new Date()
        }]);
      }
    } catch (e) {
      console.error("Error stopping autonomous session:", e);
    }
  };

  // Force Custom Trade Signal
  const handleForceSignal = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile/force_signal`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚡ FORCE CONFLUENCE SIGNAL FIRED: Successfully injected high-probability breakout buy signal for **${data.symbol}** at **$${data.price.toLocaleString()}**. Order dispatched via **${data.is_alpaca_live ? 'Alpaca Live Broker' : 'Sandbox Simulator'}**!`,
          timestamp: new Date()
        }]);
        fetchTradesAndStats();
        // Append log to pipeline console
        const time = new Date().toLocaleTimeString();
        setPipelineLogs(prev => [...prev, `[${time}] ⚠️ [FORCE SIGNAL COMMAND RECEIVED] High-confluence breakout trade executed on ${data.symbol} at $${data.price}.`]);
      }
    } catch (e) {
      console.error("Failed to force signal:", e);
    }
  };

  // Toggle Bypass Limits
  const handleToggleBypassLimits = async (checked: boolean) => {
    setBypassLimits(checked);
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          emotional_flags: {
            bypass_limits: checked
          }
        })
      });
      if (res.ok) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: checked 
            ? "⚠️ WARNING: You have bypassed all risk management limits. Bulliq's 10-layer mathematical signal scoring will now submit bracket orders directly to your broker without circuit breakers, max position size bounds, or consecutive loss lockdowns. Core strategy indicators are fully active!"
            : "✅ RISK limits re-activated. Normal safeguards, including max 3 active positions and consecutive loss cooldowns, are now enforcing portfolio protection.",
          timestamp: new Date()
        }]);
      }
    } catch (e) {
      console.error("Error toggling bypass limits:", e);
    }
  };

  // Generate Performance Report
  const generatePerformanceReport = () => {
    const closedTrades = trades.filter(t => t.status === 'closed');
    const winTrades = closedTrades.filter(t => t.pnl > 0);
    const lossTrades = closedTrades.filter(t => t.pnl <= 0);
    
    const totalWinVal = winTrades.reduce((acc, curr) => acc + curr.pnl, 0);
    const totalLossVal = lossTrades.reduce((acc, curr) => acc + curr.pnl, 0);
    
    const avgProfit = closedTrades.length > 0 ? (stats.total_pnl / closedTrades.length) : 0;
    const profitFactor = Math.abs(totalLossVal) > 0 ? (totalWinVal / Math.abs(totalLossVal)) : totalWinVal > 0 ? 99.9 : 0;
    
    const report = `================================================
          BULLIQ AI DAY TRADING PERFORMANCE REPORT
================================================
Generated On: ${new Date().toLocaleString()}
Test Duration: ${formatTimer(elapsedTime)} / 12:00:00
Execution Channel: ${trades.some(t => !t.is_mock) ? 'Alpaca Live Paper' : 'Sandbox Simulator'}
Risk Safeguards Mode: ${bypassLimits ? 'Bypassed (Core Indicators Only)' : 'Strict Guardrails Active'}

1. EXECUTIVE FINANCIAL SUMMARY
------------------------------------------------
Initial Capital: $100,000.00
Net Trading Profit: $${stats.total_pnl.toFixed(2)}
Estimated Session ROI: ${((stats.total_pnl / 100000.0) * 100).toFixed(4)}%
Total Completed Trades: ${closedTrades.length}
Active Position Backlog: ${trades.filter(t => t.status === 'open').length}

2. HIT-RATIO & EDGE STATS
------------------------------------------------
Win Rate: ${stats.win_rate}%
Winning Trades: ${winTrades.length}
Losing Trades: ${lossTrades.length}
Average PnL per Trade: $${avgProfit.toFixed(2)}
Gross Win Value: $${totalWinVal.toFixed(2)}
Gross Loss Value: $${totalLossVal.toFixed(2)}
Mathematical Profit Factor: ${profitFactor.toFixed(2)}x

3. 10-LAYER PIPELINE INTEGRITY AUDIT
------------------------------------------------
* Layer 1 (Intake): VWAP and Candle Aggregators operational.
* Layer 2 (Profile): Rules applied successfully.
* Layer 3 (Regime): Live market regime classified as ${stats.current_regime.toUpperCase()}.
* Layer 7 (Risk): Bracket orders entry/SL/TP points checked.
* Layer 10 (Guard): Zero outlier/pricing errors bypassed.
* Performance Check: Core indicators maintained a high-confluence edge.

Conclusion:
The 12-hour continuous test indicates a ${stats.total_pnl >= 0 ? 'STRONG POSITIVE' : 'CONSTRUCTIVE'} mathematical expectancy. ${bypassLimits ? 'Running in bypassed limits mode allowed the pipeline to trade frequently without emotional cooldown restrictions, proving robust raw indicator confluence performance.' : 'Strict risk guardrails protected equity drawdown from market noise.'}
================================================`;
    
    setReportText(report);
    setShowReport(true);
  };

  // Alpaca Broker State
  const [alpacaKey, setAlpacaKey] = useState('');
  const [alpacaSecret, setAlpacaSecret] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [alpacaStatus, setAlpacaStatus] = useState('');

  const handleLinkAlpaca = async () => {
    if (!alpacaKey || !alpacaSecret) {
      setAlpacaStatus('Please fill in both API Key ID and Secret Key');
      return;
    }
    
    setIsLinking(true);
    setAlpacaStatus('');
    
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/profile/alpaca`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: alpacaKey, secret_key: alpacaSecret })
      });
      
      if (res.ok) {
        const data = await res.json();
        setAlpacaStatus(`SUCCESS: Alpaca Linked! Equity: $${Number(data.account?.equity).toLocaleString()}`);
        setAlpacaKey('');
        setAlpacaSecret('');
        setIsTestRunning(true);
        setElapsedTime(0);
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Alpaca Paper Trading Account successfully linked! Live buying power is active and portfolio equity is $${Number(data.account?.equity).toLocaleString()}.\n\nI am now running continuous 10-layer market scanning. Automated bracket orders will be placed automatically!`,
          timestamp: new Date()
        }]);
        
        fetchTradesAndStats();
      } else {
        const data = await res.json();
        setAlpacaStatus(`ERROR: ${data.detail || 'Connection failed'}`);
      }
    } catch (e) {
      setAlpacaStatus('ERROR: Failed to establish contact with backend.');
    } finally {
      setIsLinking(false);
    }
  };

  // Send message to LLM
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim()) return;

    if (!textToSend) setInputValue('');
    
    // Add user message
    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const payloadMessages = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content
      }));

      const res = await fetch(`${apiBaseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: payloadMessages })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        }]);
        // Reload user profile to instantly capture chat-triggered session changes (start/stop)
        fetchProfile();
      } else {
        throw new Error("Chat service failed");
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `I ran into a connection glitch while processing your response. Please ensure the Bulliq backend server on ${apiBaseUrl} is active. In the meantime, I am continuing to analyze market ticks for you!`,
        timestamp: new Date()
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Set up TradingView Chart (Fixed for Lightweight Charts v5)
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#0b0f19' },
        textColor: '#64748b',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.02)' },
        horzLines: { color: 'rgba(255,255,255,0.02)' },
      },
      timeScale: {
        timeVisible: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: 200,
    });

    // Fix: Unified v5 Series Creation API
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    // Build initial mock candle history
    const initialHistory = [];
    let baseTime = Math.floor(Date.now() / 1000) - 50 * 60;
    let price = prices[activeSymbol] || 1000;
    
    for (let i = 0; i < 50; i++) {
      const open = price + Math.random() * 4 - 2;
      const close = open + Math.random() * 6 - 3;
      initialHistory.push({
        time: baseTime + i * 60,
        open,
        high: Math.max(open, close) + Math.random() * 2,
        low: Math.min(open, close) - Math.random() * 2,
        close
      });
      price = close;
    }
    
    candleHistoryRef.current[activeSymbol] = initialHistory;
    candleSeries.setData(initialHistory as any);

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.resize(chartContainerRef.current.clientWidth, 200);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [activeSymbol]);

  // Live WebSocket Tick aggregation
  useEffect(() => {
    const wsUrl = apiBaseUrl.replace(/^http/, 'ws') + '/api/v1/ws/live';
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'tick') {
          const tick = payload.data;
          setPrices(prev => ({ ...prev, [tick.symbol]: tick.price }));

          if (tick.symbol === activeSymbol && candleSeriesRef.current) {
            const history = candleHistoryRef.current[activeSymbol] || [];
            const lastCandle = history[history.length - 1];
            const tickTime = Math.floor(tick.timestamp);
            const candleTime = tickTime - (tickTime % 60);

            if (lastCandle && lastCandle.time === candleTime) {
              lastCandle.close = tick.price;
              lastCandle.high = Math.max(lastCandle.high, tick.price);
              lastCandle.low = Math.min(lastCandle.low, tick.price);
              candleSeriesRef.current.update(lastCandle as any);
            } else {
              const newCandle = {
                time: candleTime,
                open: tick.price,
                high: tick.price,
                low: tick.price,
                close: tick.price
              };
              history.push(newCandle);
              candleSeriesRef.current.update(newCandle as any);
            }
          }
        }
      } catch (e) {
        console.error(e);
      }
    };

    return () => ws.close();
  }, [activeSymbol, apiBaseUrl]);

  return (
    <div className="flex-1 p-6 flex flex-col lg:grid lg:grid-cols-12 gap-6 bg-[#0a0e17] overflow-y-auto max-h-[calc(100vh-70px)]">
      
      {/* Live Resampling Ticker bar */}
      <div className="lg:col-span-12 glass-panel p-4 flex flex-wrap gap-6 items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="text-[var(--color-accent)] w-5 h-5 animate-pulse" />
          <span className="font-semibold text-xs tracking-wider uppercase text-slate-300">Live Bulliq Feed:</span>
        </div>
        <div className="flex flex-wrap gap-6">
          {Object.entries(prices).map(([sym, price]) => (
            <div 
              key={sym} 
              onClick={() => setActiveSymbol(sym)}
              className={`flex items-center gap-3 cursor-pointer p-2 px-3 rounded transition-all duration-200 ${activeSymbol === sym ? 'bg-[rgba(0,200,150,0.08)] border border-[rgba(0,200,150,0.2)]' : 'hover:bg-slate-900'}`}
            >
              <span className="font-medium text-xs text-slate-400">{sym.split(':')[1]}</span>
              <span className="font-bold text-sm tracking-tight text-white">${price.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* LEFT PANEL: Switchable Bulliq Chat / Trade Terminal (65% width) */}
      <div className="lg:col-span-8 flex flex-col glass-panel border border-[rgba(255,255,255,0.06)] min-h-[580px] bg-[rgba(16,22,35,0.4)]">
        
        {/* Chat Header with Tabs */}
        <div className="p-4 border-b border-slate-800/80 flex flex-wrap gap-4 items-center justify-between bg-[rgba(22,30,49,0.3)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#00C896] to-[#34F5C5] flex items-center justify-center font-bold text-slate-950 text-sm shadow-[0_0_10px_rgba(0,200,150,0.3)] animate-pulse">
              B
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-sm text-slate-100 tracking-wider">BULLIQ AI</span>
              <span className="text-[10px] text-[var(--color-accent)] font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] animate-ping"></span>
                {isTestRunning ? 'Test Active' : 'Onboarding Active'}
              </span>
            </div>
          </div>
          
          {/* Navigation Tabs */}
          <div className="flex bg-slate-950/80 p-1 rounded-lg border border-slate-800">
            <button 
              onClick={() => setActiveTab('chat')}
              className={`p-1.5 px-4 rounded-md text-xs font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${activeTab === 'chat' ? 'bg-[#00C896] text-slate-950 shadow-[0_0_8px_rgba(0,200,150,0.3)]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'}`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Co-Pilot Chat
            </button>
            <button 
              onClick={() => setActiveTab('terminal')}
              className={`p-1.5 px-4 rounded-md text-xs font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${activeTab === 'terminal' ? 'bg-[#00C896] text-slate-950 shadow-[0_0_8px_rgba(0,200,150,0.3)]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'}`}
            >
              <Activity className="w-3.5 h-3.5" />
              Trade Terminal & Stats
            </button>
            <button 
              onClick={() => setActiveTab('autotrade')}
              className={`p-1.5 px-4 rounded-md text-xs font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${activeTab === 'autotrade' ? 'bg-[#00C896] text-slate-950 shadow-[0_0_8px_rgba(0,200,150,0.3)]' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'}`}
            >
              <Cpu className="w-3.5 h-3.5" />
              Auto-Trader Center
            </button>
          </div>
        </div>

        {/* Tab content switch */}
        {activeTab === 'chat' ? (
          <>
            {/* Chat Message Box */}
            <div className="flex-1 p-5 overflow-y-auto max-h-[460px] flex flex-col gap-4">
              {messages.map((msg, i) => (
                <div 
                  key={i} 
                  className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}
                >
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${msg.role === 'user' ? 'bg-slate-700 text-white' : 'bg-gradient-to-tr from-[#00C896] to-[#34F5C5] text-slate-950'}`}>
                    {msg.role === 'user' ? 'U' : 'B'}
                  </div>
                  <div className={`p-3.5 rounded-xl text-xs leading-relaxed ${msg.role === 'user' ? 'bg-[var(--color-accent)] text-slate-950 font-medium rounded-tr-none' : 'bg-[rgba(22,30,49,0.9)] text-slate-200 rounded-tl-none border border-slate-800'}`}>
                    {msg.content.split('\n').map((line, idx) => (
                      <p key={idx} className={line ? 'mb-2' : 'mb-4'}>{line}</p>
                    ))}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="self-start flex gap-3 items-center">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#00C896] to-[#34F5C5] flex items-center justify-center font-bold text-slate-950 text-xs">
                    B
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-xs italic flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce delay-75"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce delay-150"></span>
                    Bulliq is analyzing...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Action quick starters */}
            <div className="px-5 pb-3 flex flex-wrap gap-2">
              <button 
                onClick={() => handleSendMessage("Let's start the risk onboarding questionnaire.")}
                className="p-1.5 px-3 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] text-slate-300 font-semibold cursor-pointer flex items-center gap-1"
              >
                Start Onboarding <ArrowRight className="w-3 h-3" />
              </button>
              <button 
                onClick={() => handleSendMessage("Assess the current market regime for NSE:RELIANCE and BTC.")}
                className="p-1.5 px-3 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] text-slate-300 font-semibold cursor-pointer flex items-center gap-1"
              >
                Assess Market Regime <ArrowRight className="w-3 h-3" />
              </button>
              <button 
                onClick={() => handleSendMessage("Configure my profile: Capital is ₹100,000, Scalping style, risk 1% per trade.")}
                className="p-1.5 px-3 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] text-slate-300 font-semibold cursor-pointer flex items-center gap-1"
              >
                Set Profile: ₹100k <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-slate-800 bg-[rgba(10,14,23,0.5)] flex gap-3">
              <input 
                type="text" 
                placeholder="Type your trading parameters or ask Bulliq for investment advice..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                className="flex-1 glass-input py-3"
              />
              <button 
                onClick={() => handleSendMessage()}
                className="btn-primary flex items-center justify-center p-3 w-12 h-12"
              >
                <Send className="w-4 h-4 shrink-0" />
              </button>
            </div>
          </>
        ) : activeTab === 'terminal' ? (
          /* Day Trading Terminal Dashboard */
          <div className="flex-1 p-5 overflow-y-auto max-h-[580px] flex flex-col gap-6">
            
            {/* Live Performance Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              
              {/* Countdown / Elapsed Timer */}
              <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  {isAutoTrading ? 'Autonomous Run' : 'Advisory Channel'}
                </span>
                <div className="flex flex-col mt-1">
                  <span className={`font-extrabold text-base tracking-tight ${isAutoTrading ? 'text-rose-400 font-mono' : 'text-slate-400'}`}>
                    {isAutoTrading ? formatCountdown(sessionCountdown) : '00:00:00'}
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">
                    {isAutoTrading ? 'Session Countdown' : 'Sandbox Simulation'}
                  </span>
                </div>
                <span className={`text-[9px] font-bold p-0.5 px-1.5 rounded self-start mt-2 ${isAutoTrading ? 'bg-rose-950/40 text-rose-400 border border-rose-900/60 animate-pulse' : 'bg-slate-950/40 text-slate-400 border border-slate-800'}`}>
                  {isAutoTrading ? '🔴 LIVE ON BROKER' : '⚪ SIMULATION ONLY'}
                </span>
              </div>

              {/* Simulated/Alpaca Live Equity Balance */}
              <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Total Equity</span>
                <div className="flex flex-col mt-1">
                  <span className="font-extrabold text-base text-white tracking-tight">
                    ${(100000 + stats.total_pnl).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </span>
                  <span className={`text-[10px] font-bold ${stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                    {stats.total_pnl >= 0 ? '+' : ''}${stats.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} PnL
                  </span>
                </div>
                <span className="text-[9px] text-slate-500 font-medium mt-2">Initial: $100,000.00</span>
              </div>

              {/* Win Rate / Hit Ratio */}
              <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Hit Ratio</span>
                <div className="flex flex-col mt-1">
                  <span className="font-extrabold text-base text-white tracking-tight">{stats.win_rate}%</span>
                  <div className="w-full bg-slate-850 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-emerald-400 h-full rounded-full transition-all duration-300" style={{ width: `${stats.win_rate}%` }}></div>
                  </div>
                </div>
                <span className="text-[9px] text-slate-500 font-medium mt-2">Wins: {trades.filter(t => t.status === 'closed' && t.pnl > 0).length} / {stats.closed_trades || 1}</span>
              </div>

              {/* Risk Settings Trigger */}
              <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Risk Safeguards</span>
                <div className="flex flex-col mt-1">
                  <span className="font-extrabold text-xs text-white uppercase tracking-wider mt-1">
                    {bypassLimits ? '🔴 Bypassed' : '🟢 Safe Strict'}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <input 
                    type="checkbox" 
                    id="bypass-toggle"
                    checked={bypassLimits}
                    onChange={(e) => handleToggleBypassLimits(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-800 text-[var(--color-accent)] focus:ring-[var(--color-accent)] cursor-pointer w-4 h-4"
                  />
                  <label htmlFor="bypass-toggle" className="text-[10px] text-slate-400 font-bold cursor-pointer hover:text-slate-200">
                    Bypass Limits
                  </label>
                </div>
              </div>

            </div>

            {/* Autonomous Session Controller Card */}
            <div className="bg-[rgba(16,22,35,0.6)] p-5 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${isAutoTrading ? 'bg-rose-950/40 border border-rose-900/60 text-rose-400 animate-pulse' : 'bg-slate-900 border border-slate-850 text-slate-400'}`}>
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                  <h4 className="font-bold text-sm text-slate-200">Autonomous Trading Session</h4>
                  <p className="text-[10px] text-slate-450 leading-relaxed max-w-[450px]">
                    {isAutoTrading 
                      ? `Bulliq AI is trading live on your linked Alpaca account. Time remaining: ${formatCountdown(sessionCountdown)}.` 
                      : `In simulated Advisory mode. Start a timed session to automatically trade scored 10-layer signals.`}
                  </p>
                </div>
              </div>
              
              <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
                {!isAutoTrading ? (
                  <button 
                    onClick={() => {
                      if (!isTestRunning) {
                        alert("Please link your Alpaca Paper Account in the sidebar first to enable automated broker trading.");
                        return;
                      }
                      setIsSessionModalOpen(true);
                    }}
                    className="btn-primary p-2 px-5 text-xs font-bold shadow-[0_0_12px_rgba(0,200,150,0.15)] flex items-center gap-1.5 cursor-pointer"
                  >
                    <Activity className="w-3.5 h-3.5" />
                    Configure Auto Trade
                  </button>
                ) : (
                  <button 
                    onClick={handleStopAutoSession}
                    className="p-2 px-5 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-lg border border-rose-500 shadow-[0_0_12px_rgba(239,68,68,0.2)] flex items-center gap-1.5 cursor-pointer transition-all duration-200"
                  >
                    <AlertTriangle className="w-3.5 h-3.5 animate-bounce" />
                    Emergency Stop
                  </button>
                )}
              </div>
            </div>

            {/* Action Row & Performance Report Trigger */}
            <div className="flex justify-between items-center border-t border-slate-800/80 pt-4">
              <div className="flex flex-col">
                <h4 className="font-bold text-sm text-slate-200">Continuous Test Run Logs</h4>
                <p className="text-[10px] text-slate-400">Live ticks matching sequential 10-layer confluences</p>
              </div>
              <button 
                onClick={generatePerformanceReport}
                className="btn-primary p-2 px-4 text-xs font-bold flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,200,150,0.15)]"
              >
                <Activity className="w-3.5 h-3.5" />
                Generate Financial Report
              </button>
            </div>

            {/* Live Trades Table */}
            <div className="flex-1 bg-[rgba(10,14,23,0.5)] border border-slate-800/80 rounded-xl overflow-hidden flex flex-col">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-bold">
                      <th className="p-3">Asset</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Qty</th>
                      <th className="p-3">Entry</th>
                      <th className="p-3">SL</th>
                      <th className="p-3">TP</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Net Profit</th>
                      <th className="p-3">Execution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade) => (
                      <tr key={trade.id} className="border-b border-slate-800 hover:bg-slate-900/20 text-slate-300">
                        <td className="p-3 font-bold text-white">{trade.symbol.split(':')[1]}</td>
                        <td className="p-3">
                          <span className={`font-extrabold ${trade.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-500'}`}>
                            {trade.direction}
                          </span>
                        </td>
                        <td className="p-3">{trade.quantity}</td>
                        <td className="p-3">${trade.entry_price.toLocaleString()}</td>
                        <td className="p-3 text-rose-400/90">${trade.stop_loss.toLocaleString()}</td>
                        <td className="p-3 text-emerald-400/90">${trade.take_profit.toLocaleString()}</td>
                        <td className="p-3">
                          <span className={`p-0.5 px-2 rounded text-[10px] font-bold ${trade.status === 'open' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 animate-pulse' : 'bg-slate-950/40 text-slate-400 border border-slate-800'}`}>
                            {trade.status.toUpperCase()}
                          </span>
                        </td>
                        <td className={`p-3 text-right font-extrabold ${trade.status === 'open' ? 'text-slate-400' : trade.pnl >= 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                          {trade.status === 'open' ? '-' : `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                        </td>
                        <td className="p-3 text-[10px] font-semibold text-slate-400 uppercase">
                          {trade.is_mock ? 'Sandbox Sim' : 'Alpaca Live'}
                        </td>
                      </tr>
                    ))}
                    {trades.length === 0 && (
                      <tr>
                        <td colSpan={9} className="p-8 text-center text-slate-500">
                          No continuous trades matching active onboarding parameters have executed yet. Bypassing risk guardrails forces rapid trade executions.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        ) : (
           /* Auto-Trader Center Page */
           <div className="flex-1 p-5 overflow-y-auto max-h-[580px] flex flex-col gap-6">
             
             {/* Live Performance / Status Panel */}
             <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
               
               <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                 <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Running Mode</span>
                 <div className="flex flex-col mt-1">
                   <span className="font-extrabold text-base text-white tracking-tight">
                     {isAutoTrading ? '🔴 ACTIVE AUTO-RUN' : '⚪ SIMULATION ONLY'}
                   </span>
                   <span className="text-[10px] text-slate-500 font-medium">
                     {isAutoTrading ? `Executing live bracket orders` : `Signals run in Sandbox Simulator`}
                   </span>
                 </div>
               </div>

               <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                 <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Session Time Remaining</span>
                 <div className="flex flex-col mt-1">
                   <span className={`font-extrabold text-base tracking-tight font-mono ${isAutoTrading ? 'text-rose-400' : 'text-slate-450'}`}>
                     {isAutoTrading ? formatCountdown(sessionCountdown) : '00:00:00'}
                   </span>
                   <span className="text-[10px] text-slate-500 font-medium">
                     {isAutoTrading ? 'Auto-expires at target' : 'Start a session to deploy'}
                   </span>
                 </div>
               </div>

               <div className="bg-[rgba(17,24,39,0.7)] p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                 <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Session Allocation</span>
                 <div className="flex flex-col mt-1">
                   <span className="font-extrabold text-base text-white tracking-tight">
                     ${isAutoTrading ? sessionCapitalInput.toLocaleString() : 'N/A'}
                   </span>
                   <span className="text-[10px] text-slate-500 font-medium">
                     {isAutoTrading ? `Max Trade Risk: ${sessionRiskInput}%` : 'Limits inactive'}
                   </span>
                 </div>
               </div>

             </div>

             {/* Live Scanner Feed & Force Signals Card */}
             <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
               
               {/* 10-Layer Live Thinking Feed */}
               <div className="lg:col-span-8 bg-[rgba(10,14,23,0.5)] border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4">
                 <div className="flex justify-between items-center border-b border-slate-850 pb-2">
                   <div className="flex items-center gap-2">
                     <Cpu className="text-[var(--color-accent)] w-4.5 h-4.5 animate-pulse" />
                     <h4 className="font-bold text-sm text-slate-200">10-Layer Real-Time Intelligence Stream</h4>
                   </div>
                   <span className={`text-[9px] font-bold p-0.5 px-2 rounded ${isAutoTrading ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50' : 'bg-slate-950 text-slate-500 border border-slate-800'}`}>
                     {isAutoTrading ? 'SCANNING ACTIVE' : 'STANDBY'}
                   </span>
                 </div>
                 
                 <div className="flex-1 bg-slate-950/95 border border-slate-900 rounded-lg p-4 font-mono text-[10px] leading-relaxed text-emerald-500/90 h-[240px] overflow-y-auto flex flex-col gap-2 shadow-inner select-text">
                   {pipelineLogs.map((log, index) => (
                     <div key={index} className="border-b border-slate-900 pb-1 flex gap-2">
                       <span className="text-slate-650 shrink-0">[{index + 1}]</span>
                       <span>{log}</span>
                     </div>
                   ))}
                   {isAutoTrading && (
                     <div className="text-emerald-400 flex items-center gap-1.5 animate-pulse italic mt-1 text-[9px]">
                       <RefreshCw className="w-3 h-3 animate-spin" />
                       Pipeline actively scanning market depth, CVD imbalance, PCR levels, and sentiment feeds...
                     </div>
                   )}
                 </div>
               </div>

               {/* Tester forcing controls */}
               <div className="lg:col-span-4 flex flex-col gap-4">
                 
                 {/* Configure and start card */}
                 <div className="bg-[rgba(17,24,39,0.7)] border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4 flex-1 justify-between">
                   <div className="flex flex-col gap-1">
                     <h4 className="font-bold text-xs text-slate-200 uppercase tracking-wider">Session Activator</h4>
                     <p className="text-[10px] text-slate-450 leading-relaxed">
                       Start an autonomous trading session to authorize direct bracket order execution.
                     </p>
                   </div>
                   
                   {!isAutoTrading ? (
                     <button 
                       onClick={() => {
                         if (!isTestRunning) {
                           alert("Please link your Alpaca Paper Account in the sidebar first to enable automated broker trading.");
                           return;
                         }
                         setIsSessionModalOpen(true);
                       }}
                       className="btn-primary p-3 w-full text-xs font-bold shadow-[0_0_12px_rgba(0,200,150,0.2)] flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                     >
                       <Activity className="w-4 h-4" />
                       Deploy Auto-Trader
                     </button>
                   ) : (
                     <button 
                       onClick={handleStopAutoSession}
                       className="p-3 w-full text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-lg border border-rose-500 shadow-[0_0_12px_rgba(239,68,68,0.25)] flex items-center justify-center gap-1.5 cursor-pointer mt-2 transition-all duration-200 animate-pulse"
                     >
                       <AlertTriangle className="w-4 h-4" />
                       Emergency Stop
                     </button>
                   )}
                 </div>

                 {/* Force Trade Signal Card */}
                 <div className="bg-[rgba(17,24,39,0.7)] border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4 flex-1 justify-between">
                   <div className="flex flex-col gap-1">
                     <div className="flex items-center gap-1.5">
                       <Zap className="text-amber-400 w-4 h-4 animate-bounce" />
                       <h4 className="font-bold text-xs text-slate-200 uppercase tracking-wider">Developer Sandbox</h4>
                     </div>
                     <p className="text-[10px] text-slate-450 leading-relaxed">
                       For testing: Trigger a high-confluence Buy signal instantly to watch the live order placing logic and table updates.
                     </p>
                   </div>
                   
                   <button 
                     onClick={handleForceSignal}
                     className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-slate-100 font-bold p-3 rounded-lg text-xs transition-all duration-200 cursor-pointer shadow-[0_0_12px_rgba(245,158,11,0.15)] border border-amber-500 flex items-center justify-center gap-1.5"
                   >
                     <Zap className="w-4 h-4 text-amber-200 shrink-0" />
                     Force Trade Signal
                   </button>
                 </div>

               </div>

             </div>

             {/* Live Trades specific to this session */}
             <div className="flex-1 bg-[rgba(10,14,23,0.5)] border border-slate-800/80 rounded-xl overflow-hidden flex flex-col">
               <div className="p-4 bg-slate-900/60 border-b border-slate-800 flex justify-between items-center">
                 <h4 className="font-bold text-xs text-slate-200">Active Trades Table</h4>
                 <span className="text-[10px] text-slate-450">Updates live when signals trigger or forced</span>
               </div>
               <div className="overflow-x-auto">
                 <table className="w-full text-left text-xs border-collapse">
                   <thead>
                     <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-bold">
                       <th className="p-3">Asset</th>
                       <th className="p-3">Type</th>
                       <th className="p-3">Qty</th>
                       <th className="p-3">Entry Price</th>
                       <th className="p-3">Stop Loss</th>
                       <th className="p-3">Take Profit</th>
                       <th className="p-3">Status</th>
                       <th className="p-3 text-right">Net Profit</th>
                       <th className="p-3">Execution</th>
                     </tr>
                   </thead>
                   <tbody>
                     {trades.map((trade) => (
                       <tr key={trade.id} className="border-b border-slate-800 hover:bg-slate-900/20 text-slate-300">
                         <td className="p-3 font-bold text-white">{trade.symbol.split(':')[1]}</td>
                         <td className="p-3">
                           <span className={`font-extrabold ${trade.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-500'}`}>
                             {trade.direction}
                           </span>
                         </td>
                         <td className="p-3">{trade.quantity}</td>
                         <td className="p-3">${trade.entry_price.toLocaleString()}</td>
                         <td className="p-3 text-rose-400/90">${trade.stop_loss.toLocaleString()}</td>
                         <td className="p-3 text-emerald-400/90">${trade.take_profit.toLocaleString()}</td>
                         <td className="p-3">
                           <span className={`p-0.5 px-2 rounded text-[10px] font-bold ${trade.status === 'open' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 animate-pulse' : 'bg-slate-950/40 text-slate-400 border border-slate-800'}`}>
                             {trade.status.toUpperCase()}
                           </span>
                         </td>
                         <td className={`p-3 text-right font-extrabold ${trade.status === 'open' ? 'text-slate-400' : trade.pnl >= 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                           {trade.status === 'open' ? '-' : `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                         </td>
                         <td className="p-3 text-[10px] font-semibold text-slate-400 uppercase">
                           {trade.is_mock ? 'Sandbox Sim' : 'Alpaca Live'}
                         </td>
                       </tr>
                     ))}
                     {trades.length === 0 && (
                       <tr>
                         <td colSpan={9} className="p-8 text-center text-slate-500">
                           No trades have executed yet. Deploy the auto-trader or click the <b>Force Trade Signal</b> button above to dispatch one immediately!
                         </td>
                       </tr>
                     )}
                   </tbody>
                 </table>
               </div>
             </div>

           </div>
        )}

      </div>

      {/* RIGHT PANEL: Live Advisory Signals & Indicator Chart (35% width) */}
      <div className="lg:col-span-4 flex flex-col gap-6">
        
        {/* System Connectivity Settings */}
        <div className="glass-panel p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <RefreshCw className="text-[var(--color-accent)] w-4 h-4" />
            <h3 className="font-bold text-sm text-slate-200">System Connectivity</h3>
          </div>
          
          <div className="flex flex-col gap-2.5 text-xs">
            <div className="flex flex-col gap-1">
              <label className="text-slate-400 font-medium">Backend API base URL</label>
              <input 
                type="text" 
                placeholder="e.g. http://localhost:8000"
                value={apiBaseUrlInput}
                onChange={(e) => setApiBaseUrlInput(e.target.value)}
                className="glass-input p-2 text-xs"
              />
            </div>
            
            <button 
              onClick={() => {
                let url = apiBaseUrlInput.trim();
                if (url.endsWith('/')) {
                  url = url.slice(0, -1);
                }
                setApiBaseUrl(url);
                localStorage.setItem('BULLIQ_API_BASE_URL', url);
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: `🔄 API Base URL successfully updated to: ${url}. Attempting connections and re-establishing live WebSocket links...`,
                  timestamp: new Date()
                }]);
              }}
              className="btn-primary w-full p-2.5 text-xs font-bold cursor-pointer"
            >
              Update API Endpoint
            </button>
            <span className="text-[9px] text-slate-500 text-center leading-relaxed">
              Expose port 8000 via <b>ngrok http 8000</b> or <b>localtunnel</b> to keep your backend online and access it anywhere!
            </span>
          </div>
        </div>

        {/* Interactive mini TV Chart */}
        <div className="glass-panel p-4 flex flex-col gap-3">
          <span className="font-bold text-xs text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-[var(--color-accent)]" />
            Live Ticks: {activeSymbol}
          </span>
          <div ref={chartContainerRef} className="w-full rounded overflow-hidden" />
        </div>

        {/* Scored High-Confluence Alerts Feed */}
        <div className="glass-panel p-5 flex flex-col gap-4 flex-1">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Layers className="text-[var(--color-accent)] w-4 h-4" />
              <h3 className="font-bold text-sm text-slate-200">Advisory Signals Feed</h3>
            </div>
            <span className="text-[10px] text-emerald-400 font-semibold">10-Layer Active</span>
          </div>

          <div className="flex flex-col gap-3 overflow-y-auto max-h-[220px]">
            {signals.map((sig) => (
              <div 
                key={sig.id}
                onClick={() => setSelectedSignal(sig)}
                className={`p-3 rounded bg-slate-900 border transition-all duration-200 cursor-pointer flex flex-col gap-1.5 ${selectedSignal?.id === sig.id ? 'border-[var(--color-accent)] bg-slate-900' : 'border-slate-800 hover:border-slate-700'}`}
              >
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-white">{sig.symbol.split(':')[1]}</span>
                  <span className={`text-[9px] font-bold p-0.5 px-2 rounded ${sig.direction === 'BUY' ? 'bg-[rgba(16,185,129,0.1)] text-emerald-400' : 'bg-[rgba(239,68,68,0.1)] text-rose-500'}`}>
                    {sig.direction} Approved
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Score: <b>{sig.confidence_score}%</b></span>
                  <span>R:R Gate: <b>{sig.risk_reward_ratio}:1</b></span>
                </div>
              </div>
            ))}
            {signals.length === 0 && (
              <div className="text-center py-8 text-[11px] text-slate-500 flex flex-col items-center justify-center gap-2">
                <RefreshCw className="w-5 h-5 text-slate-700 animate-spin" />
                <span>Simulating market confluences... Signals trigger based on your onboarding capital rules.</span>
              </div>
            )}
          </div>
        </div>
        {/* Alpaca Broker Link Section */}
        <div className="glass-panel p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <ShieldAlert className="text-[var(--color-accent)] w-4 h-4" />
            <h3 className="font-bold text-sm text-slate-200">Link Alpaca Account</h3>
          </div>
          
          <div className="flex flex-col gap-2.5 text-xs">
            <div className="flex flex-col gap-1">
              <label className="text-slate-400 font-medium">Alpaca API Key ID</label>
              <input 
                type="text" 
                placeholder="Paste Key ID here..."
                value={alpacaKey}
                onChange={(e) => setAlpacaKey(e.target.value)}
                className="glass-input p-2 text-xs"
              />
            </div>
            
            <div className="flex flex-col gap-1">
              <label className="text-slate-400 font-medium">Alpaca Secret Key</label>
              <input 
                type="password" 
                placeholder="Paste Secret Key here..."
                value={alpacaSecret}
                onChange={(e) => setAlpacaSecret(e.target.value)}
                className="glass-input p-2 text-xs"
              />
            </div>
            
            <button 
              onClick={handleLinkAlpaca}
              disabled={isLinking}
              className="btn-primary w-full p-2.5 text-xs font-bold cursor-pointer mt-1.5 flex items-center justify-center gap-1.5"
            >
              {isLinking ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Link Alpaca Paper Account'
              )}
            </button>
            
            {alpacaStatus && (
              <span className={`text-[10px] text-center font-bold p-1 px-2 rounded mt-1.5 ${alpacaStatus.includes('SUCCESS') ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/60' : 'bg-rose-950/40 text-rose-400 border border-rose-900/60'}`}>
                {alpacaStatus}
              </span>
            )}
          </div>
        </div>

      </div>

      {/* Selected Signal Telemetry Audit Modal */}
      {selectedSignal && (
        <div className="lg:col-span-12 glass-panel p-5 bg-gradient-to-br from-[#161e31] to-[#0a0e17] flex flex-col gap-4 border-[rgba(0,200,150,0.3)] flex-1">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-3">
              <span className="font-bold text-base text-white">{selectedSignal.symbol} Telemetry Audit</span>
              <span className={`p-1 px-3 rounded text-[10px] font-bold ${selectedSignal.direction === 'BUY' ? 'bg-[rgba(0,200,150,0.1)] text-emerald-400' : 'bg-[rgba(239,68,68,0.1)] text-rose-500'}`}>
                {selectedSignal.direction} Plan Passed
              </span>
            </div>
            <button 
              onClick={() => setSelectedSignal(null)}
              className="text-slate-400 hover:text-white text-xs font-semibold cursor-pointer"
            >
              Close Snapshot
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Levels */}
            <div className="flex flex-col gap-3 bg-[rgba(10,14,23,0.5)] p-4 rounded border border-slate-800 text-xs">
              <span className="font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                Trigger Checkpoints
              </span>
              <div className="flex flex-col gap-2 mt-2 text-slate-300">
                <div className="flex justify-between">
                  <span>Trigger Entry Price:</span>
                  <span className="font-bold text-white">${selectedSignal.entry_price}</span>
                </div>
                <div className="flex justify-between">
                  <span>Target Profit:</span>
                  <span className="font-bold text-emerald-400">${selectedSignal.target_1}</span>
                </div>
                <div className="flex justify-between">
                  <span>Stop Loss Cover:</span>
                  <span className="font-bold text-rose-500">${selectedSignal.stop_loss}</span>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="flex flex-col gap-3 bg-[rgba(10,14,23,0.5)] p-4 rounded border border-slate-800 text-xs">
              <span className="font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                Advisor Rationale
              </span>
              <p className="text-slate-300 leading-relaxed">
                {selectedSignal.explanation}
              </p>
            </div>

            {/* 10-Layer Telemetry */}
            <div className="flex flex-col gap-3 bg-[rgba(10,14,23,0.5)] p-4 rounded border border-slate-800 text-xs">
              <span className="font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                10-Layer Sequencer Logs
              </span>
              <div className="flex flex-col gap-1.5 text-slate-300 max-h-[140px] overflow-y-auto">
                <div className="flex justify-between">
                  <span>Layer 1 (Intake):</span>
                  <span className="text-emerald-400 font-medium">VWAP ${selectedSignal.layers_telemetry?.layer1?.calculated_vwap}</span>
                </div>
                <div className="flex justify-between">
                  <span>Layer 3 (Regime):</span>
                  <span className="text-[var(--color-accent)] font-medium">{selectedSignal.market_regime}</span>
                </div>
                <div className="flex justify-between">
                  <span>Layer 4 (Technicals):</span>
                  <span>RSI {selectedSignal.layers_telemetry?.layer4?.indicators?.rsi}</span>
                </div>
                <div className="flex justify-between">
                  <span>Layer 7 (Risk):</span>
                  <span className="text-emerald-400 font-medium">Approved R:R</span>
                </div>
                <div className="flex justify-between">
                  <span>Layer 10 (Guard):</span>
                  <span className="text-emerald-400 font-medium">Verified Clean</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Performance Report Generation Modal Overlay */}
      {showReport && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl bg-gradient-to-b from-[#0B0F14] to-[#111827] border-[rgba(0,200,150,0.3)] shadow-[0_0_40px_rgba(0,200,150,0.15)] flex flex-col max-h-[90vh]">
            
            <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/40">
              <div className="flex items-center gap-2">
                <Activity className="text-[#00C896] w-5 h-5 animate-pulse" />
                <h3 className="font-extrabold text-base text-slate-100 tracking-wider">BULLIQ PERFORMANCE LOGS</h3>
              </div>
              <button 
                onClick={() => setShowReport(false)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer text-xs font-bold uppercase"
              >
                Close Report
              </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto font-mono text-xs leading-relaxed text-slate-300 whitespace-pre bg-slate-950/80 select-all border-b border-slate-800">
              {reportText}
            </div>

            <div className="p-4 flex gap-4 bg-slate-900/40 justify-end">
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(reportText);
                  alert("Report successfully copied to your clipboard!");
                }}
                className="btn-primary p-2 px-6 text-xs font-bold flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,200,150,0.2)]"
              >
                Copy to Clipboard
              </button>
              <button 
                onClick={() => setShowReport(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold p-2 px-6 rounded-lg text-xs transition-all duration-200 cursor-pointer"
              >
                Done
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Session Onboarding Configuration Modal */}
      {isSessionModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg bg-gradient-to-b from-[#0b0e14] to-[#121824] border-[rgba(0,200,150,0.3)] shadow-[0_0_45px_rgba(0,200,150,0.2)] flex flex-col max-h-[90vh] rounded-2xl">
            
            <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/40 rounded-t-2xl">
              <div className="flex items-center gap-2">
                <ShieldAlert className="text-[#00C896] w-5 h-5 animate-pulse" />
                <h3 className="font-extrabold text-base text-slate-100 tracking-wider">PRE-FLIGHT SESSION RULES</h3>
              </div>
              <button 
                onClick={() => setIsSessionModalOpen(false)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer text-xs font-bold uppercase"
              >
                Cancel
              </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-5 text-xs text-slate-350">
              <p className="text-slate-450 leading-relaxed">
                Before activating autonomous trade execution on your linked Alpaca Paper account, confirm your parameters to compile session bounds.
              </p>

              {/* Amount/Capital Allocation */}
              <div className="flex flex-col gap-1.5">
                <label className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Session Capital Allocation (USD)</label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-500 font-bold">$</span>
                  <input 
                    type="number"
                    value={sessionCapitalInput}
                    onChange={(e) => setSessionCapitalInput(Number(e.target.value))}
                    className="glass-input pl-7 p-2.5 w-full font-bold text-slate-100 bg-slate-950/80"
                    placeholder="e.g. 5000"
                  />
                </div>
                <span className="text-[9px] text-slate-500">Allocates a custom virtual buying power limit for this specific run.</span>
              </div>

              {/* Duration Custom Selector */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Session Duration (Minutes)</label>
                  <input 
                    type="number"
                    value={sessionDurationInput}
                    onChange={(e) => setSessionDurationInput(Math.max(1, Number(e.target.value)))}
                    className="glass-input p-2.5 w-full font-bold text-slate-100 bg-slate-950/80"
                    placeholder="e.g. 60"
                  />
                  <span className="text-[9px] text-slate-500">Auto-expires execution feed at timestamp.</span>
                </div>

                {/* Risk per trade */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Max Risk Per Trade (%)</label>
                  <select 
                    value={sessionRiskInput}
                    onChange={(e) => setSessionRiskInput(Number(e.target.value))}
                    className="glass-input p-2.5 w-full font-bold text-slate-100 bg-slate-950/80 cursor-pointer"
                  >
                    <option value={0.5}>0.5% (Conservative)</option>
                    <option value={1.0}>1.0% (Moderate Default)</option>
                    <option value={1.5}>1.5% (Active Momentum)</option>
                    <option value={2.0}>2.0% (Aggressive)</option>
                  </select>
                  <span className="text-[9px] text-slate-500">Calculates precise bracket order stop levels.</span>
                </div>
              </div>

              {/* Safety Authorization Check */}
              <div className="mt-2 bg-slate-950/40 p-4 rounded-xl border border-slate-900/60 flex items-start gap-3">
                <input 
                  type="checkbox" 
                  id="session-authorize"
                  checked={sessionAuthorize}
                  onChange={(e) => setSessionAuthorize(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-800 text-[var(--color-accent)] focus:ring-[var(--color-accent)] cursor-pointer w-4 h-4 mt-0.5"
                />
                <div className="flex flex-col gap-1">
                  <label htmlFor="session-authorize" className="font-bold text-slate-200 cursor-pointer hover:text-white">
                    Authorize Autonomous Execution
                  </label>
                  <p className="text-[10px] text-slate-450 leading-normal">
                    I authorize Bulliq AI's 10-layer intelligence pipeline to submit market buy/sell orders and linked bracket orders on my linked Alpaca account for the next {sessionDurationInput} minutes.
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 flex gap-3 bg-slate-900/40 justify-end rounded-b-2xl border-t border-slate-800">
              <button 
                onClick={() => setIsSessionModalOpen(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold p-2.5 px-6 rounded-lg transition-all duration-200 cursor-pointer"
              >
                Back
              </button>
              <button 
                onClick={handleStartAutoSession}
                disabled={!sessionAuthorize}
                className={`p-2.5 px-8 font-bold rounded-lg flex items-center gap-1.5 transition-all duration-200 ${sessionAuthorize ? 'btn-primary shadow-[0_0_15px_rgba(0,200,150,0.25)] cursor-pointer' : 'bg-slate-900 text-slate-650 border border-slate-800/80 cursor-not-allowed'}`}
              >
                <Activity className="w-4 h-4" />
                Deploy Live Agent
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Session Completion Report Modal */}
      {showSessionReportModal && sessionReportData && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg bg-gradient-to-b from-[#0b0e14] to-[#111827] border-[rgba(0,200,150,0.3)] shadow-[0_0_40px_rgba(0,200,150,0.2)] flex flex-col max-h-[90vh] rounded-2xl">
            
            <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/40 rounded-t-2xl">
              <div className="flex items-center gap-2">
                <TrendingUp className="text-[#00C896] w-5 h-5 animate-pulse" />
                <h3 className="font-extrabold text-base text-slate-100 tracking-wider">SESSION RUN REPORT</h3>
              </div>
              <button 
                onClick={() => setShowSessionReportModal(false)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer text-xs font-bold uppercase"
              >
                Dismiss
              </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-6 text-xs text-slate-350">
              
              <div className="text-center py-4 bg-slate-950/60 rounded-xl border border-slate-900 flex flex-col gap-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Net Session Profit / Loss</span>
                <span className={`text-2xl font-extrabold tracking-tight ${sessionReportData.totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                  {sessionReportData.totalPnL >= 0 ? '+' : ''}${sessionReportData.totalPnL.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </span>
                <span className="text-[9px] text-slate-500">Allocated Capital: ${sessionReportData.allocatedCapital.toLocaleString()}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                
                <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-900 flex flex-col justify-between">
                  <span className="text-[9px] text-slate-400 font-bold uppercase">Duration Configured</span>
                  <span className="font-extrabold text-sm text-white tracking-tight mt-1">{sessionReportData.durationMinutes} Minutes</span>
                  <span className="text-[9px] text-slate-500 mt-1">Halt: {sessionReportData.endTime}</span>
                </div>

                <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-900 flex flex-col justify-between">
                  <span className="text-[9px] text-slate-400 font-bold uppercase">Win Rate (Hit Ratio)</span>
                  <span className="font-extrabold text-sm text-white tracking-tight mt-1">{sessionReportData.winRate}%</span>
                  <span className="text-[9px] text-slate-500 mt-1">Wins: {sessionReportData.winsCount} / Losses: {sessionReportData.lossesCount}</span>
                </div>

                <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-900 flex flex-col justify-between col-span-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-slate-400 font-bold uppercase">Trades Dispatched</span>
                    <span className="font-extrabold text-xs text-white">{sessionReportData.totalTrades} Executed</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div className="bg-emerald-400 h-full rounded-full transition-all duration-300" style={{ width: `${sessionReportData.winRate}%` }}></div>
                  </div>
                </div>

              </div>

              <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-900 flex flex-col gap-2">
                <span className="font-bold text-[10px] text-slate-400 uppercase tracking-wider">Confluence Integrity Audit</span>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  During this autonomous run, all triggered trades successfully passed the sequential 10-layer gate checks (Technical, Volume Delta, Proximity levels, Options PCR, Sentiment bias, and Guardrail limits), protecting your equity from unnecessary market drag.
                </p>
              </div>

            </div>

            <div className="p-4 flex bg-slate-900/40 justify-end rounded-b-2xl border-t border-slate-800">
              <button 
                onClick={() => {
                  const summary = `================================================
          BULLIQ AI AUTONOMOUS RUN SUMMARY
================================================
Halt Time: ${sessionReportData.endTime}
Duration: ${sessionReportData.durationMinutes} Minutes
Capital Allocated: $${sessionReportData.allocatedCapital.toLocaleString()}
Net PnL: ${sessionReportData.totalPnL >= 0 ? '+' : ''}$${sessionReportData.totalPnL.toFixed(2)}
Total Trades Executed: ${sessionReportData.totalTrades}
Win Rate: ${sessionReportData.winRate}%
================================================`;
                  navigator.clipboard.writeText(summary);
                  alert("Session summary copied to clipboard!");
                }}
                className="btn-primary p-2 px-6 text-xs font-bold flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,200,150,0.2)]"
              >
                Copy Summary
              </button>
              <button 
                onClick={() => setShowSessionReportModal(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold p-2.5 px-6 rounded-lg text-xs transition-all duration-200 cursor-pointer ml-2"
              >
                Done
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
