from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends

from src.application.ports.usecases import (
    CreateOrderPort,
    GetOrderPort,
    HandlePaymentCallbackPort,
)
from src.container import Container

CreateOrderDep = Annotated[CreateOrderPort, Depends(Provide[Container.create_order])]
GetOrderDep = Annotated[GetOrderPort, Depends(Provide[Container.get_order])]
HandlePaymentCallbackDep = Annotated[
    HandlePaymentCallbackPort, Depends(Provide[Container.handle_payment_callback])
]
