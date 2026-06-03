#!/usr/bin/env python3
"""
Kanun Patrika - Nepal Supreme Court Nājir Semantic Search
FastAPI backend with Gemini API via direct HTTP (no heavy ML deps).
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from urllib.request import Request, urlopen
from urllib.error import URLError

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    WORK_DIR = Path(os.getcwd())
else:
    BASE_DIR = Path(__file__).parent
    WORK_DIR = BASE_DIR

try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PATH = WORK_DIR / "decisions.db"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set. Create .env file with your API key.")

app = FastAPI(title="Kanun Patrika", description="Nepal Supreme Court Nājir Search")


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def call_gemini(prompt: str) -> str | None:
    """Call Gemini API via stdlib urllib (no external HTTP deps needed)."""
    if not GEMINI_API_KEY:
        return None
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    decision_number: str
    decision_date: str
    bench: str
    judges: str
    mudda: str
    relevance: str = ""


QUERY_OPTIMIZATION_PROMPT = """You are a legal search expert for Nepal Supreme Court Nājir (नजिर) collections.

A user is describing a legal situation in natural Nepali. Your job is to extract the most effective search keywords and legal concepts from their query.

User's query:
"{user_query}"

Extract and return a JSON object with these fields:
- "search_keywords": Array of 3-8 most relevant Nepali legal keywords for searching (e.g., उत्तराधिकार, सम्पत्ति, अंशबण्डा, विवाह, मुद्दा, कानून, ऐन, etc.)
- "legal_concepts": Array of 2-4 broader legal concept categories (e.g., "पारिवारिक विवाद", "सम्पत्ति अधिकार", "आपराधिक मुद्दा")
- "case_context": A brief 1-2 sentence summary of what the user is looking for, in formal Nepali

IMPORTANT: Return ONLY valid JSON, no markdown, no explanation. Example format:
{{"search_keywords": ["उत्तराधिकार", "सम्पत्ति", "विवाह"], "legal_concepts": ["पारिवारिक विवाद"], "case_context": "बुबाको मृत्यु पछि सम्पत्ति विवाद सम्बन्धी मुद्दा"}}
"""

EXPLANATION_PROMPT = """You are a legal assistant helping users understand Nepal Supreme Court Nājir (नजिर) decisions.

The user asked:
"{user_query}"

Based on their query, we found these relevant Supreme Court decisions:

{results_text}

Your task:
1. Write a brief, clear explanation in Nepali (2-4 sentences) explaining what these decisions are about and why they are relevant to the user's query
2. Highlight the key legal principle from each decision
3. Be helpful and professional

Respond in JSON format:
{{
  "explanation": "Brief Nepali explanation of the results...",
  "key_points": ["Point 1 about decision...", "Point 2 about decision..."]
}}

IMPORTANT: Return ONLY valid JSON, no markdown.
"""


def search_decisions_fts(keywords: list[str], limit: int = 15) -> list[dict]:
    """Search decisions using FTS5 with multiple keywords."""
    with get_db() as conn:
        fts_query = " OR ".join(keywords)

        try:
            cursor = conn.execute("""
                SELECT
                    d.id, d.decision_number, d.decision_date, d.bench,
                    d.judges, d.mudda, d.char_count,
                    rank
                FROM decisions_fts fts
                JOIN decisions d ON d.id = fts.rowid
                WHERE decisions_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (fts_query, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "decision_number": row["decision_number"],
                    "decision_date": row["decision_date"],
                    "bench": row["bench"],
                    "judges": row["judges"],
                    "mudda": row["mudda"],
                    "char_count": row["char_count"],
                })
            return results

        except Exception as e:
            print(f"FTS search error: {e}")
            return search_decisions_fallback(keywords, limit)


