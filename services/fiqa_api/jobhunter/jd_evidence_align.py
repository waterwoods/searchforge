"""
jd_evidence_align.py - Evidence Alignment for Spotlight Stories
================================================================

This module provides functionality to attach evidence snippets from the original JD text
to spotlight stories, helping reduce hallucinations by grounding stories in actual JD content.

[Step 2 改动] 新增模块，实现简单的启发式证据提取算法。
"""

import re
import logging
from typing import List

from services.fiqa_api.jobhunter.schemas import JobJDSummary, SpotlightStory

logger = logging.getLogger(__name__)


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text by splitting on spaces, commas, and common delimiters.
    Filters out very short words (< 3 characters) and common stop words.
    
    Args:
        text: Input text
        
    Returns:
        List of keywords (normalized to lowercase)
    """
    # Common stop words to filter out
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "have", "has", "had", "do", "does", "did", "will", "would",
        "should", "could", "may", "might", "must", "can", "this", "that",
        "these", "those", "it", "its", "they", "them", "their", "we", "our",
    }
    
    # Split on spaces, commas, semicolons, parentheses, etc.
    words = re.split(r'[\s,\-;()\[\]{}|]+', text.lower())
    
    # Filter: keep words with length >= 3, not stop words, and alphanumeric
    keywords = []
    for word in words:
        word = word.strip()
        if len(word) >= 3 and word not in stop_words and word.isalnum():
            keywords.append(word)
    
    return keywords


def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitting (by periods, exclamation marks, question marks).
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Split on sentence-ending punctuation, but keep the delimiter
    sentences = re.split(r'([.!?]+)', text)
    
    # Recombine sentences with their punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]
        if sentence:
            result.append(sentence.strip())
    
    # Handle case where text doesn't end with punctuation
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    
    return result


def find_relevant_snippets(
    jd_text: str,
    story: SpotlightStory,
    max_snippets: int = 3,
) -> List[str]:
    """
    Find relevant JD text snippets for a spotlight story using keyword matching.
    
    Args:
        jd_text: Original JD text
        story: SpotlightStory to find evidence for
        max_snippets: Maximum number of snippets to return
        
    Returns:
        List of relevant sentence snippets from JD (up to max_snippets)
    """
    # Extract keywords from the story's focus area and tools_and_systems
    focus_keywords = extract_keywords(story.focus_area)
    tools_keywords = extract_keywords(story.tools_and_systems)
    
    # Combine keywords (remove duplicates)
    all_keywords = list(set(focus_keywords + tools_keywords))
    
    if not all_keywords:
        return []
    
    # Split JD into sentences
    jd_sentences = split_into_sentences(jd_text)
    
    # Score each sentence by keyword matches
    scored_sentences = []
    for sentence in jd_sentences:
        sentence_lower = sentence.lower()
        # Count keyword matches
        match_count = sum(1 for keyword in all_keywords if keyword in sentence_lower)
        if match_count > 0:
            scored_sentences.append((match_count, sentence))
    
    # Sort by match count (descending) and take top max_snippets
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    
    # Return the sentences (without scores), limiting to max_snippets
    snippets = [sentence for _, sentence in scored_sentences[:max_snippets]]
    
    return snippets


def attach_evidence_snippets(
    jd_text: str,
    summary: JobJDSummary,
) -> JobJDSummary:
    """
    Attach evidence snippets from JD text to spotlight stories.
    
    For each spotlight story, finds 1-3 relevant sentence snippets from the original JD
    that support the story's focus area and tools/systems.
    
    Args:
        jd_text: Original JD description text
        summary: JobJDSummary with spotlight_stories (may be None)
        
    Returns:
        Updated JobJDSummary with evidence_snippets populated for each spotlight story
    """
    if not summary.spotlight_stories:
        return summary
    
    logger.info(f"Attaching evidence snippets to {len(summary.spotlight_stories)} spotlight stories...")
    
    # Update each spotlight story with evidence snippets
    updated_stories = []
    for story in summary.spotlight_stories:
        snippets = find_relevant_snippets(jd_text, story, max_snippets=3)
        
        # Create updated story with evidence snippets
        updated_story = SpotlightStory(
            focus_area=story.focus_area,
            why_important=story.why_important,
            upstream_downstream=story.upstream_downstream,
            tools_and_systems=story.tools_and_systems,
            constraints_and_risks=story.constraints_and_risks,
            success_metrics=story.success_metrics,
            evidence_snippets=snippets,
        )
        updated_stories.append(updated_story)
    
    # Update summary with updated stories
    summary.spotlight_stories = updated_stories
    
    return summary
