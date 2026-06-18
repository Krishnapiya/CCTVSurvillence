import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.user import UserRepository

async def show_users():
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        users = await repo.list()
        print("=" * 60)
        print(f"DATABASE USER LIST (Total: {len(users)})")
        print("=" * 60)
        for idx, u in enumerate(users):
            print(f"{idx+1}. Email: {u.email}, Role: {u.role}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(show_users())
