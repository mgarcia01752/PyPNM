# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import importlib
import logging
import pathlib
from fastapi import FastAPI
from typing import Optional

logger = logging.getLogger(__name__)

def auto_register_routers(app: FastAPI, base_dir: Optional[str] = "src/api/routes") -> None:
    """
    Automatically discovers and registers FastAPI routers from all 'router.py' files under the given base directory.

    Args:
        app (FastAPI): The FastAPI application instance to register routers on.
        base_dir (Optional[str]): Base directory path to start searching for router.py files.
                                  Defaults to "src/api/routes".

    The function recursively searches for files named 'router.py', converts their filesystem path
    to a Python module path, imports the module, and includes the 'router' object if present.
    """
    base_path = pathlib.Path(base_dir).resolve()
    logger.debug(f"START-AUTO-LOADING routers from path: {base_path}")

    for router_file in base_path.rglob("router.py"):
        if not router_file.is_file():
            logger.debug(f"Skipping non-file: {router_file}")
            continue
        logger.debug(f"Found router file: {router_file}")

        try:
            # OS-independent module path, e.g. src.api.routes.some.router
            module_path = ".".join(router_file.relative_to(pathlib.Path.cwd()).with_suffix("").parts)
        except Exception as rel_err:
            logger.debug(f"Failed to get relative module path for {router_file}: {rel_err}")
            # fallback to absolute path parts, may fail if outside sys.path
            module_path = ".".join(router_file.with_suffix("").parts)

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as mnfe:
            logger.error(f"Module not found for {module_path}: {mnfe}")
            continue
        except Exception as imp_err:
            logger.error(f"Failed to import module {module_path}: {imp_err}")
            continue

        router = getattr(module, "router", None)
        if router is None:
            logger.debug(f"Module '{module_path}' does not define 'router' attribute.")
            continue

        try:
            app.include_router(router)
            logger.debug(f"[AUTO-ROUTER] Successfully loaded router from '{module_path}'")
        except Exception as e:
            logger.error(f"Failed to include router from {module_path}: {e}")

    logger.debug("DONE-AUTO-LOADING routers")
