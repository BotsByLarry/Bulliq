import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.trade import Trade
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        # Load trades
        res = await db.execute(select(Trade).order_by(Trade.created_at.desc()))
        trades = res.scalars().all()
        
        # Load user settings
        user_res = await db.execute(select(User).where(User.email == "test@example.com"))
        user = user_res.scalar_one_or_none()
        
        capital = user.total_capital if user else 100000.0
        
        total = len(trades)
        closed = [t for t in trades if t.status == "closed"]
        open_trades = [t for t in trades if t.status == "open"]
        wins = [t for t in closed if t.pnl > 0]
        losses = [t for t in closed if t.pnl <= 0]
        
        win_rate = (len(wins) / len(closed) * 100) if closed else 0.0
        total_pnl = sum(t.pnl for t in closed)
        avg_profit = (total_pnl / len(closed)) if closed else 0.0
        
        print("==================================================================")
        print("           BULLIQ AI DAY TRADING OVERNIGHT REPORT")
        print("==================================================================")
        print(f"Test Duration: 12 Hours (Overnight Continuous Session)")
        print(f"Initial Capital: ${capital:,.2f}")
        print(f"Net Trading Profit/Loss: ${total_pnl:+,.2f}")
        print(f"Estimated Session ROI: {(total_pnl / capital * 100):.4f}%")
        print(f"Total Executed Positions: {total}")
        print(f"Closed Positions: {len(closed)}")
        print(f"Active Floating Positions: {len(open_trades)}")
        print("------------------------------------------------------------------")
        print(f"Win Rate / Hit Ratio: {win_rate:.2f}%")
        print(f"Winning Trades: {len(wins)}")
        print(f"Losing Trades: {len(losses)}")
        print(f"Average Profit per Trade: ${avg_profit:,.2f}")
        print("==================================================================")
        
        if total > 0:
            print("\nDETAILED TRANSACTION LOG (Last 15 Trades):")
            print(f"{'SYMBOL':<15} | {'SIDE':<6} | {'QTY':<8} | {'ENTRY':<10} | {'EXIT':<10} | {'PNL':<10} | {'STATUS':<8}")
            print("-" * 75)
            for t in trades[:15]:
                entry = f"${t.entry_price:,.2f}"
                exit_pr = f"${t.exit_price:,.2f}" if t.exit_price else "-"
                pnl = f"${t.pnl:+,.2f}" if t.pnl is not None else "-"
                print(f"{t.symbol:<15} | {t.direction:<6} | {t.quantity:<8.2f} | {entry:<10} | {exit_pr:<10} | {pnl:<10} | {t.status.upper():<8}")
        else:
            print("No trades recorded in the session.")
            
if __name__ == "__main__":
    asyncio.run(main())
