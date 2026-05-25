import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == "test@example.com"))
        user = res.scalar_one_or_none()
        if user:
            print("Updating user profile settings...")
            user.emotional_flags = {
                "fomo": False,
                "panic": False,
                "revenge": False,
                "bypass_limits": True
            }
            user.consecutive_losses = 0
            db.add(user)
            await db.commit()
            print("Successfully updated default profile with bypass_limits = True!")
        else:
            print("Test user not found.")

if __name__ == "__main__":
    asyncio.run(main())
