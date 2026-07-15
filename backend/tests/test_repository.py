import asyncio

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import MockSession, get_db, session_scope
from app.models.base import Base
from app.repositories.base import BaseRepository


class ExampleModel(Base):
    __tablename__ = "test_examples"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class ExampleRepository(BaseRepository[ExampleModel]):
    model = ExampleModel


def test_mock_session_supports_repository_contract() -> None:
    async def exercise() -> None:
        session = MockSession()
        repository = ExampleRepository(session)
        model = ExampleModel(id="example-1", name="before")

        assert await repository.add(model) is model
        assert await repository.get("missing") is None
        assert await repository.get_by(name="missing") is None
        assert await repository.list() == []
        assert await repository.count() == 0
        assert (await repository.update(model, name="after")).name == "after"
        await repository.delete(model)

    asyncio.run(exercise())


def test_session_dependencies_yield_compatible_mock_sessions() -> None:
    async def exercise() -> None:
        dependency = get_db()
        session = await anext(dependency)
        assert isinstance(session, MockSession)
        await dependency.aclose()

        async with session_scope() as scoped_session:
            assert isinstance(scoped_session, MockSession)

    asyncio.run(exercise())
