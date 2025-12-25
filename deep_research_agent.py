"""
TMP AI Consulting – Stable Research Agent (Serper.dev)

"""

import os
import time
import json
import asyncio
import hashlib
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner

# --------------------------------------------------
# ENV
# --------------------------------------------------

load_dotenv(override=True)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not SERPER_API_KEY:
    raise RuntimeError("SERPER_API_KEY not found in environment")

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

@dataclass
class Config:
    MAX_SEARCH_RESULTS: int = 5
    TEXT_CHUNK_SIZE: int = 4000
    REPORT_CHUNK_SIZE: int = 18000
    CACHE_FILE: str = "research_cache.json"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    SEARCH_DELAY: float = 1.5

config = Config()

# --------------------------------------------------
# CACHE (FIXED)
# --------------------------------------------------

class PersistentCache:
    def __init__(self, file):
        self.file = file
        self.data = self._load()

    def _load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._save()

cache = PersistentCache(config.CACHE_FILE)

# --------------------------------------------------
# MODELS
# --------------------------------------------------

class SearchItem(BaseModel):
    query: str
    reason: str

class SearchPlan(BaseModel):
    searches: List[SearchItem]

class ResearchReport(BaseModel):
    title: str
    summary: str
    findings: List[str]
    detailed: str
    confidence: str

# --------------------------------------------------
# SERPER SEARCH
# --------------------------------------------------

def serper_search(query: str, num: int = 5):
    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": num,
        "hl": "en",
        "gl": "us"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)
    response.raise_for_status()

    data = response.json()

    results = []
    for item in data.get("organic", []):
        snippet = item.get("snippet")
        if snippet:
            results.append(snippet)

    return results

# --------------------------------------------------
# AGENTS
# --------------------------------------------------

planner = Agent(
    name="Planner",
    instructions="""
Developer: # Role and Objective
Design a comprehensive research plan focused on the user's specified topic, encompassing all major facets and avoiding superficial coverage. Begin with a concise, high-level checklist (3-7 bullets) outlining your major planning steps before generating the detailed search plan, ensuring clarity and completeness in your approach.

# Instructions
- Do not limit the plan to only high-level searches.
- Structure the search plan to collectively explore all core dimensions: background, mechanisms, variations, applications, limitations, and modern trends.
- Emphasize depth and breadth in search design, prioritizing diversity over redundancy.
- If the topic is broad, ensure the set of searches thoroughly spans the topic space.
- After generating the full plan, review each dimension to confirm that its span, depth, and variety are adequate; self-correct if superficial or uneven.

# FINAL OUTPUT FORMAT (STRICT — REQUIRED)

Return ONLY the following JSON structure:

{
  "searches": [
    {
      "query": "Exact Google-style search query string",
      "reason": "Why this search is necessary to fully cover the topic"
    }
  ]
}

Rules:
- Generate 12–15 searches when the topic is broad
- Each search must target a distinct dimension of the topic
- Use concrete, specific search phrasing
- Do not include any other fields
- Do not include explanations outside the JSON

""",
    output_type=SearchPlan,
    model=config.DEFAULT_MODEL
)

summarizer = Agent(
    name="Summarizer",
    instructions="""
# Role and Objective
Summarize content with depth while maintaining explanatory richness and context. Begin with a concise checklist (3-7 bullets) of what you will do; keep items conceptual, not implementation-level.
# Instructions
- Extract and synthesize:
- Key ideas along with their detailed explanations (not just isolated facts)
- Underlying causes, mechanisms, or reasoning when available
- Any conflicting viewpoints or limitations presented
- Critical context explaining the significance or relevance of the information
- Important details, even if they seem obvious, should be included
- Preserve explanations, mechanisms, reasoning, and context throughout the summary
- Do not aggressively compress the content; avoid reducing information to disconnected bullet points. Preserve narrative and explanatory flow where present.
- If information is missing or unclear in the source, explicitly note the gap in your summary.
- After producing the summary, validate that all required elements have been included and that context and explanations are preserved. If critical elements are missing, revisit and revise as necessary.
# Length Requirement
- Target summary length: 300–600 words, if the content supports it

""",
    model=config.DEFAULT_MODEL
)

