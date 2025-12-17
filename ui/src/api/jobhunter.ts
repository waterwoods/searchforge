/**
 * JobHunter API client
 * 
 * NOTE: Cache list is backed by backend SQLite cache (via /api/jobhunter/cache),
 * not by real-time LLM calls.
 */
import request from './request';
import type { CachedJobAnalysis } from '../types/api.types';

interface RawCachedItem {
  id: number;  // Backend cache record ID (primary key)
  job_url: string;
  job_title: string;
  match_score?: number | null;
  category?: string | null;
  recommendation?: string | null;
  last_analyzed_at?: string | null;
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

