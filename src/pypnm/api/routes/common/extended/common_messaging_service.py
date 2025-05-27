# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import json
from typing import Any, Dict, List, Optional, Tuple
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode

class MessageResponseType(Enum):
    """
    Enumeration of message types for categorizing responses.
    """
    PNM_FILE_TRANSACTION = 1
    
class MessageResponse:
    """
    Represents a structured response with a status and optional data payload.

    Attributes:
        status (ServiceStatusCode): Status of the message.
        payload (Optional[Any]): Associated payload (list, dict, etc.).
        
    Example:
        
        {
            "status":"SUCCESS",
            "payload":[
                {
                    "status":"SUCCESS",
                    "message_type":"PNM_FILE_TRANSACTION",
                    "message":{
                        "transaction_id":"275de83146e904d7",
                        "filename":"ds_ofdm_rxmer_per_subcar_00:50:f1:12:e2:63_954000000_1746501260.bin"
                    }
                }
            ]
        }
    
    """

    def __init__(self, status: ServiceStatusCode, payload: Optional[Any] = None):
        """
        Initializes a MessageResponse instance.

        Args:
            status (ServiceStatusCode): Status of the message.
            payload (Optional[Any]): Optional message payload.
        """
        self.status:ServiceStatusCode = status
        self.payload:Optional[Any] = payload

    def get(self) -> Dict[str, Any]:
        """
        Serializes the message response to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary with 'status' and 'data'.
        """
        return {
            "status": self.status.name,
            "payload": self.payload
        }
    
    def __repr__(self):
        return json.dumps({
            "status": self.status.name,
            "payload": self.payload
        })

    def __str__(self):
        return self.__repr__()

    def get_payload_msg(payload_element: Dict[str, Any]) -> Tuple[str, str, Any]:
        """
        Extracts 'status', 'message_type', and 'message' from a payload element.

        Args:
            payload_element (Dict[str, Any]): The payload dictionary.

        Returns:
            Tuple[str, str, Any]: A tuple containing the status, message type, and message content.
        """
        status = payload_element.get("status", "UNKNOWN")
        message_type = payload_element.get("message_type", "UNKNOWN")
        message = payload_element.get("message", None)
        return status, message_type, message

    def payload_to_dict(self, key: str = "data") -> Dict[Any, Any]:
        """
        Wraps the internal payload in a dictionary under the specified key.

        Args:
            key (str): The key under which the payload will be stored. Defaults to "data".

        Returns:
            Dict[Any, Any]: A dictionary containing the payload under the given key.
        """
        return {key: self.payload}

        
class CommonMessagingService:
    """
    Core service to manage multi-step messaging logic, aggregating statuses and data across tasks.

    This service tracks all status/data pairs and determines the final output status. Useful for
    batch operations, chained service calls, and aggregating results for client APIs.

    Attributes:
        _messages (List[Tuple[ServiceStatusCode, Dict[str, Any]]]): Queue of messages.
        _last_non_success_status (ServiceStatusCode): Most recent non-success status seen.
    """

    def __init__(self):
        """
        Initializes an empty messaging service instance.
        """
        self._messages: List[Tuple[ServiceStatusCode, Dict[str, Any]]] = []
        self._last_non_success_status = ServiceStatusCode.SUCCESS

    def build_msg(self, status: ServiceStatusCode, payload: Optional[Dict[str, Any]] = None):
        """
        Queues a new message with status and optional data.

        Args:
            status (ServiceStatusCode): Message status.
            payload (Optional[Dict[str, Any]]): Associated data for the message.

        Returns:
            bool: Always returns True after storing the message.
        """
        if status != ServiceStatusCode.SUCCESS:
            self._last_non_success_status = status

        self._messages.append((status, payload or {}))

    def send_msg(self) -> MessageResponse:
        """
        Constructs a final MessageResponse from the stored message queue.

        The returned status is either the last non-success seen or the status of the last message.

        Returns:
            MessageResponse: Aggregated response with status and list of all message data.
        """
        final_status = (
            self._last_non_success_status
            if self._last_non_success_status != ServiceStatusCode.SUCCESS
            else self._messages[-1][0]
            if self._messages
            else ServiceStatusCode.UNKNOWN
        )

        combined_data = [
            {
                "status": status.name,
                **data
            } for status, data in self._messages
        ]

        self._messages.clear()

        return MessageResponse(final_status, combined_data)

    def build_send_msg(self, status: ServiceStatusCode, data: Optional[Dict[str, Any]] = None) -> MessageResponse:
        """
        Builds and immediately sends a single message.

        Args:
            status (ServiceStatusCode): Status of the message.
            data (Optional[Dict[str, Any]]): Optional data to include.

        Returns:
            MessageResponse: Final response containing the given status and data.
        """
        self.build_msg(status, data)
        return self.send_msg()

    def build_transaction_msg(self, transaction_id: str, filename: str,
                              status: ServiceStatusCode = ServiceStatusCode.SUCCESS):
        """
        Adds a transaction message with an ID and filename to the message queue.

        Args:
            transaction_id (str): Unique transaction identifier.
            filename (str): File name tied to the transaction.
            status (ServiceStatusCode): Message status. Defaults to SUCCESS.

        Returns:
            bool: True if message is successfully added.
        """
        self.build_msg(status, {
            "message_type": MessageResponseType.PNM_FILE_TRANSACTION.name,
            "message": {
                "transaction_id": transaction_id,
                "filename": filename
            }
        })

    def get_first_of_type(self, msg_type: MessageResponseType) -> Optional[Dict[str, Any]]:
        """
        Retrieves the first message of a specified type, if available.

        Args:
            msg_type (MessageResponseType): The type to look for.

        Returns:
            Optional[Dict[str, Any]]: The first message of the given type, or None.
        """
        for _, data in self._messages:
            if data.get("message_type") == msg_type.name:
                return data
        return None
