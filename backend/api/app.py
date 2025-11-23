from fastapi import FastAPI
from .routes import etl

app = FastAPI()


app.include_router(etl.router, prefix="/api/v1/etl")
