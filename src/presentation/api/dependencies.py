from typing import Annotated

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.ports.usecases import CreateOrderPort, GetOrderPort
from src.application.usecases.create_order import CreateOrder
from src.application.usecases.get_order import GetOrder
from src.infrastructure.http.catalog import HttpCatalogClient
from src.infrastructure.http.payments import HttpPaymentsClient
from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.settings import Settings


class Container(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    engine = providers.Singleton(
        create_async_engine,
        settings.provided.async_database_url,
    )
    session_factory = providers.Singleton(async_sessionmaker, engine)

    uow = providers.Factory(SQLAlchemyUnitOfWork, session_factory=session_factory)

    catalog = providers.Singleton(
        HttpCatalogClient,
        base_url=settings.provided.CAPASHINO_URL,
        api_token=settings.provided.CAPASHINO_API_TOKEN,
    )

    payments = providers.Singleton(
        HttpPaymentsClient,
        base_url=settings.provided.CAPASHINO_URL,
        api_token=settings.provided.CAPASHINO_API_TOKEN,
        callback_url=settings.provided.PAYMENTS_CALLBACK_URL,
    )

    create_order = providers.Factory(
        CreateOrder, uow=uow, catalog=catalog, payments=payments
    )
    get_order = providers.Factory(GetOrder, uow=uow)


CreateOrderDep = Annotated[CreateOrderPort, Depends(Provide[Container.create_order])]
GetOrderDep = Annotated[GetOrderPort, Depends(Provide[Container.get_order])]
