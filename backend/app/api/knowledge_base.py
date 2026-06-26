import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Models ──────────────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    product_name: str
    course_name: str
    description: str | None = None

class ModuleCreate(BaseModel):
    course_id: str
    module_name: str
    description: str | None = None
    sort_order: int = 0

class SessionCreate(BaseModel):
    module_id: str
    title: str
    content_types: list[str] = Field(default_factory=list)
    level: int = Field(ge=1, le=7)
    skills: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    description: str | None = None
    sort_order: int = 0

class SessionUpdate(BaseModel):
    title: str | None = None
    content_types: list[str] | None = None
    level: int | None = Field(default=None, ge=1, le=7)
    skills: list[str] | None = None
    prerequisites: list[str] | None = None
    description: str | None = None
    sort_order: int | None = None


# ── Products ────────────────────────────────────────────────────────────

@router.get("/products")
async def list_products():
    client = get_supabase_client()
    result = client.table("kb_courses").select("product_name").execute()
    products = sorted(set(r["product_name"] for r in (result.data or [])))
    return {"items": products}


# ── Courses ─────────────────────────────────────────────────────────────

@router.get("/courses")
async def list_courses(product_name: str | None = Query(None)):
    client = get_supabase_client()
    query = client.table("kb_courses").select("*").eq("is_active", True)
    if product_name:
        query = query.eq("product_name", product_name)
    result = query.order("course_name").execute()
    return {"items": result.data or []}


@router.post("/courses")
async def create_course(payload: CourseCreate):
    client = get_supabase_client()
    try:
        result = client.table("kb_courses").insert(payload.model_dump()).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/courses/{course_id}")
async def delete_course(course_id: str):
    client = get_supabase_client()
    client.table("kb_courses").delete().eq("id", course_id).execute()
    return {"status": "deleted"}


# ── Modules ─────────────────────────────────────────────────────────────

@router.get("/modules")
async def list_modules(course_id: str = Query(...)):
    client = get_supabase_client()
    result = (
        client.table("kb_modules").select("*")
        .eq("course_id", course_id)
        .eq("is_active", True)
        .order("sort_order")
        .execute()
    )
    return {"items": result.data or []}


@router.post("/modules")
async def create_module(payload: ModuleCreate):
    client = get_supabase_client()
    try:
        result = client.table("kb_modules").insert(payload.model_dump()).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/modules/{module_id}")
async def delete_module(module_id: str):
    client = get_supabase_client()
    client.table("kb_modules").delete().eq("id", module_id).execute()
    return {"status": "deleted"}


# ── Sessions ────────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    module_id: str | None = Query(None),
    level: int | None = Query(None, ge=1, le=7),
    content_type: str | None = Query(None),
    skill: str | None = Query(None),
):
    client = get_supabase_client()
    query = client.table("kb_sessions").select("*").eq("is_active", True)
    if module_id:
        query = query.eq("module_id", module_id)
    if level:
        query = query.eq("level", level)
    if content_type:
        query = query.contains("content_types", [content_type])
    if skill:
        query = query.contains("skills", [skill])
    result = query.order("sort_order").execute()
    return {"items": result.data or []}


@router.post("/sessions")
async def create_session(payload: SessionCreate):
    client = get_supabase_client()
    valid_types = {"reading", "coding", "quiz", "video"}
    invalid = set(payload.content_types) - valid_types
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid content types: {invalid}")
    try:
        result = client.table("kb_sessions").insert(payload.model_dump()).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sessions/{session_id}")
async def update_session(session_id: str, payload: SessionUpdate):
    client = get_supabase_client()
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "content_types" in update:
        valid_types = {"reading", "coding", "quiz", "video"}
        invalid = set(update["content_types"]) - valid_types
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid content types: {invalid}")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        result = client.table("kb_sessions").update(update).eq("id", session_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    client = get_supabase_client()
    client.table("kb_sessions").delete().eq("id", session_id).execute()
    return {"status": "deleted"}


# ── Hierarchy view ──────────────────────────────────────────────────────

