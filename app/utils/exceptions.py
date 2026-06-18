class AppBaseException(Exception):
    """
    Base class for all custom application exceptions.
    """

    def __init__(
        self, user_message: str, internal_detail: str = None, status_code: int = 500
    ):
        self.user_message = user_message  # shown to API consumer
        self.internal_detail = internal_detail  # only logged internally
        self.status_code = status_code
        super().__init__(internal_detail or user_message)


class RepositoryException(AppBaseException):
    """Raised when database/repository operations fail."""

    def __init__(self, internal_detail: str):
        super().__init__(
            user_message="A data access error occurred. Please try again later.",
            internal_detail=internal_detail,
            status_code=500,
        )


class ServiceException(AppBaseException):
    """Raised when business logic fails unexpectedly."""

    def __init__(self, internal_detail: str):
        super().__init__(
            user_message="An internal error occurred while processing your request.",
            internal_detail=internal_detail,
            status_code=500,
        )


class UserAlreadyExistsException(AppBaseException):
    """Raised when a user with the same email already exists."""

    def __init__(self, user_message: str):
        super().__init__(
            user_message=user_message, internal_detail=user_message, status_code=400
        )


class UserNotFoundException(AppBaseException):
    """Raised when a user with the given email is not found."""

    def __init__(self, user_message: str, internal_detail: str = None):
        super().__init__(
            user_message=user_message, internal_detail=internal_detail, status_code=404
        )

class TenantAlreadyExistsException(AppBaseException):
    """Raised when a tenant with the same name already exists."""
    def __init__(self, internal_detail: str = None):
        super().__init__(
            user_message="Tenant with this name already exists", internal_detail=internal_detail, status_code=400
        )

class TenantSlugAlreadyExistsException(AppBaseException):
    """Raised when a tenant with the same slug already exists."""
    def __init__(self, internal_detail: str = None):
        super().__init__(
            user_message="Tenant with this name or slug already exists", internal_detail=internal_detail, status_code=400
        )

class TenantNotFoundException(AppBaseException):
    """Raised when a tenant with the given name is not found."""
    def __init__(self, internal_detail: str = None):
        super().__init__(
            user_message="Tenant not found", internal_detail=internal_detail, status_code=404
        )

class PropertyAlreadyExistsException(AppBaseException):
    """Raised when a property with the same name already exists."""
    def __init__(self, internal_detail: str = None):
        super().__init__(
            user_message="Property with this name already exists", internal_detail=internal_detail, status_code=400
        )

class PropertyNotFoundException(AppBaseException):
    """Raised when a property with the given name is not found."""
    def __init__(self, internal_detail: str = None):
        super().__init__(
            user_message="Property not found", internal_detail=internal_detail, status_code=404
        )
