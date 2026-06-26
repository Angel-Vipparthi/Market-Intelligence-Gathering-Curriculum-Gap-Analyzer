"""
Seed curriculum from Google Sheets into Supabase.

Reads live from sheet — change sheet, re-run script, DB updates.
No Google API key needed (sheet must be publicly accessible).

Usage:
    cd backend
    python3 scripts/seed_curriculum.py

Approach: deletes previously seeded data then inserts fresh.
Safe to re-run any number of times.
"""
import csv
import io
import json
import sys
import os
from urllib.parse import quote, urlparse

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SPREADSHEET_ID = "1pfCnsHpJ4hX-xbW2ofvyAbUzDaerNjb53V2PXyiz1HI"

SHEET_TABS = {
    "urls": "URLs",
    "course_outline": "React Course Outline",
    "projects": "Projects Used",
    "tools": "Tools and Versions",
    "practice": "Practice Content",
    "quiz": "Quiz Content",
    "gaps": "Gap Analysis Output",
}

SEED_MARKER = "google_sheet_seed"


def fetch_sheet_csv(tab_name: str) -> list[dict]:
    """Fetch a single sheet tab as list of dicts (header row = keys)."""
    encoded = quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
    print(f"  Fetching: {tab_name}...")
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = []
    for row in reader:
        cleaned = {k.strip(): v.strip() for k, v in row.items() if k and k.strip()}
        if any(v for v in cleaned.values()):
            rows.append(cleaned)
    print(f"    Got {len(rows)} rows")
    return rows


def clear_seeded_data(db):
    """Remove previously seeded data before fresh insert."""
    try:
        db.table("url_registry").delete().eq("added_by", SEED_MARKER).execute()
    except Exception:
        pass
    try:
        db.table("curriculum_documents").delete().like("metadata->>seeded_by", SEED_MARKER).execute()
    except Exception:
        pass
    try:
        db.table("curriculum_gaps").delete().like("evidence_source", SEED_MARKER).execute()
    except Exception:
        pass
    print("  Cleared previous seed data\n")


