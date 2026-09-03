import sys

with open("backend/app/main.py", "r") as f:
    content = f.read()

import_str = "from fastapi.responses import FileResponse, JSONResponse\nfrom fastapi.requests import Request\nfrom app.core.exceptions import DataUnavailableError, NoSafeRouteError\n"
content = content.replace("from fastapi.responses import FileResponse, JSONResponse\n", import_str)

handlers = """
@app.exception_handler(DataUnavailableError)
async def data_unavailable_exception_handler(request: Request, exc: DataUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc), "error": "DATA_UNAVAILABLE"}
    )

@app.exception_handler(NoSafeRouteError)
async def no_safe_route_exception_handler(request: Request, exc: NoSafeRouteError):
    return JSONResponse(
        status_code=200,
        content={"error": "REJECTED_NO_SAFE_ROUTE", "message": str(exc)}
    )

# Register main API routers
"""
content = content.replace("# Register main API routers\n", handlers)

with open("backend/app/main.py", "w") as f:
    f.write(content)

print("Patched main.py")
