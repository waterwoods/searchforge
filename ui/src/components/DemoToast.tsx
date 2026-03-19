/**
 * Simple toast for copy feedback (no heavy deps).
 */

interface DemoToastProps {
  message: string;
  type: 'success' | 'fail';
  visible: boolean;
}

export function DemoToast({ message, type, visible }: DemoToastProps) {
  if (!visible) return null;
  return (
    <div
      className={`demo-toast demo-toast-${type}`}
      role="status"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
