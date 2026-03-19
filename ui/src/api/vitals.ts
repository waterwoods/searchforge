/**
 * Vitals API client
 * 
 * Handles API calls for health monitoring data (heart rate, SpO2)
 */
import request from './request';

// ========================================
// Types
// ========================================

export interface VitalsReading {
    id: number;
    source: string;
    hr: number;
    spo2: number;
    time_ms?: number | null;
    time_str?: string | null;
    created_at: string; // ISO timestamp
}

export interface VitalsLatestResponse {
    readings: VitalsReading[];
}

// ========================================
// API Functions
// ========================================

/**
 * Get the latest vitals readings
 * @param limit Maximum number of readings to return (default: 60)
 * @returns Latest vitals readings
 */
export async function getLatestVitals(limit: number = 60): Promise<VitalsLatestResponse> {
    // [vitals-lan] uses same origin / proxy - relative path works via Vite proxy
    const response = await request.get<VitalsLatestResponse>('/vitals/latest', {
        params: { limit },
    });
    return response.data;
}
