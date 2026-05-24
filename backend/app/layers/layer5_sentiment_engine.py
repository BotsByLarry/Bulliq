import random
from typing import List, Dict
from app.layers.pipeline_context import PipelineContext

class Layer5SentimentEngine:
    """
    Layer 5: News & Sentiment Engine
    Parses live feeds and extracts public sentiment scores (-1.0 to +1.0) and classifications.
    Provides synthetic news when running in Mock Sandbox mode.
    """
    
    def process(self, context: PipelineContext, mock_mode: bool = True) -> PipelineContext:
        news_items = []
        sentiment_score = 0.0
        
        if mock_mode:
            # Generate highly realistic day trading related news items for simulation
            news_database = {
                "NSE:RELIANCE": [
                    {"headline": "Reliance Industries announces expansion of green energy gigafactories.", "sentiment": 0.8},
                    {"headline": "Brokerages maintain bullish outlook on Reliance ahead of quarterly results.", "sentiment": 0.6},
                    {"headline": "Crude oil fluctuations put short-term pressure on Reliance refining margins.", "sentiment": -0.4}
                ],
                "NSE:TCS": [
                    {"headline": "TCS bags mega multi-million dollar cloud migration deal in Europe.", "sentiment": 0.9},
                    {"headline": "IT spending slowdown might check profit growth for TCS this quarter.", "sentiment": -0.3},
                    {"headline": "TCS expands partnership with AWS for advanced generative AI offerings.", "sentiment": 0.75}
                ],
                "NSE:NIFTY50": [
                    {"headline": "Foreign institutional investors (FIIs) inject massive capital into Indian index heavyweights.", "sentiment": 0.7},
                    {"headline": "Global markets slip as US Fed hints at holding interest rates higher for longer.", "sentiment": -0.5},
                    {"headline": "Inflation numbers in India show positive moderation, index gains.", "sentiment": 0.65}
                ],
                "CRYPTO:BTCUSDT": [
                    {"headline": "Institutional inflows into Bitcoin spot ETFs reach new all-time high.", "sentiment": 0.85},
                    {"headline": "Crypto regulatory scrutiny rises as SEC investigates secondary DeFi platforms.", "sentiment": -0.6},
                    {"headline": "Bitcoin mining hash rate surges to record heights, demonstrating extreme security.", "sentiment": 0.5}
                ]
            }
            
            # Select random item from synthetic bank
            defaults = [
                {"headline": "Market consolidates in tight intraday ranges with low volume.", "sentiment": 0.0},
                {"headline": "Momentum traders witness spikes across small-cap indices.", "sentiment": 0.3}
            ]
            
            symbol_news = news_database.get(context.symbol, defaults)
            chosen_news = random.choice(symbol_news)
            
            news_items.append({
                "headline": chosen_news["headline"],
                "source": "Mock Financial Feed",
                "timestamp": context.timestamp,
                "classification": "Corporate/Macro",
                "sentiment": chosen_news["sentiment"]
            })
            
            sentiment_score = chosen_news["sentiment"]
            
        else:
            # Actual live news RSS/API logic will hook in here when user provides API keys
            # Fallback to neutral if no real keys or empty responses
            sentiment_score = 0.0
            
        context.sentiment_score = sentiment_score
        context.news_events = news_items
        
        context.telemetry["layer5"] = {
            "sentiment_score": sentiment_score,
            "news_count": len(news_items),
            "news_details": news_items
        }
        
        return context
