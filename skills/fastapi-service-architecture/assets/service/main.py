"""Deployable entry point.

This file is the only place that decides which routers this process serves.
Splitting a service out later is a matter of adding another main.py that mounts a
subset - the routes, repositories, and schemas do not move.
"""

from fastapi import Depends

from common.app import create_app
from common.security import get_principal
from service.routes import widgets_router

app = create_app(
    title="service",
    description="Service API.",
    distribution="my-distribution-name",
)

# Auth is applied when the router is mounted, not on each handler. One line here
# covers every current and future endpoint on the router, so a new route is
# authenticated by default instead of by remembering. Mount public routers
# (webhooks, OAuth callbacks) without the dependency and give them their own
# signature verification.
app.include_router(widgets_router, dependencies=[Depends(get_principal)])


if __name__ == "__main__":
    import uvicorn

    from common.settings import get_settings

    uvicorn.run(
        "service.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not get_settings().is_production,
    )
