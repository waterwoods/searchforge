import { API_BASE_URL } from './config';

export type AnalyticsDashboard = {
    north_star_avg: number | null;
    dimension_breakdown: Record<string, number | null>;
    funnel: {
        counts: Record<string, number>;
        conversion_rates: Record<string, number | null>;
    };
    dropoff_points: Array<{ from_step: string; to_step: string; drop_sessions: number; drop_rate: number }>;
    dropoff_summary: { biggest_drop: string | null; suspected_reason: string | null };
    top_issues: string[];
    sessions_in_buffer: number;
};

export async function fetchAnalyticsDashboard(): Promise<AnalyticsDashboard> {
    const url = `${API_BASE_URL}/api/analytics/dashboard`;
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`analytics dashboard failed: ${res.status}`);
    }
    return res.json() as Promise<AnalyticsDashboard>;
}
