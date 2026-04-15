"""
Semantic Router initialisation.

Builds a RouteLayer using the HuggingFace encoder that is consistent
with the embedding model used for document ingestion.
"""

from semantic_router import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from app.config.settings import settings
from app.routing.routes import ALL_ROUTES


def build_route_layer() -> SemanticRouter:
    """
    Create and return a configured SemanticRouter instance.

    The encoder uses the same HuggingFace model specified in project
    settings so that the semantic space is consistent with the vector store.
    """
    encoder = HuggingFaceEncoder(name=settings.EMBEDDING_MODEL_NAME)
    route_layer = SemanticRouter(encoder=encoder, routes=ALL_ROUTES)
    # In semantic-router v0.1.x, we must explicitly sync the index 
    # to avoid the "ValueError: Index is not ready." error.
    route_layer.sync("local")
    return route_layer


# Module-level singleton – imported by the service layer.
semantic_router = build_route_layer()
