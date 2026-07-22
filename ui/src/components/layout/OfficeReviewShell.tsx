/**
 * Minimal broker office chrome for /workbench/document-intake — no SearchForge lab shell.
 *
 * Preview/QA builds that bake Cloud QA API show a persistent QA banner so Founders
 * never confuse this surface with Production (smoky-beta).
 */
import React from 'react';
import { Layout, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { InboxOutlined, FormOutlined } from '@ant-design/icons';
import {
    isCloudQaWorkbenchClient,
    workbenchApiProfileLabel,
} from '@/config/workbenchEnv';

const { Header, Content } = Layout;
const { Text } = Typography;

const OFFICE_SHORT = 'CKS Insurance Agency';
const OFFICE_NAME = 'Chen Kui Insurance Office';

type Props = { children: React.ReactNode };

export function OfficeReviewShell({ children }: Props) {
    const showQaBanner = isCloudQaWorkbenchClient();
    const apiProfile = workbenchApiProfileLabel();

    return (
        <Layout style={{ minHeight: '100vh', background: '#f5f6f8' }}>
            {showQaBanner ? (
                <div
                    role="status"
                    data-testid="workbench-qa-banner"
                    style={{
                        background: '#1f4b99',
                        color: '#fff',
                        padding: '6px 24px',
                        fontSize: 12,
                        fontWeight: 600,
                        letterSpacing: 0.2,
                        display: 'flex',
                        gap: 16,
                        alignItems: 'center',
                        flexWrap: 'wrap',
                    }}
                >
                    <span>QA</span>
                    <span style={{ opacity: 0.85 }}>TEST</span>
                    <span style={{ opacity: 0.85 }}>API profile: {apiProfile}</span>
                    <span style={{ opacity: 0.75, fontWeight: 500 }}>
                        Cloud QA cases only — not Production
                    </span>
                </div>
            ) : null}
            <Header
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: '#fff',
                    borderBottom: '1px solid #e8e8e8',
                    padding: '0 24px',
                    height: 56,
                    lineHeight: '56px',
                }}
            >
                <div>
                    <Text strong style={{ fontSize: 15, color: '#1a1a1a' }}>
                        {OFFICE_SHORT}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 12 }}>
                        {OFFICE_NAME}
                    </Text>
                </div>
                <nav style={{ display: 'flex', gap: 20, fontSize: 13 }}>
                    <Link
                        to="/workbench/document-intake"
                        style={{ color: '#1677ff', fontWeight: 600, textDecoration: 'none' }}
                    >
                        <InboxOutlined style={{ marginRight: 6 }} />
                        Office Review Queue
                    </Link>
                    <Link
                        to="/add-car"
                        style={{ color: '#595959', textDecoration: 'none' }}
                    >
                        <FormOutlined style={{ marginRight: 6 }} />
                        Customer Wizard
                    </Link>
                </nav>
            </Header>
            <Content style={{ background: '#f5f6f8' }}>{children}</Content>
        </Layout>
    );
}
