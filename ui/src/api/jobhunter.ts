/**
 * JobHunter API client
 * 
 * NOTE: Cache list is backed by backend SQLite cache (via /api/jobhunter/cache),
 * not by real-time LLM calls.
 */
import request from './request';
import type { CachedJobAnalysis } from '../types/api.types';

// ========================================
// Resume & Career Chat Types
// ========================================

export type CareerChatTopic = 'resume_opt' | 'gap_analysis' | 'tech_question';

export type ChatRole = 'user' | 'assistant' | 'system';

export interface CareerChatMessage {
  role: ChatRole;
  content: string;
}

export interface ResumeResponse {
  ok: boolean;
  profile_id: string;
  resume_text: string | null;
  error?: string | null;
}

export interface CareerChatResponse {
  ok: boolean;
  topic: string;
  answer?: string | null;
  error?: string | null;
}

export interface QuickView {
  cn_overview: string;
  responsibilities: string[];
  requirements: string[];
  red_flags: string[];
}

export interface QuickViewResponse {
  cache_id: number;
  quick_view_cn?: string | null;  // Legacy field: single string summary
  quick_view?: QuickView | null;  // New field: structured quick view
  error?: string | null;
}

export interface AnalyzeCachedRequest {
  cache_id: number;
  profile_id: string;
}

export interface AnalyzeCachedResponse {
  cache_id: number;
  ok: boolean;
  error?: string | null;
}

interface RawCachedItem {
  id: number;  // Backend cache record ID (primary key)
  job_url: string;
  job_title: string;
  match_score?: number | null;
  category?: string | null;
  recommendation?: string | null;
  last_analyzed_at?: string | null;
  auto_skip?: boolean | null;
  auto_skip_reasons?: string[] | null;
}

interface RawJobhunterCacheResponse {
  items: RawCachedItem[];
  total: number;
}

function parseJobTitle(jobTitle: string): { title: string; company: string } {
  if (!jobTitle) {
    return { title: 'Untitled Job', company: 'Unknown Company' };
  }

  // Heuristic: many titles look like "Title | Company | LinkedIn"
  const parts = jobTitle.split('|').map((p) => p.trim()).filter(Boolean);
  if (parts.length >= 2) {
    return {
      title: parts[0],
      company: parts[1],
    };
  }

  // Handle special cases for malformed titles
  // Case 1: "(N) LinkedIn" format - likely a batch import placeholder
  if (/^\(\d+\)\s+LinkedIn$/i.test(jobTitle.trim())) {
    return { title: jobTitle, company: 'LinkedIn Jobs' };
  }

  // Case 2: Just a title without company - keep as is
  return { title: jobTitle, company: 'Unknown Company' };
}

/**
 * Fetch cached JobHunter analyses for a given profile.
 *
 * Backend route: GET /api/jobhunter/cache
 * Backed by SQLite cache table (jd_analysis_cache), not by live LLM calls.
 */
export async function fetchJobhunterCache(
  profileId: string,
  limit: number = 50
): Promise<CachedJobAnalysis[]> {
  try {
    const response = await request.get<RawJobhunterCacheResponse>('/jobhunter/cache', {
      params: {
        profile_id: profileId,
        limit,
      },
    });

    const { items } = response.data || { items: [] };

    return (items || []).map((item, index) => {
      const { title, company } = parseJobTitle(item.job_title);

      const id = `${item.job_url || 'no-url'}::${item.last_analyzed_at || index}`;

      const normalized: CachedJobAnalysis = {
        id,
        cache_id: item.id,  // Backend cache record ID for detail API lookup
        job_url: item.job_url,
        job_title: item.job_title,
        title,
        company,
        match_score: item.match_score ?? null,
        category: item.category ?? null,
        recommendation: item.recommendation ?? null,
        last_analyzed_at: item.last_analyzed_at ?? null,
        autoSkip: item.auto_skip ?? false,
        autoSkipReasons: item.auto_skip_reasons ?? null,
      };

      return normalized;
    });
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`JobHunter cache request failed (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('JobHunter cache request failed: no response from server');
    }

    throw error;
  }
}

/**
 * Cached JD Detail response from backend.
 * Contains complete analysis results including core_signals, lifecycle, spotlight_stories, etc.
 */
export interface CachedJDDetail {
  id: number;
  profile_id: string;
  job_url?: string | null;
  job_title?: string | null;
  raw_text?: string | null;  // JD text (for deep analysis trigger)
  analysis: Record<string, any>;  // Contains jd_summary, fit_summary, constraints, lifecycle, spotlight_stories, core_signals, graph_steps, etc.
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * Fetch detailed cached JD analysis by cache ID.
 *
 * Backend route: GET /api/jobhunter/cache/{cache_id}
 * Returns complete analysis JSON with all fields (core_signals, lifecycle, spotlight_stories, etc.)
 */
export async function fetchCachedJDDetail(cacheId: number): Promise<CachedJDDetail> {
  try {
    const response = await request.get<CachedJDDetail>(`/jobhunter/cache/${cacheId}`);

    return response.data;
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`JobHunter cache detail request failed (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('JobHunter cache detail request failed: no response from server');
    }

    throw error;
  }
}