@router.get("/hierarchy")
async def get_hierarchy(
    product_name: str | None = Query(None),
    course_id: str | None = Query(None),
):
    client = get_supabase_client()

    course_query = client.table("kb_courses").select("*").eq("is_active", True)
    if product_name:
        course_query = course_query.eq("product_name", product_name)
    if course_id:
        course_query = course_query.eq("id", course_id)
    courses = course_query.order("course_name").execute().data or []

    course_ids = [c["id"] for c in courses]
    if not course_ids:
        return {"courses": []}

    modules = (
        client.table("kb_modules").select("*")
        .in_("course_id", course_ids)
        .eq("is_active", True)
        .order("sort_order")
        .execute().data or []
    )

    module_ids = [m["id"] for m in modules]
    sessions = []
    if module_ids:
        sessions = (
            client.table("kb_sessions").select("*")
            .in_("module_id", module_ids)
            .eq("is_active", True)
            .order("sort_order")
            .execute().data or []
        )

    sessions_by_module: dict[str, list] = {}
    for s in sessions:
        sessions_by_module.setdefault(s["module_id"], []).append(s)

    modules_by_course: dict[str, list] = {}
    for m in modules:
        m["sessions"] = sessions_by_module.get(m["id"], [])
        modules_by_course.setdefault(m["course_id"], []).append(m)

    hierarchy = []
    for c in courses:
        c["modules"] = modules_by_course.get(c["id"], [])
        total_sessions = sum(len(m["sessions"]) for m in c["modules"])
        c["total_modules"] = len(c["modules"])
        c["total_sessions"] = total_sessions
        hierarchy.append(c)

    return {"courses": hierarchy}


# ── Stats ───────────────────────────────────────────────────────────────

@router.get("/stats")
async def kb_stats(product_name: str | None = Query(None)):
    client = get_supabase_client()

    course_query = client.table("kb_courses").select("id", count="exact").eq("is_active", True)
    if product_name:
        course_query = course_query.eq("product_name", product_name)
    courses = course_query.execute()
    course_ids = [c["id"] for c in (courses.data or [])]

    total_modules = 0
    total_sessions = 0
    level_dist: dict[str, int] = {}
    content_dist: dict[str, int] = {}
    all_skills: dict[str, int] = {}

    if course_ids:
        modules = client.table("kb_modules").select("id").in_("course_id", course_ids).eq("is_active", True).execute()
        module_ids = [m["id"] for m in (modules.data or [])]
        total_modules = len(module_ids)

        if module_ids:
            sessions = client.table("kb_sessions").select("level, content_types, skills").in_("module_id", module_ids).eq("is_active", True).execute()
            total_sessions = len(sessions.data or [])

            for s in (sessions.data or []):
                lvl = s.get("level", 0)
                if 1 <= lvl <= 2:
                    bucket = "Beginner"
                elif 3 <= lvl <= 4:
                    bucket = "Intermediate"
                else:
                    bucket = "Advanced"
                level_dist[bucket] = level_dist.get(bucket, 0) + 1

                for ct in (s.get("content_types") or []):
                    content_dist[ct] = content_dist.get(ct, 0) + 1

                for sk in (s.get("skills") or []):
                    all_skills[sk] = all_skills.get(sk, 0) + 1

    return {
        "total_courses": courses.count or 0,
        "total_modules": total_modules,
        "total_sessions": total_sessions,
        "level_distribution": level_dist,
        "content_type_distribution": content_dist,
        "top_skills": dict(sorted(all_skills.items(), key=lambda x: -x[1])[:20]),
    }


# ── Connections ─────────────────────────────────────────────────────────

