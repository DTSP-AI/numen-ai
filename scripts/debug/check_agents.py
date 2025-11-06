import asyncio
from database import init_db, get_pg_pool

async def check_agents():
    await init_db()
    pool = get_pg_pool()

    async with pool.acquire() as conn:
        agents = await conn.fetch('SELECT id, name, type, status FROM agents LIMIT 10')
        print(f'\nFound {len(agents)} agents in database:')
        for agent in agents:
            print(f'  - {agent["id"]}: {agent["name"]} ({agent["type"]}, {agent["status"]})')

        # Check for the specific agent from the error
        specific_agent = await conn.fetchrow(
            'SELECT id, name, status FROM agents WHERE id = $1',
            '07410aaa-34c4-405c-8766-5c3e8bdafca0'
        )

        if specific_agent:
            print(f'\n✅ Agent from error exists: {specific_agent["name"]} ({specific_agent["status"]})')
        else:
            print(f'\n❌ Agent 07410aaa-34c4-405c-8766-5c3e8bdafca0 NOT FOUND in database')

if __name__ == '__main__':
    asyncio.run(check_agents())
