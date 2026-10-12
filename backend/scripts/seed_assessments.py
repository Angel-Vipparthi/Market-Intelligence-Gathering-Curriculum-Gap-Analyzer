"""
Seed curriculum assessments from react_question_details_json.json
into both curriculum_assessments (structured) and curriculum_documents (for gap agent search).
"""

import json
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.supabase import get_supabase_client

EXAM_TYPE_MAP = {
    "MCQ Exam": "mcq_exam",
    "MCQ Quiz": "mcq_quiz",
    "Course Quiz": "course_quiz",
    "Coding Exam": "coding_exam",
}

def load_data():
    path = os.path.join(os.path.dirname(__file__), "react_question_details_json.json")
    with open(path) as f:
        return json.load(f)

def seed():
    client = get_supabase_client()
    data = load_data()

    assessment_rows = []
    doc_rows = []
    stats = {"units": 0, "questions": 0, "docs": 0, "skipped": 0}

    for unit in data:
        unit_id = unit["unit_id"]
        content_data = unit.get("content_data", {})
        parent_title = content_data.get("title", "")
        parent_desc = content_data.get("description", "")

        stats["units"] += 1

        unit_questions_text = []

        for exam in content_data.get("exam_details", []):
            exam_title = exam.get("title", "")
            exam_type = EXAM_TYPE_MAP.get(exam_title, "mcq_exam")
            total_max_score = exam.get("total_max_score")

            for q in exam.get("question_details", []):
                question_id = q.get("question_id", str(uuid4()))
                question_content = q.get("question_content") or q.get("content", "")

                if not question_content:
                    stats["skipped"] += 1
                    continue

                options = q.get("available_options", [])
                correct = q.get("correct_answer", "")

                assessment_rows.append({
                    "unit_id": unit_id,
                    "exam_title": exam_title,
                    "exam_type": exam_type,
                    "question_id": question_id,
                    "question_type": q.get("question_type", "MULTIPLE_CHOICE"),
                    "question_content": question_content,
                    "correct_answer": correct if isinstance(correct, str) else json.dumps(correct),
                    "available_options": options,
                    "parent_title": parent_title,
                    "parent_description": parent_desc,
                    "total_max_score": int(float(total_max_score)) if total_max_score is not None else None,
                })

                options_text = " | ".join(o.get("content", "") for o in options)
                unit_questions_text.append(
                    f"[{exam_type}] Q: {question_content} Options: {options_text}"
                )
                stats["questions"] += 1

        if unit_questions_text:
            doc_content = f"Assessment: {parent_title}\n" + "\n".join(unit_questions_text)
            doc_rows.append({
                "document_type": "assessment",
                "title": f"Assessment - {parent_title} ({unit_id[:8]})",
                "content": doc_content[:10000],
                "course_name": "React",
                "metadata": {"unit_id": unit_id, "source": "question_details_json"},
            })
            stats["docs"] += 1

    # Insert assessments in batches
    print(f"Inserting {len(assessment_rows)} assessment rows...")
    batch_size = 50
    for i in range(0, len(assessment_rows), batch_size):
        batch = assessment_rows[i:i + batch_size]
        try:
            client.table("curriculum_assessments").upsert(
                batch, on_conflict="unit_id,question_id"
            ).execute()
            print(f"  Batch {i // batch_size + 1}: {len(batch)} rows")
        except Exception as e:
            print(f"  Batch {i // batch_size + 1} failed: {e}")

    # Insert documents (skip duplicates by title)
    print(f"\nInserting {len(doc_rows)} curriculum_documents rows...")
    for doc in doc_rows:
        try:
            client.table("curriculum_documents").upsert(
                doc, on_conflict="title"
            ).execute()
        except Exception as e:
            print(f"  Doc '{doc['title'][:40]}' failed: {e}")

    print(f"\nDone!")
    print(f"  Units processed: {stats['units']}")
    print(f"  Questions inserted: {stats['questions']}")
    print(f"  Documents created: {stats['docs']}")
    print(f"  Skipped (no content): {stats['skipped']}")

if __name__ == "__main__":
    seed()