@router.get("/connections")
async def kb_connections(
    product_name: str | None = Query(None),
    course_id: str | None = Query(None),
):
    """Return nodes (sessions) and edges (prerequisites + shared skills) for visualization."""
    client = get_supabase_client()

    course_query = client.table("kb_courses").select("id, course_name").eq("is_active", True)
    if product_name:
        course_query = course_query.eq("product_name", product_name)
    if course_id:
        course_query = course_query.eq("id", course_id)
    courses = course_query.execute().data or []
    course_map = {c["id"]: c["course_name"] for c in courses}
    course_ids = list(course_map.keys())

    if not course_ids:
        return {"nodes": [], "edges": [], "skill_clusters": []}

    modules = (
        client.table("kb_modules").select("id, course_id, module_name")
        .in_("course_id", course_ids).eq("is_active", True)
        .order("sort_order").execute().data or []
    )
    module_map = {m["id"]: m for m in modules}
    module_ids = list(module_map.keys())

    if not module_ids:
        return {"nodes": [], "edges": [], "skill_clusters": []}

    sessions = (
        client.table("kb_sessions").select("id, module_id, title, level, skills, prerequisites, content_types")
        .in_("module_id", module_ids).eq("is_active", True)
        .order("sort_order").execute().data or []
    )

    # Build title→id lookup for prerequisite matching
    title_to_id: dict[str, str] = {}
    for s in sessions:
        title_to_id[s["title"].lower()] = s["id"]

    # Build nodes
    nodes = []
    for s in sessions:
        mod = module_map.get(s["module_id"], {})
        nodes.append({
            "id": s["id"],
            "title": s["title"],
            "level": s["level"],
            "skills": s.get("skills") or [],
            "content_types": s.get("content_types") or [],
            "module_name": mod.get("module_name", ""),
            "course_name": course_map.get(mod.get("course_id", ""), ""),
        })

    # Build edges
    edges = []
    # 1. Prerequisite edges
    for s in sessions:
        for prereq in (s.get("prerequisites") or []):
            prereq_id = title_to_id.get(prereq.lower())
            if prereq_id:
                edges.append({
                    "source": prereq_id,
                    "target": s["id"],
                    "type": "prerequisite",
                    "label": "prerequisite",
                })
            else:
                edges.append({
                    "source": prereq,
                    "target": s["id"],
                    "type": "prerequisite_unlinked",
                    "label": prereq,
                })

    # 2. Shared-skill edges (connect sessions sharing ≥2 skills)
    for i, s1 in enumerate(sessions):
        skills1 = set(s1.get("skills") or [])
        if not skills1:
            continue
        for s2 in sessions[i + 1:]:
            skills2 = set(s2.get("skills") or [])
            shared = skills1 & skills2
            if len(shared) >= 2:
                edges.append({
                    "source": s1["id"],
                    "target": s2["id"],
                    "type": "shared_skills",
                    "label": ", ".join(sorted(shared)),
                })

    # 3. Skill clusters
    skill_sessions: dict[str, list[str]] = {}
    for s in sessions:
        for sk in (s.get("skills") or []):
            skill_sessions.setdefault(sk, []).append(s["title"])

    skill_clusters = [
        {"skill": sk, "sessions": titles, "count": len(titles)}
        for sk, titles in sorted(skill_sessions.items(), key=lambda x: -len(x[1]))
        if len(titles) >= 2
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "skill_clusters": skill_clusters[:20],
        "total_connections": len(edges),
        "prereq_chains": sum(1 for e in edges if e["type"] == "prerequisite"),
        "skill_links": sum(1 for e in edges if e["type"] == "shared_skills"),
    }


# ── Module quiz mapping ────────────────────────────────────────────────
# Maps module names → which Module Quiz(es) contain their assessments
MODULE_QUIZ_MAP: dict[str, list[str]] = {
    "Introduction to React JS and States": ["Module Quiz - 1"],
    "Introduction to State Hook": ["Module Quiz - 2"],
    "Effect Hook and Rules of Hooks": ["Module Quiz - 3"],
    "Routing using React Router": ["Module Quiz - 4"],
    "Authentication & Authorization": ["Module Quiz - 5"],
    "React Context": ["Module Quiz - 6"],
}

# ── Session Content ────────────────────────────────────────────────────

