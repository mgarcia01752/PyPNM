# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.routes.pypmn.system.config.schemas import SystemConfigModel
from config.config_manager import ConfigManager
from config.pnm_config_manager import PnmConfigManager

class PyPnmSystemConfigAPI:
    """
    API class for managing PyPNM system configuration.

    Provides endpoints to retrieve and update the application configuration
    stored in a JSON file (typically located at `config/system.json`).
    """

    def __init__(self):
        """
        Initializes the SystemConfigAPI instance and sets up the route handlers.
        """
        self.router = APIRouter(
            prefix="/pypnm/system/config",
            tags=["PyPNM System Configuration"]
        )
        self.router.post("/get", summary="Get PyPNM System Config")(self.get_system_config)
        self.router.post("/update", summary="Update PyPNM System Config")(self.update_system_config)

    async def get_system_config(self):
        """
        Retrieves the entire PyPNM System Configuration.

        Returns:
            
            JSONResponse: A success response containing the full configuration dictionary
        """
        try:
            cm = ConfigManager()
            config = cm.as_dict()
            return JSONResponse(content={"status": "success", "data": config})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load config: {e}")

    async def update_system_config(self, config_update: SystemConfigModel):
        """
        Updates the PyPNM System Configuration with the Provided Values.

        Args:
        
            config_update (SystemConfigModel): The new configuration to be saved.

        Returns:
        
            JSONResponse: A success response if the config was saved and reloaded successfully
        """
        try:
            cm = ConfigManager()
            cm.save(config_update.model_dump())
            PnmConfigManager.reload()
            return JSONResponse(content={"status": "success", "message": "Configuration updated"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {e}")


router = PyPnmSystemConfigAPI().router
