import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    
    # Activate the job named 'Human_Restricted'
    res = await conn.execute("UPDATE alert_jobs SET is_active = True WHERE name = 'Human_Restricted'")
    print(f"Updated alert_jobs: {res}")
    
    # Check the updated jobs
    jobs = await conn.fetch("SELECT id, name, event_type, is_active FROM alert_jobs WHERE name = 'Human_Restricted'")
    for j in jobs:
        print(f"- ID: {j['id']}, Name: {j['name']}, Type: {j['event_type']}, Active: {j['is_active']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
