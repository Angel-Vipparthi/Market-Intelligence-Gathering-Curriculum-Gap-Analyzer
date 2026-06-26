"""
Seed Knowledge Base with original Module → Session hierarchy from curriculum_documents.
Maps quizzes/practices to sessions by matching session_name.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db.supabase import get_supabase_client


MODULE_ORDER = [
    "Introduction to React JS and States",
    "Introduction to State Hook",
    "Effect Hook and Rules of Hooks",
    "Routing using React Router",
    "Authentication & Authorization",
    "React Context",
]

MODULE_SESSIONS = {
    "Introduction to React JS and States": [
        "Introduction to React JS",
        "Components and Props",
        "Lists & Keys",
        "State & Events",
        "Common Mistakes",
    ],
    "Introduction to State Hook": [
        "Conditional Rendering",
        "State Hook | Part 2",
        "State Hook | Part 3",
        "On Demand Session",
        "Debugging using Developer tools",
        "On Demand Session - 2",
    ],
    "Effect Hook and Rules of Hooks": [
        "Effect Hook and Rules of Hooks",
        "Effect Hooks - 2",
        "Making API Call with Hooks",
        "Schedulers with Hooks",
    ],
    "Routing using React Router": [
        "React Under the Hood",
        "Routing using React Router",
        "Routing using react-router | Part 2",
        "Common Mistakes | Part 2",
        "Authentication & Authorization",
    ],
    "Authentication & Authorization": [
        "Authentication & Authorization | Part 2",
        "Authentication & Authorization | Part 3",
        "Common Mistakes | Part 3",
        "Authentication & Authorization | Part 4",
        "Sorting Products",
    ],
    "React Context": [
        "Third-Party Packages",
        "React Context",
        "React Context | Part 2",
        "React Context | Part 3",
    ],
}

MODULE_LEVELS = {
    "Introduction to React JS and States": 1,
    "Introduction to State Hook": 2,
    "Effect Hook and Rules of Hooks": 3,
    "Routing using React Router": 4,
    "Authentication & Authorization": 5,
    "React Context": 5,
}


def seed():
    client = get_supabase_client()

    # Clear existing KB data
    print("Clearing existing KB data...")
    client.table("kb_sessions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    client.table("kb_modules").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    client.table("kb_courses").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    # Fetch all curriculum docs for content type and tools mapping
    docs = client.table("curriculum_documents").select(
        "document_type, title, session_name, tools"
    ).execute().data or []

    # Build session → content type mapping
    session_content = {}  # {session_name: set of content_types}
    session_tools = {}    # {session_name: list of tools}

    for d in docs:
        dt = d.get("document_type", "")
        title = d.get("title", "")
        sname = d.get("session_name") or title

        if dt == "session":
            session_content.setdefault(title, set()).add("reading")
            session_tools[title] = d.get("tools") or []
        elif dt == "quiz":
            session_content.setdefault(sname, set()).add("quiz")
        elif dt == "coding_challenge":
            session_content.setdefault(sname, set()).add("coding")

    # Create course
    print("Creating course: React (NIAT)...")
    course = client.table("kb_courses").upsert(
        {"product_name": "NIAT", "course_name": "React", "description": "Full-stack React curriculum covering fundamentals to advanced patterns"},
        on_conflict="product_name,course_name",
    ).execute()
    course_id = course.data[0]["id"]
    print(f"  Course ID: {course_id}")

    # Create modules and sessions
    for i, mod_name in enumerate(MODULE_ORDER):
        sessions = MODULE_SESSIONS.get(mod_name, [])
        if not sessions:
            print(f"\n[{i+1}] {mod_name} — no sessions, skipping")
            continue

        print(f"\n[{i+1}/{len(MODULE_ORDER)}] {mod_name} ({len(sessions)} sessions)")

        mod = client.table("kb_modules").upsert(
            {
                "course_id": course_id,
                "module_name": mod_name,
                "sort_order": i,
            },
            on_conflict="course_id,module_name",
        ).execute()
        module_id = mod.data[0]["id"]

        base_level = MODULE_LEVELS.get(mod_name, 3)

        for j, stitle in enumerate(sessions):
            stitle = stitle.strip()
            ct = sorted(session_content.get(stitle, {"reading"}))
            tools = session_tools.get(stitle, [])
            skills = [t.lower() for t in tools]

            # Prerequisites: previous session in same module
            prereqs = [sessions[j - 1]] if j > 0 else []

            client.table("kb_sessions").upsert(
                {
                    "module_id": module_id,
                    "title": stitle,
                    "content_types": ct,
                    "level": base_level,
                    "skills": skills[:15],
                    "prerequisites": prereqs,
                    "sort_order": j,
                },
                on_conflict="module_id,title",
            ).execute()
            ct_str = ", ".join(ct)
            print(f"  + {stitle} [{ct_str}] L{base_level} ({len(skills)} skills)")

    # Projects module
    project_docs = [d for d in docs if d.get("document_type") == "project"]
    if project_docs:
        print(f"\n[Projects] {len(project_docs)} projects")
        mod = client.table("kb_modules").upsert(
            {"course_id": course_id, "module_name": "Projects", "sort_order": len(MODULE_ORDER)},
            on_conflict="course_id,module_name",
        ).execute()
        proj_mod_id = mod.data[0]["id"]

        for k, pd in enumerate(project_docs):
            ptitle = pd.get("title", "")
            ptools = pd.get("tools") or []
            client.table("kb_sessions").upsert(
                {
                    "module_id": proj_mod_id,
                    "title": ptitle,
                    "content_types": ["coding"],
                    "level": 4,
                    "skills": [t.lower() for t in ptools][:10],
                    "prerequisites": [],
                    "sort_order": k,
                },
                on_conflict="module_id,title",
            ).execute()
            print(f"  + {ptitle}")

    print("\nDone!")


if __name__ == "__main__":
    seed()
