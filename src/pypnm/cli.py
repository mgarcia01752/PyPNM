import uvicorn

def main():
    print("🚀 Starting PyPNM FastAPI server...")
    uvicorn.run("pypnm.api.main:app", host="127.0.0.1", port=8000, reload=True)
