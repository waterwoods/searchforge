/**
 * Client config context — provides client-specific UI copy to Unified Intake.
 * Fetches from GET /api/inbox/client-config?client=<id>.
 * Client ID from URL ?client= param, or backend default.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getClientConfig, mergeUiCopy, type UiCopy } from '../api/clientConfig';

interface ClientConfigState {
    clientId: string;
    uiCopy: UiCopy;
    loading: boolean;
    error: string | null;
}

const defaultState: ClientConfigState = {
    clientId: 'chen_kui',
    uiCopy: mergeUiCopy(undefined),
    loading: true,
    error: null,
};

const ClientConfigContext = createContext<ClientConfigState>(defaultState);

export function ClientConfigProvider({ children }: { children: React.ReactNode }) {
    const [searchParams] = useSearchParams();
    const clientParam = searchParams.get('client')?.trim() || undefined;
    const [state, setState] = useState<ClientConfigState>(defaultState);

    const fetchConfig = useCallback(async () => {
        setState((s) => ({ ...s, loading: true, error: null }));
        try {
            const res = await getClientConfig(clientParam);
            const merged = mergeUiCopy(res.ui_copy);
            setState({
                clientId: res.client_id,
                uiCopy: merged,
                loading: false,
                error: null,
            });
        } catch (e) {
            const msg = (e as { message?: string })?.message ?? 'Failed to load client config';
            setState((s) => ({
                ...s,
                loading: false,
                error: msg,
                uiCopy: mergeUiCopy(undefined),
            }));
        }
    }, [clientParam]);

    useEffect(() => {
        void fetchConfig();
    }, [fetchConfig]);

    return (
        <ClientConfigContext.Provider value={state}>
            {children}
        </ClientConfigContext.Provider>
    );
}

export function useClientConfig(): ClientConfigState {
    const ctx = useContext(ClientConfigContext);
    return ctx ?? defaultState;
}
