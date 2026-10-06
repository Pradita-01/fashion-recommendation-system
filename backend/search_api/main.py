from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from search_api.routes.health import router as health_router
from search_api.routes.products import router as products_router
from search_api.routes.search import router as search_router
from search_api.routes.parse import router as parse_router
from search_api.routes.recommend import router as recommend_router

app = FastAPI(
    title="Fashion Recommendation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(products_router)
app.include_router(search_router)
app.include_router(parse_router)
app.include_router(recommend_router)
