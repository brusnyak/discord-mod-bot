from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "modbot.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def init_db():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        with open(SCHEMA_PATH) as f:
            await db.executescript(f.read())
        await db.commit()


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
