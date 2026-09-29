class DomainError(Exception):
    pass


class OrderNotFound(DomainError):
    pass


class ItemNotFound(DomainError):
    pass


class InsufficientStock(DomainError):
    pass


class InvalidStatusTransition(DomainError):
    pass
