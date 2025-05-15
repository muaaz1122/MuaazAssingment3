import asyncio
from app.database import get_db, engine
from app.models import User
from sqlalchemy.future import select

async def delete_user(email_to_delete):
    async with engine.begin() as conn:
        result = await conn.execute(select(User).where(User.email == email_to_delete))
        user = result.scalars().first()
        if user:
            await conn.execute(User.__table__.delete().where(User.email == email_to_delete))
            print(f"Deleted user: {email_to_delete}")
        else:
            print(f"User with email {email_to_delete} not found")

if __name__ == "__main__":
    email = input("Enter email to delete: ")
    asyncio.run(delete_user(email))
