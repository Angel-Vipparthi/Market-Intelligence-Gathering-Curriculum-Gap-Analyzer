import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Analyze review feedback to improve agent skills."""

    def __init__(self):
        self.client = get_supabase_client()

    def store_feedback(
        self,
        decision_id: str,
        feedback_type: str,
        content: str,
        skill_name: str | None = None,
    ) -> str:
        """Store a feedback entry linked to a review decision.

        Args:
            decision_id: UUID of the review decision this feedback relates to.
            feedback_type: Type of feedback (e.g., 'correction', 'suggestion', 'praise').
            content: The feedback content text.
            skill_name: Optional name of the agent skill this feedback applies to.

        Returns:
            The UUID of the created feedback record.
        """
        feedback_id = str(uuid4())

        data = {
            "id": feedback_id,
            "decision_id": decision_id,
            "feedback_type": feedback_type,
            "feedback_content": content,
            "is_actionable": feedback_type in ("correction", "suggestion"),
            "is_processed": False,
        }

        if skill_name:
            data["skill_name"] = skill_name

        try:
            self.client.table("review_feedback").insert(data).execute()
            logger.info(f"Stored feedback {feedback_id} for decision {decision_id}")
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            raise

        return feedback_id

    def analyze_rejection_patterns(
        self, skill_name: str, window_days: int = 30
    ) -> dict[str, Any]:
        """Analyze patterns in rejections for a specific skill over a time window.

        Args:
            skill_name: Name of the agent skill to analyze.
            window_days: Number of days to look back.

        Returns:
            Dict with rejection_rate, common_issues, and suggested_improvements.
        """
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=window_days)
        ).isoformat()

        try:
            # Get all review decisions for this skill's outputs
            all_decisions = (
                self.client.table("review_decisions")
                .select("*")
                .gte("created_at", cutoff)
                .execute()
            )

            decisions = all_decisions.data or []

            # If skill_name refers to an entity_type pattern, filter accordingly
            skill_decisions = [
                d for d in decisions if d.get("entity_type", "") == skill_name
            ]

            # If no direct match, use all decisions
            if not skill_decisions:
                skill_decisions = decisions

            total = len(skill_decisions)
            if total == 0:
                return {
                    "rejection_rate": 0.0,
                    "common_issues": [],
                    "suggested_improvements": [],
                    "total_decisions": 0,
                }

            rejections = [d for d in skill_decisions if d.get("decision") == "rejected"]
            rejection_rate = len(rejections) / total

            # Analyze rejection comments for common issues
            issue_counts: dict[str, int] = {}
            for rejection in rejections:
                comments = rejection.get("comments") or ""
                if comments:
                    lower_comments = comments.lower()
                    for keyword in [
                        "inaccurate",
                        "missing",
                        "wrong",
                        "incomplete",
                        "outdated",
                        "irrelevant",
                        "low quality",
                        "hallucination",
                        "false positive",
                        "too broad",
                        "too narrow",
                    ]:
                        if keyword in lower_comments:
                            issue_counts[keyword] = issue_counts.get(keyword, 0) + 1

            common_issues = sorted(
                issue_counts.items(), key=lambda x: x[1], reverse=True
            )

            # Get related feedback entries
            rejection_ids = [r["id"] for r in rejections]
            suggested_improvements = []

            if rejection_ids:
                try:
                    feedback_result = (
                        self.client.table("review_feedback")
                        .select("feedback_content")
                        .in_("decision_id", rejection_ids)
                        .eq("is_actionable", True)
                        .execute()
                    )
                    suggested_improvements = [
                        f.get("feedback_content", "")
                        for f in (feedback_result.data or [])
                        if f.get("feedback_content")
                    ]
                except Exception:
                    pass

            return {
                "rejection_rate": round(rejection_rate, 3),
                "common_issues": [
                    {"issue": issue, "count": count} for issue, count in common_issues
                ],
                "suggested_improvements": suggested_improvements,
                "total_decisions": total,
                "total_rejections": len(rejections),
            }

        except Exception as e:
            logger.error(f"Failed to analyze rejection patterns: {e}")
            return {
                "rejection_rate": 0.0,
                "common_issues": [],
                "suggested_improvements": [],
                "error": str(e),
            }

    def get_skill_performance(self, skill_id: str) -> dict[str, Any]:
        """Get performance metrics for a specific agent skill.

        Args:
            skill_id: UUID of the agent skill.

        Returns:
            Dict with usage_count, success_rate, avg_confidence, rejection_rate.
        """
        try:
            # Get the skill record
            skill_result = (
                self.client.table("agent_skills")
                .select("*")
                .eq("id", skill_id)
                .execute()
            )

            if not skill_result.data:
                return {
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "avg_confidence": 0.0,
                    "rejection_rate": 0.0,
                }

            skill = skill_result.data[0]
            skill_name = skill.get("skill_name", "")

            # Get workflow runs involving this skill
            try:
                runs = (
                    self.client.table("workflow_costs")
                    .select("workflow_run_id, workflow_type")
                    .ilike("node_name", f"%{skill_name}%")
                    .execute()
                )
                usage_count = len(set(r["workflow_run_id"] for r in (runs.data or [])))
            except Exception:
                usage_count = 0

            # Get review decisions to compute success/rejection rate
            entity_type = "digest" if "digest" in skill_name.lower() else "gap"
            try:
                decisions = (
                    self.client.table("review_decisions")
                    .select("decision")
                    .eq("entity_type", entity_type)
                    .execute()
                )

                total_decisions = len(decisions.data or [])
                if total_decisions > 0:
                    approvals = sum(
                        1
                        for d in decisions.data
                        if d.get("decision") == "approved"
                    )
                    rejections = sum(
                        1
                        for d in decisions.data
                        if d.get("decision") == "rejected"
                    )
                    success_rate = approvals / total_decisions
                    rejection_rate = rejections / total_decisions
                else:
                    success_rate = 0.0
                    rejection_rate = 0.0
            except Exception:
                success_rate = 0.0
                rejection_rate = 0.0

            # Average confidence from outputs
            avg_confidence = skill.get("current_score", 0.0)

            return {
                "usage_count": usage_count,
                "success_rate": round(success_rate, 3),
                "avg_confidence": round(avg_confidence, 3),
                "rejection_rate": round(rejection_rate, 3),
            }

        except Exception as e:
            logger.error(f"Failed to get skill performance: {e}")
            return {
                "usage_count": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "rejection_rate": 0.0,
                "error": str(e),
            }
