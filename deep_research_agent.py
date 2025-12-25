"""
TMP AI Consulting – Deep Research Agent
Production-ready with optimized prompts and error handling
Now with 15 comprehensive searches for deeper insights
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from agents import Agent, Runner
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
import asyncio
import time
import logging
import json
import hashlib
import random
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# ------------------------------
# Configuration
# ------------------------------

@dataclass
class Config:
    MAX_SEARCH_RESULTS: int = 5
    MAX_CONCURRENT_SEARCHES: int = 2  # Reduced to avoid DDG rate limits
    MAX_RETRIES: int = 3
    DEFAULT_MODEL: str = "gpt-4o-mini"
    TEXT_CHUNK_SIZE: int = 4000
    REPORT_CHUNK_SIZE: int = 20000  # Increased for more content
    CACHE_FILE: str = "research_cache.json"
    BATCH_DELAY: float = 2.5  # Delay between search batches

config = Config()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------------
# Cost & Cache Helpers
# ------------------------------

class CostTracker:
    def __init__(self):
        self.calls = 0
        self.estimated = 0.0

    def add(self, cost=0):
        self.calls += 1
        self.estimated += cost

    def summary(self):
        return {
            "api_calls": self.calls,
            "cost_usd": round(self.estimated, 4)
        }
    
    def reset(self):
        self.calls = 0
        self.estimated = 0.0

costs = CostTracker()

class PersistentCache:
    def __init__(self, cache_file=None):
        self.cache_file = cache_file or config.CACHE_FILE
        self.data = self._load()

    def _load(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get(self, key):
        hashed = hashlib.md5(key.encode()).hexdigest()
        return self.data.get(hashed)

    def set(self, key, value):
        hashed = hashlib.md5(key.encode()).hexdigest()
        self.data[hashed] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._save()

cache = PersistentCache()

# ------------------------------
# Output Structures
# ------------------------------

class SearchItem(BaseModel):
    reason: str
    query: str

class SearchPlan(BaseModel):
    searches: List[SearchItem]

class ResearchReport(BaseModel):
    title: str
    summary: str
    findings: List[str]
    detailed: str
    confidence: str

# ------------------------------
# Enhanced Agent Prompts (15 Searches)
# ------------------------------

PLANNER_PROMPT = """You are an expert Research Strategist. Your job is to generate 15 search queries that will help comprehensively answer the user's specific question.
**CRITICAL INSTRUCTION:**
Read the user's query carefully. What are they ACTUALLY asking? Generate 15 searches that would help YOU answer their exact question if you were researching it yourself.
**RULES:**
1. **Match the query type**: 
   - Comparison query? → Search for specific differences, not general info
   - "What is X" query? → Search for definitions, explanations, examples
   - "How to do X" query? → Search for tutorials, guides, step-by-step
   - Tool/product query? → Search for specific tools, reviews, comparisons
   - Creative/fictional query? → Search for folklore, fiction, fan analysis
   
2. **Be specific**: Use concrete terms (names, products, places, concepts), not vague keywords
3. **Stay focused**: All 15 searches should explore different angles of the SAME core question
4. **Adapt to domain**:
   - Technical topic? → Use technical terms, version numbers, frameworks
   - Creative topic? → Use cultural sources, mythology, fiction, fan communities
   - Regional topic? → Specify regions, compare specific aspects
   - Abstract topic? → Use academic, theoretical, psychological sources
