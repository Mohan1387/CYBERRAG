"""
Answer Generation Module

This module handles the generation of natural language answers using a Large Language Model (LLM).
It constructs a prompt using retrieved context documents and the user's question, then queries
the Google Gemini API to generate a comprehensive response.
"""

from textwrap import dedent
from typing import List, Dict, Any
import ollama
from src.config import OLLAMA_HOST, SUMMARIZE_MODEL, GEMMA_API_KEY
from src.logger import get_logger, progress_tracker
import google.generativeai as genai

logger = get_logger("answerer")

def generate_answer(
    question: str,
    hits: Dict[str, Any]
) -> str:
    """
    Generate a comprehensive answer to a user's question based on retrieved documents.
    
    This function:
    1. Constructs a prompt with strict persona and citation guidelines.
    2. Includes the retrieved documents (hits) as context.
    3. Queries the Google Gemini API.
    4. Returns the generated text response.
    
    Args:
        question (str): The user's question.
        hits (Dict[str, Any]): A dictionary of retrieved documents (name -> text).
        
    Returns:
        str: The generated answer from the LLM.
        
    Raises:
        Exception: If the LLM generation fails.
    """
    progress_tracker.start_stage("generate_answer", f"Question: {question[:50]}")
    
    try:
        logger.info(f"📝 Generating answer for question: '{question}'")
        logger.debug(f"Using {len(hits)} documents as context")
        
        question = question.strip()
        contexts = hits

        PROMPT_TEMPLATE = f"""You are a Senior Threat Intelligence Analyst briefing a client. You possess direct knowledge of the threats.

### STYLE & BEHAVIOR GUIDELINES (STRICT):
1.  **Be the Expert:** Answer directly and confidently. **Adopt the information as your own knowledge.**
2.  **Banned Phrases:** NEVER start sentences with "Based on the documents," "The text says," "According to the context," or similar meta-talk.
3.  **Citation:** Every factual claim must be followed by a citation in the format document name passed in the context.
4.  **Refusal:** If the answer is not in the contexts, strictly state: "The provided documents do not contain information to answer this question."
5.  **Answer Length:** Provide a concise yet comprehensive answer of at least 5 paragraphs when necessary.

### LOGIC & REASONING:
1.  **Grounding:** Use ONLY the provided context snippets. Do not use outside knowledge.
2.  **Conflict Resolution:** The contexts are ordered by relevance. If information in Context 1 conflicts with Context 3, **prioritize Context 1**.
3.  **Completeness:** Synthesize details from multiple source given in the contexts to provide a comprehensive answer.

### EXAMPLES OF CORRECT VS. INCORRECT BEHAVIOR:

**Question:** What vulnerability is Akira exploiting?
❌ **Bad Answer:** Based on the provided documents, Akira is exploiting CVE-2020-3259.
✅ **Good Answer:** Akira actors are actively exploiting CVE-2020-3259 to gain initial access [1].

**Question:** Who are they targeting?
❌ **Bad Answer:** The text mentions that they target the healthcare sector.
✅ **Good Answer:** They aggressively target the healthcare sector, focusing on patient data exfiltration [2].

**Question:** What is the ransom demand? (Information missing)
❌ **Bad Answer:** I cannot find that in the text.
✅ **Good Answer:** The provided documents do not contain information to answer this question.

---
### INTELLIGENCE SOURCES:
{contexts}

### CLIENT QUESTION:
{question}

### YOUR BRIEFING:
"""

        logger.debug(f"Configuring Gemini model: {SUMMARIZE_MODEL}")
        genai.configure(api_key=GEMMA_API_KEY)
        model = genai.GenerativeModel(SUMMARIZE_MODEL)
        
        logger.debug("Sending prompt to LLM...")
        response = model.generate_content(PROMPT_TEMPLATE)
        
        if response and response.text:
            answer_length = len(response.text)
            progress_tracker.complete_stage("generate_answer", f"Generated {answer_length} chars")
            logger.info(f"✓ Answer generated successfully ({answer_length} characters)")
            return response.text
        else:
            progress_tracker.complete_stage("generate_answer", "Empty response")
            logger.warning("LLM returned empty response")
            return "Unable to generate answer from the provided contexts."
            
    except Exception as e:
        progress_tracker.fail_stage("generate_answer", str(e))
        logger.error(f"✗ LLM answer generation failed: {e}", exc_info=True)
        raise Exception(f"LLM answer generation error: {str(e)}")