writer = Agent(
    name="Writer",
    instructions="""
You are an expert generalist researcher.

Your task: produce a COMPLETE and exhaustive report on the provided topic.

Begin with a concise checklist (3-7 bullets) outlining your conceptual sub-tasks for full coverage of the topic before producing the actual report. This will ensure no key dimensions are overlooked.

**Before writing, infer the topic’s domain(s) and identify all major dimensions a well-informed reader would expect to see covered.**

**MANDATORY RULES:**
1. Do not stop at a surface-level explanation.
2. Do not optimize for brevity.
3. Do not assume the reader wants a summary.
4. Do not skip a dimension because it feels “obvious.”
5. **TARGET LENGTH: 9,000 - 10,000 WORDS.** You must aim for this length.
6. **FORMAT:** The output must be valid Markdown.
7. **CONTENT:** The output must be the *entire* exhaustive report, not a summary or an outline.

**GENERIC COVERAGE CHECK:**
For any topic, cover each of the following sections as distinct headers (unless the topic’s unique structure requires adaptation):
- Definition and Scope
- Origins or Background (if applicable)
- Core Components or Concepts
- How It Works / How It is Used
- Variations or Classifications
- Practical Examples or Applications
- Benefits and Strengths
- Limitations, Risks, or Drawbacks
- Common Misconceptions or Mistakes
- Evolution or Modern Developments
- Broader Impact (social, economic, cultural, scientific—as relevant)

If the topic does not fit perfectly into these sections or spans multiple domains, adapt and augment the section structure for full coverage. You may rename or add sections for clarity or completeness, but do not omit relevant content.

If information is incomplete or uncertain, clearly indicate these gaps and explain any assumptions. Where uncertainty is significant, summarize unanswered questions.

If applicable, provide references, citations, or links supporting factual claims, and include a concluding 'References' section.

**WRITING STANDARD:**
- Use clear section headers as above (Markdown H2: ## Section Name)
- Explain mechanisms, not just outcomes
- Expand each section until it is independently thorough
- If a knowledgeable reader would say "this is missing X," expand further

**Depth self-check:**
- Before finishing, ask: "If I were new to this topic and wanted mastery, would I need to ask follow-up questions?"
- If yes, continue expanding.

After drafting, review the report for completeness and explicitly validate that all relevant dimensions are thoroughly covered. If any are missing or insufficiently explored, expand as needed.

**Output Format:**
Present the report in Markdown with the following structure:
- A top-level heading with the report’s title (e.g., # [Topic Name] Report)
- Optional metadata at the top (e.g., Topic, Date, Domains)
- One section per coverage area above, each starting with ## Section Name
- If sources are used, close with a ## References section
- If information is missing or uncertain, note it in the relevant section and summarize in a final ## Unanswered Questions/Limitations section

**Example:**

# [Topic Name] Report

**Topic:** [Provided Topic]  
**Date:** [YYYY-MM-DD]  
**Domains:** [Inferred Domains]

## Definition and Scope
...

## Origins or Background
...

... (Other sections)

## References
1. [Source 1]
2. [Source 2]

## Unanswered Questions/Limitations
- [Question or limitation]

""",
    output_type=ResearchReport,
    model=config.DEFAULT_MODEL
)

# --------------------------------------------------
# CORE PIPELINE
# --------------------------------------------------

async def run_single_search(user_query: str, item: SearchItem):
    cache_key = hashlib.md5(f"{user_query}::{item.query}".encode()).hexdigest()

    cached = cache.get(cache_key)
    if cached:
        return cached["value"]

    snippets = serper_search(item.query, config.MAX_SEARCH_RESULTS)
    combined_text = "\n".join(snippets)[:config.TEXT_CHUNK_SIZE]

    summary = await Runner.run(summarizer, combined_text)

    cache.set(cache_key, summary.final_output)
    await asyncio.sleep(config.SEARCH_DELAY)

    return summary.final_output

async def run_all_searches(user_query: str, plan: SearchPlan):
    summaries = []
    for item in plan.searches:
        summaries.append(await run_single_search(user_query, item))
    return summaries

async def generate_report(user_query: str, summaries: List[str]):
    combined = "\n\n".join(summaries)[:config.REPORT_CHUNK_SIZE]

    writer_input = f"""
TOPIC:
{user_query}

SOURCE MATERIAL:
{combined}
"""

    result = await Runner.run(writer, writer_input)
    return result.final_output


# --------------------------------------------------
# PUBLIC ENTRYPOINT (USE THIS)
# --------------------------------------------------

async def run_deep_research(user_query: str):
    start = time.time()

    plan_result = await Runner.run(planner, user_query)
    plan = plan_result.final_output

    summaries = await run_all_searches(user_query, plan)

    if len(summaries) < 3:
        raise RuntimeError("Not enough relevant data found")

    report = await generate_report(user_query, summaries)

    return {
        "status": "success",
        "plan": plan.model_dump(),
        "report": report.model_dump(),
        "duration": round(time.time() - start, 2)
    }
