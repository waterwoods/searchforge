/**
 * Minimal smoke component to verify /demo route is hit.
 * No antd, no external deps. Inline styles ensure visibility.
 */
export function DemoRouteSmoke() {
  return (
    <div style={{ padding: 24, background: '#fff', color: '#333', fontSize: 18 }}>
      Demo route smoke OK
    </div>
  );
}
