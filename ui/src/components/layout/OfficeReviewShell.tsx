/**
 * Minimal broker office chrome for /workbench/document-intake — no SearchForge lab shell.
 */
import React from 'react';
import { Layout, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { InboxOutlined, FormOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Text } = Typography;

const OFFICE_SHORT = 'CKS Insurance Agency';
const OFFICE_NAME = 'Chen Kui Insurance Office';

type Props = { children: React.ReactNode };

export function OfficeReviewShell({ children }: Props) {
    return (
        <Layout style={{ minHeight: '100vh', background: '#f5f6f8' }}>
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
