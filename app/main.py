import uvicorn
import databases

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from api.users import users_router
from api.auth import auth_router
from api.dao import dao_router
from api.util import util_router
from api.activities import activity_router
from api.proposals import proposal_router
from api.notifications import notification_router
from api.assets import assets_router
from api.blogs import blogs_router
from api.faq import faq_router
from api.quotes import quotes_router


from config import Config, Network


CFG = Config[Network]
DATABASE_URL = CFG.connection_string


database = databases.Database(DATABASE_URL)
Base: DeclarativeMeta = declarative_base()


app = FastAPI(title="paideia-api", docs_url="/api/docs", openapi_url="/api")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# origins = ["*"]
origins = [
    "https://*.paideia.im",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}


@app.get("/api/ping")
def ping():
    return {"status": "ok", "message": "Service is healthy"}


app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(dao_router, prefix="/api/dao", tags=["dao"])
app.include_router(proposal_router, prefix="/api/proposals", tags=["proposals"])
app.include_router(activity_router, prefix="/api/activities", tags=["activities"])
app.include_router(
    notification_router, prefix="/api/notificatons", tags=["notifications"]
)
app.include_router(blogs_router, prefix="/api/blogs", tags=["blogs"])
app.include_router(faq_router, prefix="/api/faq", tags=["faq"])
app.include_router(quotes_router, prefix="/api/quotes", tags=["quotes"])
app.include_router(util_router, prefix="/api/util", tags=["util"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
