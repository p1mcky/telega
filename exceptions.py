class APIError(Exception):
    """Базовое исключение для ошибок, связанных с API."""


class EmptyKeyOrValue(APIError):
    """Ошибка при отсуствие ключа или значения."""
    pass


class EndpointAccessError(APIError):
    """Исключение для ошибок доступа к эндпоинту."""
    pass


class UnexpectedStatusCodeError(APIError):
    """Исключение для неожиданных статус-кодов."""
    pass


class EmptyResponseAPI(APIError):
    """Исключение, возникающее при получении пустого ответа от API."""
    pass
