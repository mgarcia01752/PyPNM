
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import abc
from typing import TypeVar, Type, Any, Tuple, Dict

from pypnm.api.routes.advance.common.capture_service import AbstractCaptureService

T = TypeVar("T", bound=AbstractCaptureService)

class AbstractService(abc.ABC):
    """
    Base router class managing the lifecycle of capture service instances.

    Responsibilities:
        - Instantiate and start capture services using load_service().
        - Store service instances keyed by operation ID in an internal registry.
        - Provide get_service() for retrieving active services in route handlers.

    Attributes:
        _service_store (Dict[str, AbstractCaptureService]):
            Registry mapping operation IDs to service instances.
    """

    def __init__(self) -> None:
        """
        Initialize the internal service registry.
        """
        self._service_store: Dict[str, AbstractCaptureService] = {}

    async def loadService(
        self,
        service_cls: Type[T],
        *args: Any,
        **kwargs: Any) -> Tuple[str, str]:
        """
        Instantiate, start, and register a capture service.

        Args:
            service_cls (Type[T]): Capture service class to instantiate.
            *args: Positional args for the service constructor.
            **kwargs: Keyword args for the service constructor.

        Returns:
            Tuple[str, str]: (group_id, operation_id) returned by service.start().

        Raises:
            Exception: Propagates errors from instantiation or startup.
        """
        service: T = service_cls(*args, **kwargs)
        group_id, operation_id = await service.start()
        self._service_store[operation_id] = service
        return group_id, operation_id

    def getService(self, operation_id: str) -> AbstractCaptureService:
        """
        Retrieve a previously loaded service by its operation ID.

        Args:
            operation_id (str): The ID returned by load_service().

        Returns:
            AbstractCaptureService: The associated service instance.

        Raises:
            KeyError: If no service exists for the given operation ID.
        """
        try:
            return self._service_store[operation_id]
        except KeyError:
            raise KeyError(f"No service loaded for operation_id '{operation_id}'")