// ========================================
// Resume Management APIs
// ========================================

/**
 * Get user resume for a given profile.
 * 
 * Backend route: GET /api/jobhunter/profile/resume?profile_id=...
 * Returns resume text or null if not found.
 */
export async function getUserResume(profileId: string): Promise<string | null> {
  try {
    const response = await request.get<ResumeResponse>('/jobhunter/profile/resume', {
      params: {
        profile_id: profileId,
      },
    });

    const data = response.data;
    if (!data.ok || !data.resume_text) {
      return null;
    }

    return data.resume_text;
  } catch (error: any) {
    // 404 is acceptable (resume not found), return null
    if (error.response?.status === 404) {
      return null;
    }

    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to get resume (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to get resume: no response from server');
    }

    throw error;
  }
}

/**
 * Save user resume for a given profile.
 * 
 * Backend route: POST /api/jobhunter/profile/resume
 * Body: { profile_id: string, resume_text: string }
 */
export async function saveUserResume(profileId: string, resumeText: string): Promise<void> {
  try {
    const response = await request.post<ResumeResponse>('/jobhunter/profile/resume', {
      profile_id: profileId,
      resume_text: resumeText,
    });

    const data = response.data;
    if (!data.ok) {
      const errorMsg = data.error || 'Failed to save resume';
      throw new Error(errorMsg);
    }
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to save resume (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to save resume: no response from server');
    }

    throw error;
  }
}

// ========================================
// Career Chat API
// ========================================

/**
 * Send career chat message.
 * 
 * Backend route: POST /api/jobhunter/career_chat
 * Body: { profile_id: string, cache_id: number, topic: CareerChatTopic, messages: CareerChatMessage[] }
 */
export async function sendCareerChat(params: {
  profileId: string;
  cacheId: number;
  topic: CareerChatTopic;
  messages: CareerChatMessage[];
}): Promise<CareerChatResponse> {
  try {
    const response = await request.post<CareerChatResponse>('/jobhunter/career_chat', {
      profile_id: params.profileId,
      cache_id: params.cacheId,
      topic: params.topic,
      messages: params.messages,
    });

    const data = response.data;
    if (!data.ok) {
      const errorMsg = data.error || 'Career chat failed';
      throw new Error(errorMsg);
    }

    return data;
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Career chat failed (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Career chat failed: no response from server');
    }

    throw error;
  }
}

// ========================================
// Quick View API
// ========================================

/**
 * Get quick view (快速概览) for a cached JD analysis.
 * 
 * Backend route: POST /api/jobhunter/quick_view
 * Body: { cache_id: number }
 * Returns: QuickViewResponse with quick_view_cn (3-5 sentence Chinese summary)
 */
export async function getQuickView(cacheId: number): Promise<QuickViewResponse> {
  try {
    const response = await request.post<QuickViewResponse>('/jobhunter/quick_view', {
      cache_id: cacheId,
    });

    return response.data;
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to fetch quick view (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to fetch quick view: no response from server');
    }

    throw error;
  }
}

// ========================================
// Lv2 Deep Analysis API
// ========================================

/**
 * Trigger Lv2 deep analysis for a cached JD.
 * 
 * Backend route: POST /api/jobhunter/analyze_cached
 * Body: { cache_id: number, profile_id: string }
 * Returns: AnalyzeCachedResponse
 */
export async function runFullAnalysisForCacheId(
  cacheId: number,
  profileId: string
): Promise<AnalyzeCachedResponse> {
  try {
    const response = await request.post<AnalyzeCachedResponse>('/jobhunter/analyze_cached', {
      cache_id: cacheId,
      profile_id: profileId,
    });

    const data = response.data;
    if (!data.ok) {
      const errorMsg = data.error || 'Failed to run full analysis';
      throw new Error(errorMsg);
    }

    return data;
  } catch (error: any) {
    // Normalize error message for callers
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to run full analysis (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to run full analysis: no response from server');
    }

    throw error;
  }
}