@router.get("/session-content")
async def get_session_content(
    session_title: str = Query(...),
    module_name: str | None = Query(None),
):
    """Return reading material, MCQ questions, and coding practice for a session."""
    client = get_supabase_client()

    # 1. Reading material
    reading = (
        client.table("curriculum_documents").select("title, content, tools")
        .eq("document_type", "session").eq("title", session_title)
        .execute().data or []
    )

    # 2. MCQ questions from curriculum_assessments
    mcqs: list[dict] = []
    if module_name:
        quiz_names = MODULE_QUIZ_MAP.get(module_name, [])
        for qn in quiz_names:
            rows = (
                client.table("curriculum_assessments")
                .select("question_content, question_type, correct_answer, available_options, exam_type, parent_title")
                .eq("parent_title", qn)
                .in_("exam_type", ["mcq_exam", "mcq_quiz", "course_quiz"])
                .eq("is_active", True)
                .execute().data or []
            )
            mcqs.extend(rows)

    if not mcqs:
        all_quizzes = ["Module Quiz - 1", "Module Quiz - 2", "Module Quiz - 3",
                       "Module Quiz - 4", "Module Quiz - 5", "Module Quiz - 6", "Course Quiz"]
        for qn in all_quizzes:
            rows = (
                client.table("curriculum_assessments")
                .select("question_content, question_type, correct_answer, available_options, exam_type, parent_title")
                .eq("parent_title", qn)
                .in_("exam_type", ["mcq_exam", "mcq_quiz", "course_quiz"])
                .ilike("question_content", f"%{session_title.split('|')[0].strip().split(' ')[0]}%")
                .eq("is_active", True)
                .limit(10)
                .execute().data or []
            )
            mcqs.extend(rows)

    # Deduplicate MCQs
    seen_q: set[str] = set()
    unique_mcqs: list[dict] = []
    for m in mcqs:
        qc = m.get("question_content", "")
        if qc not in seen_q:
            seen_q.add(qc)
            unique_mcqs.append(m)

    # 3. Coding practice from curriculum_assessments (IDE_BASED_CODING)
    coding_practice: list[dict] = []
    if module_name:
        quiz_names = MODULE_QUIZ_MAP.get(module_name, [])
        for qn in quiz_names:
            rows = (
                client.table("curriculum_assessments")
                .select("question_content, question_type, correct_answer, exam_type, parent_title")
                .eq("parent_title", qn)
                .eq("exam_type", "coding_exam")
                .eq("is_active", True)
                .execute().data or []
            )
            coding_practice.extend(rows)

    if not coding_practice:
        for qn in ["Module Quiz - 1", "Module Quiz - 2", "Module Quiz - 3",
                    "Module Quiz - 4", "Module Quiz - 5", "Module Quiz - 6"]:
            rows = (
                client.table("curriculum_assessments")
                .select("question_content, question_type, correct_answer, exam_type, parent_title")
                .eq("parent_title", qn)
                .eq("exam_type", "coding_exam")
                .ilike("question_content", f"%{session_title.split('|')[0].strip().split(' ')[0]}%")
                .eq("is_active", True)
                .limit(5)
                .execute().data or []
            )
            coding_practice.extend(rows)

    # Deduplicate coding
    seen_c: set[str] = set()
    unique_coding: list[dict] = []
    for c in coding_practice:
        qc = c.get("question_content", "")[:100]
        if qc not in seen_c:
            seen_c.add(qc)
            unique_coding.append(c)

    return {
        "session_title": session_title,
        "reading": reading,
        "mcqs": unique_mcqs,
        "coding_practice": unique_coding,
        "total_reading": len(reading),
        "total_mcqs": len(unique_mcqs),
        "total_coding": len(unique_coding),
    }


@router.get("/module-assessments")
async def get_module_assessments(module_name: str = Query(...)):
    """Return all MCQ + coding assessment questions for a module."""
    client = get_supabase_client()

    quiz_names = MODULE_QUIZ_MAP.get(module_name, [])
    if not quiz_names:
        return {"module_name": module_name, "mcqs": [], "coding": [], "total": 0}

    mcqs: list[dict] = []
    coding: list[dict] = []

    for qn in quiz_names:
        rows = (
            client.table("curriculum_assessments")
            .select("question_content, question_type, correct_answer, available_options, exam_type, parent_title")
            .eq("parent_title", qn).eq("is_active", True)
            .execute().data or []
        )
        for r in rows:
            if r["exam_type"] == "coding_exam":
                coding.append(r)
            else:
                mcqs.append(r)

    return {
        "module_name": module_name,
        "mcqs": mcqs,
        "coding": coding,
        "total": len(mcqs) + len(coding),
    }
