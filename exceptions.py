class CustomAPIError(Exception):
    """Базовое исключение для ошибок, связанных с API."""
    pass


class EmptyKeyOrValue(CustomAPIError):
    """Ошибка при отсуствие ключа или значения."""
    pass


class EndpointAccessError(CustomAPIError):
    """Исключение для ошибок доступа к эндпоинту."""
    pass


class UnexpectedStatusCodeError(CustomAPIError):
    """Исключение для неожиданных статус-кодов."""
    pass


class EmptyResponseAPI(CustomAPIError):

    pass