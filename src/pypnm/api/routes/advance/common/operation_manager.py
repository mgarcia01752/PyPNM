
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from pypnm.api.routes.advance.common.types.types import OperationId
from pypnm.api.routes.common.classes.file_capture.types import GroupId
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.constants import cast

class OperationManager:
    """
    Manager for mapping background capture operations to their capture group IDs.

    Each operation is assigned a unique operation_id and linked to a
    capture_group_id. Mappings are persisted in a JSON file so that
    captures can be looked up later by operation ID.

    JSON schema:
    {
        "<operation_id>": {
            "capture_group_id": "<group_id>",
            "created": <unix_epoch_seconds>
        },
        ...
    }
    """
    def __init__(self, capture_group_id: GroupId, db_path: Optional[Path] = None) -> None:
        """
        Initialize a new operation manager for a given capture group.

        Args:
            capture_group_id: The ID of the capture group to associate.
            db_path: Optional path to the operations DB file; if None,
                     retrieves from ConfigManager under
                     [PnmFileRetrieval].operation_db.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.capture_group_id: GroupId = capture_group_id
        self.operation_id: OperationId = cast(OperationId, uuid.uuid4().hex[:16])

        # Resolve DB file path
        if db_path:
            self.db_path = db_path
        else:
            db_str = SystemConfigSettings.operation_db
            self.db_path = Path(db_str)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure DB exists
        if not self.db_path.exists():
            self._atomic_write({})

    def _load(self) -> Dict[str, Any]:
        """
        Load the operations DB from disk.

        Returns:
            Dict of operation mappings, or empty dict on parse error.
        """
        try:
            with self.db_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load operation DB, resetting: {e}")
            return {}

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """
        Atomically write the given data to the DB file.
        """
        temp = self.db_path.with_suffix('.tmp')
        with temp.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        temp.replace(self.db_path)

    def _save(self, data: Dict[str, Any]) -> None:
        """
        Persist the given operations dict to disk with atomic write.
        """
        try:
            self._atomic_write(data)
        except Exception as e:
            self.logger.error(f"Failed to save operation DB: {e}")

    def register(self) -> OperationId:
        """
        Register this operation with its capture group ID in the DB.

        Verifies that the associated capture group exists before registration.

        Returns:
            The operation_id assigned.

        Raises:
            ValueError: If the capture_group_id is not present in the CaptureGroup database.
        """
        # Verify that the capture group exists, or fail hard
        from pypnm.api.routes.common.classes.file_capture.capture_group import CaptureGroup
        cg = CaptureGroup(group_id=self.capture_group_id)
        if self.capture_group_id not in cg.list_groups():
            raise ValueError(
                f"CaptureGroup '{self.capture_group_id}' does not exist"
            )

        db = self._load()
        db[self.operation_id] = {
            "capture_group_id": self.capture_group_id,
            "created": int(time.time())
        }
        self._save(db)
        self.logger.info(
            f"Registered operation {self.operation_id} for group {self.capture_group_id}"
        )
        return self.operation_id

    @classmethod
    def get_capture_group(cls, operation_id: str, db_path: Optional[Path] = None) -> GroupId:
        """
        Retrieve the capture_group_id for a given operation_id.

        Args:
            operation_id: The operation ID to look up.
            db_path: Optional override for the operations DB file.

        Returns:
            capture_group_id if found, otherwise None.
            Exception thrown
        """
        
        if not db_path:
            db_str = SystemConfigSettings.operation_db
            db_path = Path(db_str)
        try:
            with db_path.open("r", encoding="utf-8") as f:
                db = json.load(f)
            rec = db.get(operation_id)
            return rec.get("capture_group_id") if isinstance(rec, dict) else None
        except Exception as e:
            cls.logger = logging.getLogger(cls.__name__)
            cls.logger.error(f"Error retrieving capture group for {operation_id}: {e}")
            return ""

    @classmethod
    def list_operations(cls, db_path: Optional[Path] = None) -> List[str]:
        """
        List all registered operation IDs.

        Args:
            db_path: Optional override for the operations DB file.

        Returns:
            List of operation_id strings.
        """
        if not db_path:
            db_str = SystemConfigSettings.operation_db
            db_path = Path(db_str)
        try:
            with db_path.open("r", encoding="utf-8") as f:
                return list(json.load(f).keys())
        except Exception as e:
            logging.getLogger(cls.__name__).error(f"Error listing operations: {e}")
            return []