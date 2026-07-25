/**
 * P3-C Slice 1 — Unified Broker Header (display only).
 * Who / Vehicle / Next Action — reuse workbench_list projection helpers.
 */
import type { CSSProperties } from 'react';
import { Typography } from 'antd';
import type { SavedCase } from '@/api/inboxTriage';
import {
  resolveCurrentActionLabel,
  resolveFindabilityCustomerName,
  resolveVehicleContext,
} from '@/features/intake/utils/workbenchFindability';

const { Text } = Typography;

export type BrokerHeaderFields = {
  customerDisplayName: string;
  vehicleSummary: string;
  currentNextAction: string;
};

/** Resolve V1 header fields from existing projection helpers (no new rules). */
export function resolveBrokerHeaderFields(caseItem: SavedCase): BrokerHeaderFields {
  const customerDisplayName = resolveFindabilityCustomerName(caseItem);
  const vehicleRaw = resolveVehicleContext(caseItem).trim();
  return {
    customerDisplayName,
    vehicleSummary: vehicleRaw || '—',
    currentNextAction: resolveCurrentActionLabel(caseItem),
  };
}

export type BrokerHeaderProps = {
  caseItem: SavedCase;
  /** Optional style override (e.g. tighter drawer spacing). */
  style?: CSSProperties;
};

/**
 * Compact case context header for broker detail surfaces.
 * Answers: Who? Vehicle? What should I do next?
 */
export function BrokerHeader({ caseItem, style }: BrokerHeaderProps) {
  const { customerDisplayName, vehicleSummary, currentNextAction } =
    resolveBrokerHeaderFields(caseItem);

  return (
    <div
      className="broker-header"
      data-testid="broker-header"
      style={{
        marginBottom: 12,
        padding: '12px 14px',
        borderRadius: 8,
        border: '1px solid #d6e4ff',
        borderLeft: '4px solid #2f54eb',
        background: 'linear-gradient(180deg, #f7faff 0%, #ffffff 100%)',
        ...style,
      }}
    >
      <Text
        strong
        className="broker-header-customer"
        data-testid="broker-header-customer"
        style={{ fontSize: 16, color: '#10239e', display: 'block', lineHeight: 1.35 }}
      >
        {customerDisplayName}
      </Text>
      <Text
        className="broker-header-vehicle"
        data-testid="broker-header-vehicle"
        style={{ fontSize: 13, color: '#434343', display: 'block', marginTop: 4, lineHeight: 1.4 }}
      >
        {vehicleSummary}
      </Text>
      <Text
        className="broker-header-next-action"
        data-testid="broker-header-next-action"
        style={{
          fontSize: 13,
          color: '#0958d9',
          display: 'block',
          marginTop: 8,
          fontWeight: 600,
          lineHeight: 1.4,
        }}
      >
        {currentNextAction}
      </Text>
    </div>
  );
}
