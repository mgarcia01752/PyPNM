import importlib
import pathlib
import sys
from fastapi import FastAPI

def auto_register_routers(app: FastAPI):
    """
    Auto-discovers and registers FastAPI routers by looking for 'router.py' files
    under src/pypnm/api/routes. Skips files explicitly marked as non-routable.
    """
    print("🔧 Starting auto_register_routers()")

    # Find project root (up to 'pypnm')
    project_root = pathlib.Path(__file__).resolve()
    while project_root.name != "pypnm":
        if project_root == project_root.parent:
            print("❌ Could not find 'pypnm' directory.")
            return
        project_root = project_root.parent

    routes_path = project_root / "api" / "routes"
    if not routes_path.exists():
        print(f"❌ Path not found: {routes_path}")
        return

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"📦 Added to sys.path: {project_root}")

    print(f"🔍 Scanning for router.py files under: {routes_path}\n")

    for router_file in routes_path.rglob("router.py"):
        print(f"📄 Found: {router_file}")
        try:
            relative_path = router_file.relative_to(project_root).with_suffix("")
            module_path = ".".join(relative_path.parts)
            print(f"🔗 Importing module: {module_path}")

            module = importlib.import_module(module_path)

            if getattr(module, "__skip_autoregister__", False):
                print(f"⏭️  Skipped (marked non-routable): {module_path}")
                continue

            router = getattr(module, "router", None)
            if router is None:
                print(f"⚠️  No 'router' found in module: {module_path}")
                continue

            app.include_router(router)
            print(f"✅ Registered router from: {module_path}")

        except Exception as e:
            print(f"❌ Failed to import or register: {router_file}\n   ↪ {e}")

    print("\n✅ Finished auto_register_routers()\n")
