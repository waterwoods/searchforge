/**
 * Release identity bar — lightweight build/version display for founder clarity.
 * Shows: version, built time (LA), build id, environment.
 */
import { Typography } from 'antd';

const { Text } = Typography;

function formatBuildTimeLA(iso: string): string {
    try {
        const d = new Date(iso);
        const dateStr = d.toLocaleDateString('en-CA', {
            timeZone: 'America/Los_Angeles',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        });
        const timeStr = d.toLocaleTimeString('en-US', {
            timeZone: 'America/Los_Angeles',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        });
        return `${dateStr} ${timeStr} PT`;
    } catch {
        return iso?.slice(0, 16) || '—';
    }
}

function getEnv(): string {
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_APP_ENV) {
        return import.meta.env.VITE_APP_ENV;
    }
    return import.meta.env?.DEV ? 'local' : 'production';
}

export const ReleaseIdentityBar = () => {
    const version = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '—';
    const buildTimeIso = typeof __BUILD_TIME_ISO__ !== 'undefined' ? __BUILD_TIME_ISO__ : '';
    const buildId = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : '—';
    const env = getEnv();

    const builtStr = formatBuildTimeLA(buildTimeIso);

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                fontSize: '11px',
                flexShrink: 0,
                flex: '0 0 auto',
                minWidth: 200,
                whiteSpace: 'nowrap',
            }}
        >
            <Text style={{ color: 'rgba(255,255,255,0.98)', fontSize: '11px' }}>
                v{version}
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.95)', fontSize: '11px' }}>
                Built: {builtStr}
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.92)', fontSize: '11px' }}>
                {buildId}
            </Text>
            <Text
                style={{
                    color: 'rgba(255,255,255,0.88)',
                    fontSize: '10px',
                    textTransform: 'uppercase',
                }}
            >
                {env}
            </Text>
        </div>
    );
};