def search_decisions_fallback(keywords: list[str], limit: int = 15) -> list[dict]:
    """Fallback: LIKE-based search when FTS fails."""
    with get_db() as conn:
        conditions = []
        params = []
        for kw in keywords[:5]:
            conditions.append("(mudda LIKE ? OR full_text LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        where = " OR ".join(conditions)
        params.append(limit)

        cursor = conn.execute(f"""
            SELECT id, decision_number, decision_date, bench, judges, mudda, char_count
            FROM decisions
            WHERE {where}
            LIMIT ?
        """, params)

        return [dict(row) for row in cursor.fetchall()]


def optimize_query_with_gemini(user_query: str) -> dict:
    """Use Gemini to extract search keywords from user query."""
    if not GEMINI_API_KEY:
        return {
            "search_keywords": user_query.split()[:5],
            "legal_concepts": [],
            "case_context": user_query,
        }

    prompt = QUERY_OPTIMIZATION_PROMPT.format(user_query=user_query)
    text = call_gemini(prompt)

    if not text:
        words = user_query.split()
        return {
            "search_keywords": words[:5],
            "legal_concepts": [],
            "case_context": user_query,
        }

    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        print(f"Gemini optimization parse error: {e}")
        words = user_query.split()
        return {
            "search_keywords": words[:5],
            "legal_concepts": [],
            "case_context": user_query,
        }


def explain_results_with_gemini(user_query: str, results: list[dict]) -> dict:
    """Use Gemini to explain search results to the user."""
    if not results:
        return {
            "explanation": "तपाईंको खोजी अनुसार कुनै निर्णय भेटिएन। कृपया फरक शब्दहरू प्रयोग गरेर फेरि खोज्नुहोस्।",
            "key_points": [],
        }

    if not GEMINI_API_KEY:
        return {
            "explanation": "यी निर्णयहरू तपाईंको खोजीसँग सम्बन्धित छन्।",
            "key_points": [r.get("mudda", "")[:100] for r in results[:3]],
        }

    results_text = ""
    for i, r in enumerate(results[:8], 1):
        results_text += f"""
Decision {i}:
- निर्णय नं: {r['decision_number']}
- मिति: {r['decision_date']}
- बेन्च: {r['bench']}
- मुद्दा: {r['mudda'][:200] if r['mudda'] else 'उपलब्ध छैन'}
"""

    prompt = EXPLANATION_PROMPT.format(
        user_query=user_query, results_text=results_text
    )
    text = call_gemini(prompt)

    if not text:
        return {
            "explanation": f"तपाईंको खोजीसँग {len(results)} वटा निर्णयहरू भेटिए।",
            "key_points": [r.get("mudda", "")[:100] for r in results[:3]],
        }

    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        print(f"Gemini explanation parse error: {e}")
        return {
            "explanation": f"तपाईंको खोजीसँग {len(results)} वटा निर्णयहरू भेटिए।",
            "key_points": [r.get("mudda", "")[:100] for r in results[:3]],
        }


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = BASE_DIR / "static" / "index.html"
    return FileResponse(str(index_path))


@app.post("/api/search")
async def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    optimized = optimize_query_with_gemini(request.query)

    keywords = optimized.get("search_keywords", [])
    if not keywords:
        keywords = request.query.split()[:5]

    results = search_decisions_fts(keywords, limit=12)

    explanation = explain_results_with_gemini(request.query, results)

    search_results = []
    for r in results:
        search_results.append(SearchResult(
            decision_number=r["decision_number"],
            decision_date=r["decision_date"],
            bench=r["bench"],
            judges=r["judges"],
            mudda=r["mudda"],
        ))

    return {
        "query": request.query,
        "optimized_query": optimized,
        "results": search_results,
        "explanation": explanation,
        "total_found": len(search_results),
    }


@app.get("/api/stats")
async def stats():
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM decisions")
        total = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(DISTINCT source_file) FROM decisions")
        files = cursor.fetchone()[0]

        cursor = conn.execute("""
            SELECT bench, COUNT(*) as cnt
            FROM decisions WHERE bench != ''
            GROUP BY bench ORDER BY cnt DESC
        """)
        benches = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]

    return {
        "total_decisions": total,
        "total_files": files,
        "bench_distribution": benches,
    }


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting Kanun Patrika on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