5. **No forced structure**: Don't include "history" if they didn't ask for history. Don't include "future trends" if they asked about current tools.
**YOUR TASK:**
Generate exactly 15 searches. For each search, write:
- "reason": A clear explanation of what information this search will uncover (one sentence)
- "query": A 5-12 word search query optimized for search engines
**OUTPUT (strict JSON):**
{
  "searches": [
    {"reason": "...", "query": "..."},
    ...15 total...
  ]
}
**USER QUERY:**"""

SUMMARIZER_PROMPT = """You are a Senior Research Analyst specializing in information distillation.
**YOUR ROLE:**
Extract and synthesize the most valuable insights from raw search results.
**TASK:**
Create a precise, fact-dense summary that:
- Captures 3-5 KEY FACTS or DATA POINTS (prioritize numbers, dates, named entities)
- Identifies the MAIN ARGUMENT or FINDING
- Notes any CONTRADICTIONS or LIMITATIONS in the source
- Maintains ATTRIBUTION (e.g., "According to [source]...")
**QUALITY CRITERIA:**
✓ Information density: Every sentence adds value
✓ Specificity: Include concrete examples, statistics, expert names
✓ Objectivity: Distinguish facts from opinions
✓ Relevance: Filter out tangential information
**CONSTRAINTS:**
- Length: 150-200 words MAXIMUM
- No hallucination: If data is unclear, state "unclear" rather than guessing
- No marketing fluff or generic statements
- Use active voice and precise language
**BAD EXAMPLE:**
"The article discusses various interesting aspects of AI. Many experts believe it's important. There are several challenges and opportunities."
**GOOD EXAMPLE:**
"According to Stanford's 2024 AI Index, enterprise AI adoption reached 72% (up from 55% in 2023). Key drivers: cost reduction (43% of implementations) and productivity gains averaging 35%. However, MIT study (n=500 firms) found 68% failed to achieve ROI targets within 18 months, primarily due to data infrastructure gaps and change management issues. Gartner predicts consolidation around 3-4 dominant platforms by 2026."
**Now summarize this content:**"""

WRITER_PROMPT = """You are a Distinguished Research Director.
**YOUR ROLE:**
Synthesize 15 research summaries into a comprehensive, publication-quality report.
**CORE INSTRUCTION:**
Read the provided research summaries first. Then, design a report structure that **naturally fits the content**. 
Do not force a specific template (like "Technical Foundation" or "Business Impact") if it doesn't match the topic.
- If the topic is mythology → Structure it around themes, symbolism, and cultural impact.
- If the topic is software → Structure it around features, architecture, and performance.
- If the topic is history → Structure it chronologically or by key events.
**REPORT REQUIREMENTS:**
**1. TITLE**
- Clear, descriptive, and engaging (10-15 words)
**2. EXECUTIVE SUMMARY (180-220 words)**
- A high-level synthesis of the most important insights
- Must stand alone as a complete overview
- Adapt tone to the subject matter
**3. KEY FINDINGS (exactly 8 bullets)**
- The 8 most significant facts, themes, or insights discovered
- Format: "[Core Insight] → [Context/Implication]"
**4. DETAILED ANALYSIS (1200-1500 words)**
- **Create your own subsection headers (###)** based on the themes that emerge from the research.
- Organize the content logically for the reader.
- Aim for 4-6 distinct sections.
- Synthesize sources (don't just list them).
- Use markdown for readability.
**5. CONFIDENCE ASSESSMENT**
- Assess the reliability and consensus of the gathered information (High/Medium/Low) with a brief justification.
**OUTPUT FORMAT (strict JSON):**
{
  "title": "string",
  "summary": "string",
  "findings": ["string", "string", "string", "string", "string", "string", "string", "string"],
  "detailed": "markdown string (1200-1500 words with custom ### headers)",
  "confidence": "string"
}
**Now synthesize the research summaries below:**"""


# ------------------------------
# Agents with Enhanced Prompts
# ------------------------------

planner = Agent(
    name="ResearchPlanner",
    instructions=PLANNER_PROMPT,
    output_type=SearchPlan,
    model=config.DEFAULT_MODEL
)

summarizer = Agent(
    name="Summarizer",
    instructions=SUMMARIZER_PROMPT,
    model=config.DEFAULT_MODEL
)

writer = Agent(
    name="ReportWriter",
    instructions=WRITER_PROMPT,
    output_type=ResearchReport,
    model=config.DEFAULT_MODEL
)

# ------------------------------
# Search Utility (DuckDuckGo)
# ------------------------------

def ddg_search(query: str, max_results=None):
    max_results = max_results or config.MAX_SEARCH_RESULTS
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        logger.info(f"Search successful: {query} ({len(results)} results)")
        return results
    except DuckDuckGoSearchException as e:
        logger.error(f"DuckDuckGo error for '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected search error for '{query}': {e}")
        return []

# ------------------------------
# Pipeline Steps
# ------------------------------

async def generate_plan(query: str) -> SearchPlan:
    logger.info(f"Generating research plan for: {query}")
    result = await Runner.run(planner, f"Research Query: {query}")
    costs.add(0.002)
    return result.final_output

async def run_single_search(item: SearchItem, progress_callback=None):
    """Run a single search with retry logic and caching"""
    
    cached = cache.get(item.query)
    if cached and isinstance(cached, dict):
        logger.info(f"Cache hit for: {item.query}")
        if progress_callback:
            progress_callback(f"✓ Using cached results for: {item.query}")
        return cached["value"]

    for attempt in range(config.MAX_RETRIES):
        try:
            if progress_callback:
                progress_callback(f"🔍 Searching: {item.query} (attempt {attempt + 1})")
            
            raw_results = ddg_search(item.query)
            
            if not raw_results:
                logger.warning(f"No results for: {item.query}")
                return f"⚠️ No results found for: {item.query}"

            combined = "\n".join(
                r.get("body", "") or r.get("snippet", "") or "" 
                for r in raw_results
            )

            if progress_callback:
                progress_callback(f"📝 Summarizing results for: {item.query}")

            summary = await Runner.run(summarizer, combined[:config.TEXT_CHUNK_SIZE])
            costs.add(0.002)

            clean = summary.final_output.strip()
            cache.set(item.query, clean)

            if progress_callback:
                progress_callback(f"✅ Completed: {item.query}")

            return clean

        except Exception as e:
            wait_time = (attempt + 1) * 2 + random.uniform(0, 1)  # Add jitter
            logger.warning(f"Attempt {attempt + 1} failed for '{item.query}': {e}")
            
            if attempt < config.MAX_RETRIES - 1:
                if progress_callback:
                    progress_callback(f"⏳ Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All retries exhausted for: {item.query}")
                return f"❌ Search failed after {config.MAX_RETRIES} attempts: {item.query}"

async def run_all_searches(plan: SearchPlan, progress_callback=None):
    """Run all searches with concurrency control and batch delays"""
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_SEARCHES)
    
    async def bounded_search(item, batch_num):
        async with semaphore:
            # Add delay between batches to avoid rate limits
            if batch_num > 0:
                delay = config.BATCH_DELAY + random.uniform(0, 0.5)  # Add jitter
                await asyncio.sleep(delay)
            return await run_single_search(item, progress_callback)
    
    # Group searches into batches
    batch_size = config.MAX_CONCURRENT_SEARCHES
    results = []
    
    total_batches = (len(plan.searches) + batch_size - 1) // batch_size
    
    for i in range(0, len(plan.searches), batch_size):
        batch = plan.searches[i:i + batch_size]
        batch_num = i // batch_size
        
        if progress_callback:
            progress_callback(f"🔍 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} searches)")
        
        batch_tasks = [bounded_search(s, batch_num) for s in batch]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        
        logger.info(f"Completed batch {batch_num + 1}/{total_batches}")
    
    # Filter out exceptions
    summaries = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Search {i} failed: {result}")
            summaries.append(f"Search failed: {str(result)}")
        else:
            summaries.append(result)
    
    return summaries

async def generate_report(query: str, summaries: List[str], progress_callback=None):
    """Generate final report from summaries"""
    if progress_callback:
        progress_callback("📊 Synthesizing comprehensive report...")
    
    combined = "\n\n".join(summaries)
    result = await Runner.run(writer, combined[:config.REPORT_CHUNK_SIZE])
    costs.add(0.005)
    
    return result.final_output

# ------------------------------
# MAIN ENTRY
# ------------------------------

async def run_deep_research(query: str, progress_callback=None):
    """Main research pipeline with full error handling"""
    start_time = time.time()
    costs.reset()  # Reset costs for each research run
    
    logger.info(f"Starting research: {query}")
    
    try:
        # Step 1: Generate plan
        if progress_callback:
            progress_callback("🎯 Planning 15-point research strategy...")
        plan = await generate_plan(query)
        
        # Step 2: Execute searches
        if progress_callback:
            progress_callback(f"🔍 Executing {len(plan.searches)} comprehensive searches...")
        summaries = await run_all_searches(plan, progress_callback)
        
        # Step 3: Generate report
        report = await generate_report(query, summaries, progress_callback)
        
        duration = time.time() - start_time
        logger.info(f"Research completed in {duration:.2f}s")
        
        if progress_callback:
            progress_callback("✅ Research complete!")
        
        return {
            "report": report.model_dump(),  # Convert Pydantic model to dict
            "plan": plan.model_dump(),      # Convert Pydantic model to dict
            "costs": costs.summary(),
            "duration": round(duration, 2),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        return {
            "report": None,
            "plan": None,
            "costs": costs.summary(),
            "duration": round(time.time() - start_time, 2),
            "status": "error",
            "error": str(e)
        }

