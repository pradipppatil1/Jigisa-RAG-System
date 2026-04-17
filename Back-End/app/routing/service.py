"""
Routing Service — the main entry-point for semantic query classification.

Responsibilities:
  1. Classify a user query into one of the 5 defined routes.
  2. Intersect the classification with the user's RBAC role.
  3. Log every routing decision to the MySQL routing_logs table.
  4. Return a structured RoutingResult.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.routing.router import semantic_router
from app.routing.schemas import RoutingResult
from app.core.database import SessionLocal
from app.models.routing_log import RoutingLog

logger = logging.getLogger(__name__)

# ── RBAC Matrix ──────────────────────────────────────────────────────────
# Maps each user role to the set of routes it is allowed to access.
ROLE_ACCESS_MAP: dict[str, set[str]] = {
    "employee":    {"hr_general_route"},
    "finance":     {"hr_general_route", "finance_route"},
    "engineering": {"hr_general_route", "engineering_route"},
    "marketing":   {"hr_general_route", "marketing_route"},
    "c_level":     {
        "hr_general_route",
        "finance_route",
        "engineering_route",
        "marketing_route",
        "cross_department_route",
    },
}

# Maps route names to human-readable department names for messages.
ROUTE_DEPARTMENT_MAP: dict[str, str] = {
    "finance_route":          "Finance",
    "engineering_route":      "Engineering",
    "marketing_route":        "Marketing",
    "hr_general_route":       "HR / General",
    "cross_department_route": "Cross-Department",
}

# Maps route names to the Qdrant collection names they target.
ROUTE_COLLECTION_MAP: dict[str, list[str]] = {
    "finance_route":          ["finance"],
    "engineering_route":      ["engineering"],
    "marketing_route":        ["marketing"],
    "hr_general_route":       ["general"],
    "cross_department_route": ["general", "finance", "engineering", "marketing"],
}


class RoutingService:
    """Stateless service that classifies queries and enforces RBAC."""

    # ── public API ───────────────────────────────────────────────────────

    def route_query(
        self,
        query: str,
        user_role: str,
        user_id: Optional[str] = None,
    ) -> RoutingResult:
        """
        Classify *query*, check RBAC for *user_role*, persist the log,
        and return a ``RoutingResult``.
        """
        # 1. Classify the query
        route_result = semantic_router(query)
        route_name: Optional[str] = route_result.name if route_result else None
        confidence: float = 0.0

        # semantic-router may expose a similarity score
        if hasattr(route_result, "similarity_score") and route_result.similarity_score is not None:
            confidence = float(route_result.similarity_score)
        elif hasattr(route_result, "score") and route_result.score is not None:
            confidence = float(route_result.score)

        # 1.5 Keyword Heuristic Override
        # If the user explicitly mentions a department, we can prioritize that
        # route over the semantic embeddings, especially if it aligns with their role.
        query_lower = query.lower()
        if "finance" in query_lower or "financial" in query_lower or "revenue" in query_lower or "profit" in query_lower or "budget" in query_lower:
            route_name = "finance_route"
        elif "marketing" in query_lower or "campaign" in query_lower or "brand" in query_lower:
            route_name = "marketing_route"
        elif "engineering" in query_lower or "architecture" in query_lower or "deployment" in query_lower or "kubernetes" in query_lower:
            route_name = "engineering_route"
        elif (
            "hr " in query_lower or "human resources" in query_lower or "hr" == query_lower
            or "leave" in query_lower or "leaves" in query_lower
            or "policy" in query_lower or "policies" in query_lower
            or "handbook" in query_lower or "benefit" in query_lower
            or "vacation" in query_lower or "sick day" in query_lower
            or "holiday" in query_lower or "time off" in query_lower
            or "maternity" in query_lower or "paternity" in query_lower
            or "attendance" in query_lower or "employee" in query_lower
        ):
            route_name = "hr_general_route"

        # 2. Handle unclassified queries
        if route_name is None:
            result = RoutingResult(
                route_name=None,
                confidence=confidence,
                is_authorized=False,
                message="I could not determine the intent of your query. "
                        "Could you please rephrase your question?",
                collections=[],
            )
            self._log(user_id, user_role, query, result)
            return result

        # 3. RBAC check
        allowed_routes = ROLE_ACCESS_MAP.get(user_role, set())
        is_authorized = route_name in allowed_routes

        if is_authorized:
            # Determine target collections
            collections = ROUTE_COLLECTION_MAP.get(route_name, [])

            # For cross-department, filter to only authorised collections
            if route_name == "cross_department_route" and user_role != "c_level":
                user_collections = self._get_user_collections(user_role)
                collections = [c for c in collections if c in user_collections]

            result = RoutingResult(
                route_name=route_name,
                confidence=confidence,
                is_authorized=True,
                message=None,
                collections=collections,
            )
        else:
            department = ROUTE_DEPARTMENT_MAP.get(route_name, route_name)
            result = RoutingResult(
                route_name=route_name,
                confidence=confidence,
                is_authorized=False,
                message=(
                    f"I'm sorry, but you do not have authorization to access "
                    f"{department} records. Please contact the {department} "
                    f"department for assistance."
                ),
                collections=[],
            )

        # 4. Log to MySQL
        self._log(user_id, user_role, query, result)
        return result

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _get_user_collections(user_role: str) -> set[str]:
        """Return the set of Qdrant collection names a role can access."""
        allowed_routes = ROLE_ACCESS_MAP.get(user_role, set())
        collections: set[str] = set()
        for route in allowed_routes:
            collections.update(ROUTE_COLLECTION_MAP.get(route, []))
        return collections

    @staticmethod
    def _log(
        user_id: Optional[str],
        user_role: str,
        query: str,
        result: RoutingResult,
    ) -> None:
        """Persist a routing log entry to the MySQL routing_logs table."""
        try:
            db = SessionLocal()
            log_entry = RoutingLog(
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                user_role=user_role,
                query=query,
                route_selected=result.route_name,
                confidence=result.confidence,
                is_authorized=result.is_authorized,
                message=result.message,
            )
            db.add(log_entry)
            db.commit()
            logger.info(
                "Routing log | role=%s | route=%s | authorized=%s | query=%s",
                user_role,
                result.route_name,
                result.is_authorized,
                query[:80],
            )
        except Exception as exc:
            logger.error("Failed to persist routing log: %s", exc)
            db.rollback()
        finally:
            db.close()


# Module-level singleton
routing_service = RoutingService()