def seed_urls(db):
    """Seed url_registry from URLs tab."""
    rows = fetch_sheet_csv(SHEET_TABS["urls"])
    count = 0
    current_source_type = ""

    for row in rows:
        source_type = row.get("Source Type", "")
        url = row.get("URLs", "") or row.get("URL", "")
        if source_type:
            current_source_type = source_type
        if not url or not url.startswith("http"):
            continue

        domain = urlparse(url).netloc.lower()

        tier = "unknown"
        if any(d in domain for d in ["react.dev", "vite.dev", "vitejs.dev", "redux-toolkit.js.org", "reactrouter.com"]):
            tier = "official_docs"
        elif "npmjs.com" in domain:
            tier = "tech_publication"
        elif any(d in domain for d in ["github.com", "blog"]):
            tier = "major_blog"

        category = "frontend"
        if "vite" in url.lower():
            category = "build_tools"
        elif "redux" in url.lower():
            category = "state_management"
        elif "router" in url.lower():
            category = "routing"
        elif "testing" in url.lower() or "jest" in url.lower():
            category = "testing"

        try:
            db.table("url_registry").insert({
                "url": url,
                "domain": domain,
                "source_name": current_source_type,
                "credibility_tier": tier,
                "category": category,
                "is_active": True,
                "added_by": SEED_MARKER,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("url_registry").update({
                    "source_name": current_source_type,
                    "credibility_tier": tier,
                    "category": category,
                    "is_active": True,
                    "added_by": SEED_MARKER,
                }).eq("url", url).execute()
                count += 1
            else:
                print(f"    WARN: {url}: {e}")

    print(f"  -> URLs: {count} seeded")
    return count


def seed_course_outline(db):
    """Seed sessions from React Course Outline tab."""
    rows = fetch_sheet_csv(SHEET_TABS["course_outline"])
    count = 0
    current_course = ""
    current_module = ""

    tool_keywords = {
        "React": ["react", "jsx", "hooks", "useState", "useEffect", "useContext", "useReducer", "useMemo", "useCallback", "useRef"],
        "Vite": ["vite"],
        "React Router": ["react router", "BrowserRouter", "useNavigate", "useParams", "react-router"],
        "Redux Toolkit": ["redux", "createSlice", "configureStore", "RTK"],
        "js-cookie": ["js-cookie", "Cookies.set", "Cookies.remove"],
        "React Icons": ["react-icons", "react icons"],
        "Recharts": ["recharts"],
        "React Slick": ["react-slick", "react slick"],
        "React Chrono": ["react-chrono", "react chrono"],
        "UUID": ["uuid", "uuidv4"],
        "ESLint": ["eslint"],
        "Prettier": ["prettier"],
        "Styled Components": ["styled-components", "styled components"],
        "Emotion": ["emotion"],
        "Framer Motion": ["framer-motion", "framer motion"],
    }

    for row in rows:
        course = row.get("Course Name", "")
        module = row.get("Module Name", "")
        session_no = row.get("Session No.", "") or row.get("Session No", "")
        session_name = row.get("Session Name", "")
        key_takeaways = row.get("Key Takeaways", "")
        outline = row.get("Outline", "")

        if course:
            current_course = course
        if module:
            current_module = module
        if not session_name:
            continue

        content = key_takeaways
        if outline:
            content = f"{key_takeaways}\n\n{outline}"

        tools = []
        content_lower = content.lower()
        for tool, keywords in tool_keywords.items():
            if any(kw.lower() in content_lower for kw in keywords):
                tools.append(tool)

        try:
            db.table("curriculum_documents").insert({
                "document_type": "session",
                "title": session_name,
                "content": content,
                "course_name": current_course,
                "module_name": current_module,
                "session_name": session_name,
                "tools": tools,
                "metadata": {"session_no": session_no, "seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_documents").update({
                    "content": content,
                    "course_name": current_course,
                    "module_name": current_module,
                    "tools": tools,
                    "metadata": {"session_no": session_no, "seeded_by": SEED_MARKER},
                }).eq("title", session_name).execute()
                count += 1
            else:
                print(f"    WARN session '{session_name}': {e}")

    if current_course:
        try:
            db.table("curriculum_documents").insert({
                "document_type": "course",
                "title": current_course,
                "content": f"{current_course} — {count} sessions covering React fundamentals through advanced topics.",
                "course_name": current_course,
                "tools": ["React", "Vite", "React Router"],
                "metadata": {"seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
        except Exception:
            db.table("curriculum_documents").update({
                "content": f"{current_course} — {count} sessions covering React fundamentals through advanced topics.",
                "metadata": {"seeded_by": SEED_MARKER},
            }).eq("title", current_course).execute()

    print(f"  -> Sessions: {count} seeded")
    return count


def seed_projects(db):
    """Seed projects from Projects Used tab."""
    rows = fetch_sheet_csv(SHEET_TABS["projects"])
    count = 0

    for row in rows:
        name = row.get("Project Name", "")
        if not name:
            continue

        session_mapping = row.get("Session Mapping", "")
        concepts = row.get("Concepts Practiced", "")
        tools_str = row.get("Tools Used", "")
        remarks = row.get("Remarks", "")

        tools = [t.strip() for t in tools_str.split(",") if t.strip()] if tools_str else []
        content_parts = [f"Project: {name}"]
        if session_mapping:
            content_parts.append(f"Session Mapping: {session_mapping}")
        if concepts:
            content_parts.append(f"Concepts: {concepts}")
        if tools_str:
            content_parts.append(f"Tools: {tools_str}")
        if remarks:
            content_parts.append(f"Remarks: {remarks}")
        content = "\n".join(content_parts)

        try:
            db.table("curriculum_documents").insert({
                "document_type": "project",
                "title": name,
                "content": content,
                "course_name": "React",
                "tools": tools,
                "metadata": {"session_mapping": session_mapping, "remarks": remarks, "seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_documents").update({
                    "content": content,
                    "tools": tools,
                    "metadata": {"session_mapping": session_mapping, "remarks": remarks, "seeded_by": SEED_MARKER},
                }).eq("title", name).execute()
                count += 1
            else:
                print(f"    WARN project '{name}': {e}")

    print(f"  -> Projects: {count} seeded")
    return count


def seed_tools(db):
    """Seed tools from Tools and Versions tab."""
    rows = fetch_sheet_csv(SHEET_TABS["tools"])
    count = 0

    for row in rows:
        tool = row.get("Tool / Library", "") or row.get("Tool/Library", "")
        if not tool:
            continue

        used = row.get("Used in Curriculum?", "").strip().lower()
        version = row.get("Version Used", "")
        where_used = row.get("Where Used", "")
        remarks = row.get("Remarks", "")

        title = f"{tool} v{version}" if version else tool
        content_parts = [f"Tool: {tool}"]
        if version:
            content_parts.append(f"Version: {version}")
        if used:
            content_parts.append(f"Used in curriculum: {used}")
        if where_used:
            content_parts.append(f"Where used: {where_used}")
        if remarks:
            content_parts.append(remarks)
        content = "\n".join(content_parts)

        try:
            db.table("curriculum_documents").insert({
                "document_type": "tool_registry",
                "title": title,
                "content": content,
                "course_name": "React",
                "tools": [tool],
                "versions": {tool: version} if version else {},
                "metadata": {"used_in_curriculum": used in ("yes", "y", "true"), "where_used": where_used, "seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_documents").update({
                    "content": content,
                    "versions": {tool: version} if version else {},
                    "metadata": {"used_in_curriculum": used in ("yes", "y", "true"), "where_used": where_used, "seeded_by": SEED_MARKER},
                }).eq("title", title).execute()
                count += 1
            else:
                print(f"    WARN tool '{tool}': {e}")

    print(f"  -> Tools: {count} seeded")
    return count


def seed_practice(db):
    """Seed practice content from Practice Content tab."""
    rows = fetch_sheet_csv(SHEET_TABS["practice"])
    count = 0

    for row in rows:
        session_name = row.get("Session Name", "")
        if not session_name:
            continue

        unit_id = row.get("Unit ID", "")
        cheatsheet = row.get("Cheatsheet/Coding practice", "") or row.get("Cheatsheet/ Coding practice", "") or row.get("Cheatsheet / Coding practice", "")

        content = f"Practice content for session: {session_name}"
        if cheatsheet:
            content += f"\n{cheatsheet}"

        title = f"Practice: {session_name}"

        try:
            db.table("curriculum_documents").insert({
                "document_type": "coding_challenge",
                "title": title,
                "content": content,
                "course_name": "React",
                "session_name": session_name,
                "metadata": {"unit_id": unit_id, "seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_documents").update({
                    "content": content,
                    "metadata": {"unit_id": unit_id, "seeded_by": SEED_MARKER},
                }).eq("title", title).execute()
                count += 1
            else:
                print(f"    WARN practice '{session_name}': {e}")

    print(f"  -> Practice: {count} seeded")
    return count


def seed_quizzes(db):
    """Seed quiz content from Quiz Content tab."""
    rows = fetch_sheet_csv(SHEET_TABS["quiz"])
    count = 0

    for row in rows:
        session_name = row.get("Session Name", "")
        if not session_name:
            continue

        unit_id = row.get("Unit ID", "")
        mcq = row.get("MCQ practice", "") or row.get("MCQ Practice", "")

        content = f"Quiz for session: {session_name}"
        if mcq:
            content += f"\n{mcq}"

        title = f"Quiz: {session_name}"

        try:
            db.table("curriculum_documents").insert({
                "document_type": "quiz",
                "title": title,
                "content": content,
                "course_name": "React",
                "session_name": session_name,
                "metadata": {"unit_id": unit_id, "seeded_by": SEED_MARKER},
                "is_active": True,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_documents").update({
                    "content": content,
                    "metadata": {"unit_id": unit_id, "seeded_by": SEED_MARKER},
                }).eq("title", title).execute()
                count += 1
            else:
                print(f"    WARN quiz '{session_name}': {e}")

    print(f"  -> Quizzes: {count} seeded")
    return count


def seed_existing_gaps(db):
    """Seed existing gap analysis from Gap Analysis Output tab."""
    rows = fetch_sheet_csv(SHEET_TABS["gaps"])
    count = 0

    for row in rows:
        area = row.get("Area", "")
        gap_statement = row.get("Gap", "")
        if not area or not gap_statement:
            continue

        evidence = row.get("Current Curriculum Evidence", "")
        market_standard = row.get("Market Standard", "")
        severity_raw = row.get("Severity", "medium").strip().lower()
        recommendation = row.get("Recommendation", "")
        confidence_raw = row.get("Confidence", "medium").strip().lower()
        status = row.get("Status", "pending_review").strip()

        severity = severity_raw if severity_raw in ("critical", "high", "medium", "low") else "medium"
        confidence_map = {"high": 0.85, "medium": 0.6, "low": 0.3}
        confidence = confidence_map.get(confidence_raw, 0.6)

        decision = "pending_review"
        if status.lower() in ("need to review", "needs review"):
            decision = "needs_review"
        elif status.lower() == "approved":
            decision = "approved"

        try:
            db.table("curriculum_gaps").insert({
                "gap_type": "design_gap",
                "market_signal": market_standard,
                "curriculum_evidence": evidence,
                "gap_statement": gap_statement,
                "what_to_act": recommendation,
                "why_to_act": f"Market standard: {market_standard}",
                "severity": severity,
                "impacted_content_area": area,
                "confidence": confidence,
                "decision_status": decision,
                "evidence_source": SEED_MARKER,
            }).execute()
            count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                db.table("curriculum_gaps").update({
                    "market_signal": market_standard,
                    "curriculum_evidence": evidence,
                    "what_to_act": recommendation,
                    "why_to_act": f"Market standard: {market_standard}",
                    "severity": severity,
                    "impacted_content_area": area,
                    "confidence": confidence,
                    "decision_status": decision,
                    "evidence_source": SEED_MARKER,
                }).eq("gap_statement", gap_statement).execute()
                count += 1
            else:
                print(f"    WARN gap '{gap_statement[:50]}': {e}")

    print(f"  -> Gaps: {count} seeded")
    return count


def seed():
    from app.db.supabase import get_supabase_client
    db = get_supabase_client()

    print(f"Google Sheet: {SPREADSHEET_ID}")
    print(f"{'=' * 60}\n")

    clear_seeded_data(db)

    total = 0
    total += seed_urls(db)
    total += seed_course_outline(db)
    total += seed_projects(db)
    total += seed_tools(db)
    total += seed_practice(db)
    total += seed_quizzes(db)
    total += seed_existing_gaps(db)

    print(f"\n{'=' * 60}")
    print(f"Total: {total} records seeded from Google Sheets.")
    print("Re-run anytime to sync latest sheet changes.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    seed()
