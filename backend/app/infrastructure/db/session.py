from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.db.repository import PostgresRepository


def create_database(url: str):
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=5,
        connect_args={"timeout": 5, "command_timeout": 15},
    )
    return engine, async_sessionmaker(engine, expire_on_commit=False)


class PostgresUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        self.repo = PostgresRepository(self.session)
        return self

    async def __aexit__(self, *args):
        # Roll back uncommitted reads/writes even if no exception was raised.
        try:
            await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self):
        await self.session.commit()
