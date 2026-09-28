from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine

from src.settings import Settings


class Container(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    engine = providers.Singleton(
        create_async_engine,
        settings.provided.async_database_url,
    )
