from fastapi import FastAPI

from app.api.private.v1.private_router import private_router
from app.api.public.v1.public_router import public_router
from app.api.root_path import base_router
from app.core.settings import get_settings

app = FastAPI(
    title=get_settings().app_name,
    description="Manages device bootstrapping and provides an admin API for AWS IoT Core",
    version="1.0",
)

app.include_router(base_router)
app.include_router(public_router, prefix=get_settings().API_PUBLIC_V1_STR)
app.include_router(private_router, prefix=get_settings().API_PRIVATE_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        access_log=False,
        log_config="./log_conf.yaml",
    )
