/**
 * Job Application APIs for JobHunter
 */
import request from './request';

export type ApplicationStatus = 'planned' | 'applied' | 'interviewing' | 'offer' | 'rejected' | 'skipped';

export interface JobApplicationItem {
  id: number;
  profile_id: string;
  cache_id: number;
  job_url?: string | null;
  job_title?: string | null;
  company?: string | null;
  status: ApplicationStatus;
  first_seen_at?: string | null;
  applied_at?: string | null;
  last_updated_at?: string | null;
  notes?: string | null;
}

export interface JobApplicationListResponse {
  items: JobApplicationItem[];
  total: number;
}

/**
 * Get job application records.
 * 
 * Backend route: GET /api/jobhunter/applications
 * Query params: profile_id, status (optional), limit, offset
 */
export async function getJobApplications(params: {
  profileId: string;
  status?: ApplicationStatus;
  limit?: number;
  offset?: number;
}): Promise<JobApplicationListResponse> {
  try {
    const response = await request.get<JobApplicationListResponse>('/jobhunter/applications', {
      params: {
        profile_id: params.profileId,
        status: params.status,
        limit: params.limit || 100,
        offset: params.offset || 0,
      },
    });

    return response.data;
  } catch (error: any) {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to get job applications (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to get job applications: no response from server');
    }
    throw error;
  }
}

/**
 * Create or update a job application record.
 * 
 * Backend route: POST /api/jobhunter/applications
 * Body: { profile_id: string, cache_id: number, status: ApplicationStatus, notes?: string }
 */
export async function upsertJobApplication(params: {
  profileId: string;
  cacheId: number;
  status: ApplicationStatus;
  notes?: string;
}): Promise<JobApplicationItem> {
  try {
    const response = await request.post<JobApplicationItem>('/jobhunter/applications', {
      profile_id: params.profileId,
      cache_id: params.cacheId,
      status: params.status,
      notes: params.notes,
    });

    return response.data;
  } catch (error: any) {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to update job application (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to update job application: no response from server');
    }
    throw error;
  }
}

/**
 * Delete a job application record (mark as not applied).
 * 
 * Backend route: DELETE /api/jobhunter/applications
 * Query params: profile_id, cache_id
 */
export async function deleteJobApplication(params: {
  profileId: string;
  cacheId: number;
}): Promise<{ ok: boolean; deleted: boolean }> {
  try {
    const response = await request.delete<{ ok: boolean; deleted: boolean }>('/jobhunter/applications', {
      params: {
        profile_id: params.profileId,
        cache_id: params.cacheId,
      },
    });

    return response.data;
  } catch (error: any) {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      throw new Error(`Failed to delete job application (HTTP ${status}): ${errorMessage}`);
    } else if (error.request) {
      throw new Error('Failed to delete job application: no response from server');
    }
    throw error;
  }
}

