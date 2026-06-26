from fastapi import APIRouter
from app.api import urls, digests, gaps, skills, costs, evaluations, health, reviews, graph, knowledge_base

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(urls.router, prefix="/urls", tags=["urls"])
api_router.include_router(digests.router, prefix="/digests", tags=["digests"])
api_router.include_router(gaps.router, tags=["gaps"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(costs.router, prefix="/costs", tags=["costs"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(knowledge_base.router, prefix="/kb", tags=["knowledge-base"])
