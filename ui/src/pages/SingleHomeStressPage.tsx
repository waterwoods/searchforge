// frontend/src/pages/SingleHomeStressPage.tsx
/**
 * Single Home Stress Check Page
 * 
 * Layout Structure:
 * - Left Column (30-35% width on desktop): Input form with property selection, financial inputs, and "Ask AI" card
 *   - Narrower column to emphasize the right-hand dashboard
 * - Right Column (65-70% width on desktop): Main results dashboard
 *   1. Top Row: Two side-by-side cards - "Your Wallet" and "Target Home" (lighter background #1d1f23)
 *   2. Stress Band Bar: Horizontal 3-segment bar (Loose/OK/Tight) with prominent band label and DTI (background #24272c)
 *   3. What-if Scenarios: Quick scenario buttons (-10% income, -$50k price)
 *   4. Payment Breakdown: Detailed payment statistics with emphasized Total Monthly Payment
 *   5. AI Explanation: Borrower narrative and recommended actions
 *   6. Agent Steps: Collapsible section showing AI reasoning steps
 * 
 * Visual Emphasis:
 * - Core numbers (stress band label, DTI ratio, Total Monthly Payment, Monthly Income, Cash Flow) use larger fonts and bold weights
 * - Different card background shades (#1d1f23 for wallet/home, #24272c for stress band, default for others) create visual separation
 * - Consistent vertical spacing (margin-top) between sections prevents visual blending
 * 
 * Responsive:
 * - Large screens (1200px+): Left 30-35%, Right 65-70%
 * - Small screens: Columns stack vertically (xs={24})
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
    Card,
    Typography,
    InputNumber,
    Input,
    Button,
    Row,
    Col,
    Form,
    App,
    Spin,
    Tag,
    Alert,
    Space,
    Select,
    Radio,
    Divider,
    Statistic,
    Table,
    Collapse,
    Skeleton,
} from 'antd';
import { BankOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { API_BASE_URL } from '../api/config';
import {
    StressCheckRequest,
    StressCheckResponse,
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
    MortgageProperty,
    AgentStep,
    SuggestedScenario,
    SaferHomesResult,
    SafetyUpgradeResult,
    ApprovalScore,
    MortgageProgramPreview,
    RiskAssessment,
    StressBand,
    StrategyLabResult,
} from '../types/api.types';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;
const { TextArea } = Input;

interface SessionProfile {
    monthlyIncome: number;
    otherDebtsMonthly: number;
    downPaymentPct: number;
    riskPreference: 'conservative' | 'neutral' | 'aggressive';
}

// Preset scenario type for demo purposes
interface PresetScenario {
    id: string;
    name: string;
    description: string;
    values: {
        monthly_income: number;
        other_debts_monthly: number;
        list_price: number;
        down_payment_pct: number;
        state: string;
        zip_code?: string;
        hoa_monthly?: number;
        risk_preference: 'conservative' | 'neutral' | 'aggressive';
    };
}

// Preset scenarios for demo - aligned with backend demo_scenarios.py
const PRESET_SCENARIOS: PresetScenario[] = [
    {
        id: 'socal_tight',
        name: 'SoCal High Price, Feels Tight',
        description: 'High income but very expensive SoCal home. DTI should land in tight band (43-80%).',
        values: {
            monthly_income: 15000,
            other_debts_monthly: 600,
            list_price: 1100000,
            down_payment_pct: 20,
            state: 'CA',
            zip_code: '92648',
            hoa_monthly: 450,
            risk_preference: 'neutral',
        },
    },
    {
        id: 'texas_starter_ok',
        name: 'Texas Starter Home, Comfortable',
        description: 'Moderate income, reasonable starter home in Texas. DTI in ok band (36-43%).',
        values: {
            monthly_income: 9000,
            other_debts_monthly: 300,
            list_price: 380000,
            down_payment_pct: 20,
            state: 'TX',
            zip_code: '78701',
            hoa_monthly: 150,
            risk_preference: 'neutral',
        },
    },
    {
        id: 'extreme_high_risk',
        name: 'Extreme High Risk, Hard Block',
        description: 'Low/modest income, very high home price, minimal down payment. DTI > 80%, triggers hard_block.',
        values: {
            monthly_income: 4500,
            other_debts_monthly: 1200,
            list_price: 850000,
            down_payment_pct: 5,
            state: 'CA',
            zip_code: '90803',
            hoa_monthly: 400,
            risk_preference: 'neutral',
        },
    },
    {
        id: 'borderline_with_aid',
        name: 'Borderline but Aid-Eligible',
        description: 'Borderline DTI/LTV, moderate income. DTI in tight band (43-80%), should find mortgage programs.',
        values: {
            monthly_income: 8000,
            other_debts_monthly: 500,
            list_price: 550000,
            down_payment_pct: 15,
            state: 'CA',
            zip_code: '92705',
            hoa_monthly: 350,
            risk_preference: 'neutral',
        },
    },
];

// Type for parsed AI Answer
type ParsedAiAnswer = {
    borrowerNarrative?: string;
    recommendedActions?: string[];
    rawText: string; // Fallback text
};

// Helper function to parse AI Answer from various formats
function parseAiAnswer(raw: string | object | undefined): ParsedAiAnswer {
    if (!raw) {
        return { rawText: '' };
    }

    // Handle object case
    if (typeof raw === 'object') {
        const anyRaw = raw as any;
        return {
            borrowerNarrative: anyRaw.borrower_narrative ?? anyRaw.borrowerNarrative,
            recommendedActions: anyRaw.recommended_actions ?? anyRaw.recommendedActions,
            rawText: JSON.stringify(raw, null, 2),
        };
    }

    // Handle string case: try to parse as JSON, fallback to raw text
    try {
        const parsed = JSON.parse(raw);
        const anyParsed = parsed as any;
        return {
            borrowerNarrative: anyParsed.borrower_narrative ?? anyParsed.borrowerNarrative,
            recommendedActions: anyParsed.recommended_actions ?? anyParsed.recommendedActions,
            rawText: raw,
        };
    } catch {
        return { rawText: raw };
    }
}

/**
 * Demo script (for hiring manager):
 * 
 * Users can either type in the NL assistant on the right, or use the presets and form on the left.
 * 
 * Conversation path:
 * 1. In the NL assistant, type something like:
 *    "I make $150k a year and I'm looking at a $750k home in 90803 with 20% down."
 * 2. Answer any follow-up questions until the NL card says it has enough info.
 * 3. Click "Run Mortgage Agent on this plan".
 * 4. Scroll to the Stage Timeline and Agent Steps to see the full workflow.
 *    (A badge indicates that this run was started from conversation.)
 * 
 * Preset path:
 * - Select a preset from the Demo Presets dropdown to auto-fill the form and run the Mortgage Agent.
 * - Badge shows "Started from form".
 * 
 * Note: Both entry modes lead to the same unified Mortgage Agent workflow.
 */

// [CHANGE] Added natural language Single-Home Agent entry for /single-home-agent
export const SingleHomeStressPage = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<SingleHomeAgentResponse | null>(null);
    const [properties, setProperties] = useState<MortgageProperty[]>([]);
    const [loadingProperties, setLoadingProperties] = useState(false);
    const [sessionProfile, setSessionProfile] = useState<SessionProfile | null>(null);
    const [usingSessionProfile, setUsingSessionProfile] = useState(false);
    const [nlQuestion, setNlQuestion] = useState<string>('');
    const [nlLoading, setNlLoading] = useState<boolean>(false);
    const [nlError, setNlError] = useState<string | null>(null);
    const [nlAnswer, setNlAnswer] = useState<SingleHomeAgentResponse | null>(null);

    // NL Assistant state (for form filling)
    const [nlAssistantText, setNlAssistantText] = useState<string>('');
    const [nlAssistantLoading, setNlAssistantLoading] = useState<boolean>(false);
    const [nlAssistantError, setNlAssistantError] = useState<string | null>(null);
    const [nlConversation, setNlConversation] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
    const [nlAssistantResult, setNlAssistantResult] = useState<{
        partial_request: Record<string, any>;
        merged_request?: Record<string, any>;
        missing_required_fields: string[];
        router_decision: 'have_enough_info' | 'need_more_info';
        followup_question?: string;
        conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>;
    } | null>(null);
    const [showFullExplanation, setShowFullExplanation] = useState(false);
    const [saferHomesResult, setSaferHomesResult] = useState<SaferHomesResult | null>(null);
    const [saferHomesLoading, setSaferHomesLoading] = useState<boolean>(false);
    const [saferHomesError, setSaferHomesError] = useState<string | null>(null);
    const [lastRunStartedFromNL, setLastRunStartedFromNL] = useState(false);

    const formatCurrency = (value?: number | null, minFractionDigits: number = 0, maxFractionDigits: number = 0) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return '--';
        }
        return `$${value.toLocaleString(undefined, {
            minimumFractionDigits: minFractionDigits,
            maximumFractionDigits: maxFractionDigits,
        })}`;
    };

    const formatPercent = (value?: number | null, fractionDigits: number = 1) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return '--';
        }
        return `${(value * 100).toFixed(fractionDigits)}%`;
    };

    const getStrategyLabSummaryText = (strategyLab: StrategyLabResult | null | undefined): string | null => {
        if (!strategyLab || !strategyLab.scenarios || strategyLab.scenarios.length === 0) {
            return null;
        }

        const baselineBand = strategyLab.baseline_stress_band;
        if (!baselineBand) {
            return null;
        }

        // Check if baseline is tight or high_risk
        const isBaselineTightOrWorse = baselineBand === 'tight' || baselineBand === 'high_risk';

        // Check all scenarios
        const allScenarios = strategyLab.scenarios;
        const allTightOrWorse = allScenarios.every(
            (scenario) => scenario.stress_band === 'tight' || scenario.stress_band === 'high_risk'
        );
        const hasOkOrLoose = allScenarios.some(
            (scenario) => scenario.stress_band === 'ok' || scenario.stress_band === 'loose'
        );

        // Case A: All (baseline + all scenarios) are tight or high_risk
        if (isBaselineTightOrWorse && allTightOrWorse) {
            return "Even after trying a few tweaks, this home still looks out of reach for your current profile. Consider looking for cheaper homes or different ZIPs.";
        }

        // Case B: At least one scenario is ok or loose
        if (hasOkOrLoose) {
            return "Some tweaks make this plan more manageable. Focus on the scenarios with lower stress bands.";
        }

        // Case C: Other cases (e.g., some improvement but still mostly tight)
        return "These scenarios show how price or down payment changes move your stress level, but this home may still be on the tight side.";
    };

    const buildStressRequestPayload = useCallback((values: any): StressCheckRequest => {
        let listPrice = values.list_price;
        let state = values.state;

        if (values.property_id) {
            const property = properties.find((p) => p.id === values.property_id);
            if (property) {
                listPrice = property.purchase_price;
                state = property.state;
            }
        }

        return {
            monthly_income: values.monthly_income,
            other_debts_monthly: values.other_debts_monthly,
            list_price: listPrice,
            down_payment_pct: ((values.down_payment_pct ?? 20) / 100),
            state: state || null,
            zip_code: values.zip_code || null,
            hoa_monthly: values.hoa_monthly || 0,
            risk_preference: values.risk_preference || 'neutral',
        };
    }, [properties]);

    // Load properties on mount
    useEffect(() => {
        const loadProperties = async () => {
            try {
                setLoadingProperties(true);
                const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/properties`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                });

                if (!res.ok) {
                    throw new Error(`Failed to load properties: ${res.status}`);
                }

                const data: MortgageProperty[] = await res.json();
                setProperties(data);
            } catch (err) {
                console.error('Failed to load properties:', err);
                message.warning('Failed to load property list.');
            } finally {
                setLoadingProperties(false);
            }
        };

        loadProperties();
    }, [message]);

    const handlePropertyChange = (propertyId: string | null) => {
        if (propertyId) {
            const property = properties.find(p => p.id === propertyId);
            if (property) {
                form.setFieldsValue({
                    list_price: property.purchase_price,
                    state: property.state,
                    hoa_monthly: property.hoa_monthly || 0,
                });
            }
        }
    };

    const handleChangeHomeClick = () => {
        // Scroll to property select field - try multiple selectors
        const propertySelect = document.querySelector('[name="property_id"]') ||
            document.querySelector('.ant-select-selector') ||
            document.querySelector('input[placeholder*="property" i]');
        if (propertySelect) {
            (propertySelect as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Focus the select after a short delay
            setTimeout(() => {
                try {
                    (propertySelect as HTMLElement).focus();
                } catch (e) {
                    // If focus fails, that's okay
                    console.log('Could not focus property select');
                }
            }, 300);
        } else {
            // Fallback: scroll to the form
            const formCard = document.querySelector('.ant-card');
            if (formCard) {
                formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    };

    const handleSaveSessionProfile = useCallback(() => {
        const values = form.getFieldsValue();

        // Validate required fields
        if (!values.monthly_income || values.monthly_income <= 0 || isNaN(values.monthly_income)) {
            message.error('Please fill in monthly income before saving baseline.');
            return;
        }
        if (!values.other_debts_monthly || values.other_debts_monthly < 0 || isNaN(values.other_debts_monthly)) {
            message.error('Please fill in other debts monthly before saving baseline.');
            return;
        }
        if (!values.down_payment_pct || values.down_payment_pct < 0 || values.down_payment_pct > 100 || isNaN(values.down_payment_pct)) {
            message.error('Please fill in down payment percentage before saving baseline.');
            return;
        }
        if (!values.risk_preference || !['conservative', 'neutral', 'aggressive'].includes(values.risk_preference)) {
            message.error('Please select a risk preference before saving baseline.');
            return;
        }

        // Save profile
        setSessionProfile({
            monthlyIncome: values.monthly_income,
            otherDebtsMonthly: values.other_debts_monthly,
            downPaymentPct: values.down_payment_pct,
            riskPreference: values.risk_preference,
        });
        setUsingSessionProfile(true);
        message.success('Saved as baseline for this session.');
    }, [form, message]);

    const handleApplySessionProfile = useCallback(() => {
        if (!sessionProfile) {
            message.warning('No baseline profile saved yet this session.');
            return;
        }

        // Apply profile values to form
        form.setFieldsValue({
            monthly_income: sessionProfile.monthlyIncome,
            other_debts_monthly: sessionProfile.otherDebtsMonthly,
            down_payment_pct: sessionProfile.downPaymentPct,
            risk_preference: sessionProfile.riskPreference,
        });
        setUsingSessionProfile(true);
    }, [sessionProfile, form, message]);

    const handleStressCheck = async () => {
        try {
            const values = await form.validateFields();

            const stressRequest: StressCheckRequest = buildStressRequestPayload(values);

            const request: SingleHomeAgentRequest = {
                stress_request: stressRequest,
                user_message: null, // Optional: can be added later if we want to support user questions
            };

            setLoading(true);
            setResponse(null);
            setLastRunStartedFromNL(false); // Form-only run

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/single-home-agent`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Request failed: ${res.status}`);
            }

            const data: SingleHomeAgentResponse = await res.json();
            setResponse(data);
        } catch (err: any) {
            console.error('Stress check failed:', err);
            message.error(err.message || 'Failed to run stress check');
        } finally {
            setLoading(false);
        }
    };

    // Handler for running the full Mortgage Agent from NL assistant
    const handleRunMortgageAgentFromNL = async () => {
        try {
            // Use the merged_request from NL assistant if available, otherwise use form values
            let values;
            if (nlAssistantResult?.merged_request) {
                // Merge NL assistant result with current form values
                const formValues = form.getFieldsValue();
                values = { ...formValues, ...nlAssistantResult.merged_request };
                // Update form to reflect merged values
                form.setFieldsValue(values);
            } else {
                values = await form.validateFields();
            }

            const stressRequest: StressCheckRequest = buildStressRequestPayload(values);

            const request: SingleHomeAgentRequest = {
                stress_request: stressRequest,
                user_message: null,
            };

            setLoading(true);
            setResponse(null);
            setLastRunStartedFromNL(true); // Run started from NL

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/single-home-agent`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Request failed: ${res.status}`);
            }

            const data: SingleHomeAgentResponse = await res.json();
            setResponse(data);

            // Scroll to results after a short delay
            setTimeout(() => {
                const stageTimeline = document.querySelector('[data-stage-timeline]');
                if (stageTimeline) {
                    stageTimeline.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 500);

            message.success('Analysis complete – see the Mortgage Agent workflow below.');
        } catch (err: any) {
            console.error('Mortgage Agent run failed:', err);
            message.error(err.message || 'Failed to run Mortgage Agent');
        } finally {
            setLoading(false);
        }
    };

    // Handler for preset scenario selection - auto-fills form and triggers stress check
    const handlePresetSelect = async (presetId: string) => {
        const preset = PRESET_SCENARIOS.find(p => p.id === presetId);
        if (!preset) {
            message.error('Preset scenario not found');
            return;
        }

        try {
            // Clear property_id if set, so manual values take effect
            form.setFieldsValue({
                property_id: null,
                ...preset.values,
            });

            // Trigger stress check automatically (form-only run)
            await handleStressCheck();
        } catch (err: any) {
            console.error('Failed to apply preset:', err);
            message.error('Failed to apply preset scenario');
        }
    };

    const handleFindSaferHomes = async () => {
        try {
            const values = await form.validateFields();

            // Validate required fields
            if (!values.monthly_income || !values.other_debts_monthly || !values.list_price) {
                message.warning('Please fill in monthly income, debts, and list price before searching for safer homes.');
                return;
            }

            // Get zip_code from stress result if available, otherwise from form values
            const zipCode = response?.stress_result?.home_snapshot?.zip_code || values.zip_code;
            if (!zipCode) {
                message.warning('Please provide a ZIP code to search for safer homes. You can add it to the form or it will be extracted from the stress check result.');
                return;
            }

            setSaferHomesLoading(true);
            setSaferHomesError(null);
            setSaferHomesResult(null);

            const stressRequest: StressCheckRequest = buildStressRequestPayload(values);
            // Ensure zip_code is included
            stressRequest.zip_code = zipCode;

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/safer-homes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stressRequest),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Request failed: ${res.status}`);
            }

            const data: SaferHomesResult = await res.json();
            setSaferHomesResult(data);
        } catch (err: any) {
            if (err?.errorFields) {
                setSaferHomesError('Please complete the required inputs before searching for safer homes.');
                return;
            }
            console.error('Find safer homes failed:', err);
            setSaferHomesError(err?.message || 'Failed to search for safer homes.');
            message.error('Failed to search for safer homes');
        } finally {
            setSaferHomesLoading(false);
        }
    };

    const handleAskAi = async () => {
        if (!nlQuestion.trim()) {
            message.warning('Please enter a question for the AI.');
            return;
        }

        try {
            setNlLoading(true);
            setNlError(null);
            setNlAnswer(null);

            const values = await form.validateFields();
            const stressRequest: StressCheckRequest = buildStressRequestPayload(values);

            const payload: SingleHomeAgentRequest = {
                stress_request: stressRequest,
                user_message: nlQuestion.trim(),
            };

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/single-home-agent`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Request failed: ${res.status}`);
            }

            const data: SingleHomeAgentResponse = await res.json();
            setNlAnswer(data);
        } catch (err: any) {
            if (err?.errorFields) {
                setNlError('Please complete the required inputs before asking the AI.');
                return;
            }
            console.error('Ask AI failed:', err);
            setNlError(err?.message || 'Failed to contact AI agent.');
            message.error('Failed to contact AI agent');
        } finally {
            setNlLoading(false);
        }
    };

    const handleNlAssistant = async () => {
        if (!nlAssistantText.trim()) {
            message.warning('Please enter your situation description.');
            return;
        }

        try {
            setNlAssistantLoading(true);
            setNlAssistantError(null);
            setNlAssistantResult(null);

            // Get current form values to send as current_request
            const currentValues = form.getFieldsValue();
            const currentRequest: Record<string, any> = {};

            // Map form fields to request format
            if (currentValues.monthly_income) {
                currentRequest.monthly_income = currentValues.monthly_income;
            }
            if (currentValues.other_debts_monthly) {
                currentRequest.other_debts_monthly = currentValues.other_debts_monthly;
            }
            if (currentValues.list_price) {
                currentRequest.list_price = currentValues.list_price;
            }
            if (currentValues.down_payment_pct) {
                // Convert percentage to decimal if needed
                currentRequest.down_payment_pct = currentValues.down_payment_pct / 100;
            }
            if (currentValues.zip_code) {
                currentRequest.zip_code = currentValues.zip_code;
            }
            if (currentValues.state) {
                currentRequest.state = currentValues.state;
            }
            if (currentValues.hoa_monthly) {
                currentRequest.hoa_monthly = currentValues.hoa_monthly;
            }
            if (currentValues.risk_preference) {
                currentRequest.risk_preference = currentValues.risk_preference;
            }

            const payload = {
                user_text: nlAssistantText.trim(),
                current_request: Object.keys(currentRequest).length > 0 ? currentRequest : undefined,
                conversation_history: nlConversation.length > 0 ? nlConversation : undefined,
            };

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/nl-to-stress-request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Request failed: ${res.status}`);
            }

            const data = await res.json();
            setNlAssistantResult(data);

            // Update conversation history from response (backend maintains single source of truth)
            if (data.conversation_history && Array.isArray(data.conversation_history)) {
                // Limit to last 10 messages (5 turns) on frontend as well
                const maxMessages = 10;
                const updatedHistory = data.conversation_history.length > maxMessages
                    ? data.conversation_history.slice(-maxMessages)
                    : data.conversation_history;
                setNlConversation(updatedHistory);
            }

            // Update form with merged_request
            if (data.merged_request) {
                const updates: Record<string, any> = {};
                if (data.merged_request.monthly_income !== undefined) {
                    updates.monthly_income = data.merged_request.monthly_income;
                }
                if (data.merged_request.other_debts_monthly !== undefined) {
                    updates.other_debts_monthly = data.merged_request.other_debts_monthly;
                }
                if (data.merged_request.list_price !== undefined) {
                    updates.list_price = data.merged_request.list_price;
                }
                if (data.merged_request.down_payment_pct !== undefined) {
                    // Convert decimal to percentage
                    updates.down_payment_pct = data.merged_request.down_payment_pct * 100;
                }
                if (data.merged_request.zip_code !== undefined) {
                    updates.zip_code = data.merged_request.zip_code;
                }
                if (data.merged_request.state !== undefined) {
                    updates.state = data.merged_request.state;
                }
                if (data.merged_request.hoa_monthly !== undefined) {
                    updates.hoa_monthly = data.merged_request.hoa_monthly;
                }
                if (data.merged_request.risk_preference !== undefined) {
                    updates.risk_preference = data.merged_request.risk_preference;
                }

                form.setFieldsValue(updates);
                message.success('Form updated with recognized fields');
            }

            // Clear the input field after successful submission
            setNlAssistantText('');
        } catch (err: any) {
            console.error('NL Assistant failed:', err);
            const errorMsg = err?.message || 'Sorry, I couldn\'t process that. Please try again or fill the form directly.';
            setNlAssistantError(errorMsg);
            message.error('Failed to process your request');

            // Don't wipe conversation on error - user can retry
        } finally {
            setNlAssistantLoading(false);
        }
    };

    // Helper function to apply scenario updates and re-run stress check
    const applyScenarioAndRun = async (updates: Partial<{ monthly_income?: number; list_price?: number }>) => {
        try {
            const currentValues = form.getFieldsValue();

            // Validate required fields before applying scenario
            if (updates.monthly_income !== undefined && (!currentValues.monthly_income || currentValues.monthly_income <= 0)) {
                message.warning('Please fill in monthly income before running scenarios.');
                return;
            }

            if (updates.list_price !== undefined && (!currentValues.list_price || currentValues.list_price <= 0)) {
                message.warning('Please fill in home listing price before running scenarios.');
                return;
            }

            // Apply updates to form
            const newValues = { ...currentValues, ...updates };
            form.setFieldsValue(newValues);

            // Trigger validation and re-run stress check
            await form.validateFields();
            await handleStressCheck();
        } catch (err: any) {
            // Validation errors are handled by form, but catch any other errors
            if (err.errorFields) {
                // Form validation error, already shown by Ant Design
                return;
            }
            console.error('Scenario application failed:', err);
        }
    };

    // Scenario handlers
    const handleIncomeMinus10Percent = () => {
        const currentIncome = form.getFieldValue('monthly_income');
        if (!currentIncome || currentIncome <= 0) {
            message.warning('Please fill in monthly income before running scenarios.');
            return;
        }
        const newIncome = Math.round(currentIncome * 0.9 * 100) / 100; // Round to 2 decimals
        applyScenarioAndRun({ monthly_income: newIncome });
    };

    const handlePriceMinus50k = () => {
        const currentPrice = form.getFieldValue('list_price');
        if (!currentPrice || currentPrice <= 0) {
            message.warning('Please fill in home listing price before running scenarios.');
            return;
        }
        const minPrice = 50000; // Minimum price threshold
        if (currentPrice <= minPrice) {
            message.warning(`Price must be greater than $${minPrice.toLocaleString()} to apply -$50k scenario.`);
            return;
        }
        const newPrice = Math.max(minPrice, currentPrice - 50000);
        // Clear property_id if set, so the manual price adjustment takes effect
        const currentValues = form.getFieldsValue();
        if (currentValues.property_id) {
            form.setFieldsValue({ property_id: null });
        }
        applyScenarioAndRun({ list_price: newPrice });
    };

    // Dispatcher for AI-suggested scenarios - reuses existing what-if handlers
    const handleSuggestedScenarioClick = (key: 'income_minus_10' | 'price_minus_50k') => {
        if (key === 'income_minus_10') {
            return handleIncomeMinus10Percent();
        }
        if (key === 'price_minus_50k') {
            return handlePriceMinus50k();
        }
    };

    const getStressBandColor = (band: string) => {
        switch (band) {
            case 'loose':
                return 'green';
            case 'ok':
                return 'blue';
            case 'tight':
                return 'orange';
            case 'high_risk':
                return 'red';
            default:
                return 'default';
        }
    };

    const getStressBandLabel = (band: string) => {
        switch (band) {
            case 'loose':
                return 'Loose';
            case 'ok':
                return 'OK';
            case 'tight':
                return 'Tight';
            case 'high_risk':
                return 'High Risk';
            default:
                return band;
        }
    };

    const getStressBandExplanation = (band: string, dtiRatio: number) => {
        switch (band) {
            case 'loose':
                return `DTI ratio is ${(dtiRatio * 100).toFixed(1)}%. This home is comfortably affordable.`;
            case 'ok':
                return `DTI ratio is ${(dtiRatio * 100).toFixed(1)}%. This home is within acceptable affordability range.`;
            case 'tight':
                return `DTI ratio is ${(dtiRatio * 100).toFixed(1)}%. This home may be stretching your budget.`;
            case 'high_risk':
                return `DTI ratio is ${(dtiRatio * 100).toFixed(1)}%. This home is likely unaffordable and poses high financial risk.`;
            default:
                return '';
        }
    };

    // Helper function to format duration (same as MortgageAssistantPage)
    const formatDuration = (value: number | null | undefined): string => {
        if (value === null || value === undefined) return 'N/A';
        if (value < 0.01) return '< 0.01 ms';
        if (value < 1) return value.toFixed(3) + ' ms';
        if (value < 1000) return value.toFixed(1) + ' ms';
        return (value / 1000).toFixed(2) + ' s';
    };

    // Helper function to extract local_cost_factors_source from agent_steps
    const getLocalCostFactorsSource = (stressResult: StressCheckResponse | null): string | null => {
        if (!stressResult) return null;

        // First check if it's directly on the response (if backend adds it later)
        if (stressResult.local_cost_factors_source) {
            return stressResult.local_cost_factors_source;
        }

        // Otherwise, try to extract from agent_steps
        if (stressResult.agent_steps) {
            const marketDataStep = stressResult.agent_steps.find(
                step => step.step_name === 'Market Data Fetch'
            );
            if (marketDataStep?.outputs && typeof marketDataStep.outputs === 'object') {
                const source = (marketDataStep.outputs as any).local_cost_factors_source;
                if (typeof source === 'string') {
                    return source;
                }
            }
        }

        return null;
    };

    // Helper function to format local cost assumptions as a readable string
    const formatLocalCostAssumptions = (stressResult: StressCheckResponse | null): string | null => {
        if (!stressResult) return null;

        const parts: string[] = [];

        if (stressResult.assumed_tax_rate_pct != null) {
            parts.push(`Tax est: ${stressResult.assumed_tax_rate_pct.toFixed(2)}%`);
        }

        if (stressResult.assumed_insurance_ratio_pct != null) {
            parts.push(`Insurance est: ${stressResult.assumed_insurance_ratio_pct.toFixed(2)}%`);
        }

        const source = getLocalCostFactorsSource(stressResult);
        if (source) {
            // Format source for display (e.g., "zip_override_90803" -> "ZIP override 90803", "state_default_CA" -> "State default CA")
            let displaySource = source;
            if (source === 'zip_override') {
                displaySource = 'ZIP override';
            } else if (source === 'state_default') {
                displaySource = 'State default';
            } else if (source === 'global_default') {
                displaySource = 'Default';
            } else if (source.startsWith('zip_override_')) {
                const zip = source.replace('zip_override_', '');
                displaySource = `ZIP override ${zip}`;
            } else if (source.startsWith('state_default_')) {
                const state = source.replace('state_default_', '');
                displaySource = `State default ${state}`;
            }
            parts.push(`Source: ${displaySource}`);
        }

        return parts.length > 0 ? parts.join(' · ') : null;
    };

    // Helper function to get status tag color
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'failed':
                return 'error';
            case 'in_progress':
                return 'processing';
            case 'pending':
                return 'default';
            default:
                return 'default';
        }
    };

    // Helper function to format JSON preview (truncated to ~150 chars)
    const formatJsonPreview = (obj: any, maxLength: number = 150): string => {
        if (!obj) return 'N/A';
        const str = JSON.stringify(obj, null, 2);
        return str.length > maxLength
            ? str.substring(0, maxLength) + '…'
            : str;
    };

    // Helper render functions for cleaner JSX
    const renderWalletCard = (response: SingleHomeAgentResponse) => {
        const monthlyIncome = response.stress_result.wallet_snapshot?.monthly_income || form.getFieldValue('monthly_income');
        const otherDebts = response.stress_result.wallet_snapshot?.other_debts_monthly || form.getFieldValue('other_debts_monthly');
        const minSafe = response.stress_result.wallet_snapshot?.safe_payment_band?.min_safe;
        const maxSafe = response.stress_result.wallet_snapshot?.safe_payment_band?.max_safe;
        const cashFlow = (monthlyIncome || 0) - response.stress_result.total_monthly_payment - (otherDebts || 0);

        return (
            <Card
                title="Your wallet"
                style={{ backgroundColor: '#1d1f23', marginBottom: '16px' }}
            >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>Monthly income:</Text>
                        <Title level={4} style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
                            {formatCurrency(monthlyIncome)}
                        </Title>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>Other debts monthly:</Text>
                        <Text strong style={{ fontSize: '16px' }}>{formatCurrency(otherDebts)}</Text>
                    </div>
                    <Divider style={{ margin: '16px 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>Safe payment range:</Text>
                        <Text strong style={{ color: '#52c41a', fontSize: '18px', fontWeight: 600 }}>
                            {formatCurrency(minSafe)} - {formatCurrency(maxSafe)}
                        </Text>
                    </div>
                    <Text type="secondary" style={{ fontSize: '11px', marginTop: '4px', display: 'block' }}>
                        (Based on your income, debts, and risk preference)
                    </Text>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>Cash flow after payment:</Text>
                        <Title
                            level={4}
                            style={{
                                margin: 0,
                                fontSize: '20px',
                                fontWeight: 600,
                                color: cashFlow >= 0 ? '#52c41a' : '#ff4d4f'
                            }}
                        >
                            {formatCurrency(cashFlow)}
                        </Title>
                    </div>
                    <Text type="secondary" style={{ fontSize: '11px', marginTop: '12px', display: 'block' }}>
                        From: Current profile / stress check
                    </Text>
                </Space>
            </Card>
        );
    };

    const renderTargetHomeCard = (response: SingleHomeAgentResponse) => {
        const propertyId = form.getFieldValue('property_id');
        const property = propertyId ? properties.find(p => p.id === propertyId) : null;
        const propertyName = property ? `${property.name}, ${property.city}` : 'Target home';
        const listPrice = response.stress_result.home_snapshot?.list_price || form.getFieldValue('list_price');
        const hoaMonthly = response.stress_result.home_snapshot?.hoa_monthly || form.getFieldValue('hoa_monthly') || 0;
        const zipCode = response.stress_result.home_snapshot?.zip_code;
        const state = response.stress_result.home_snapshot?.state || form.getFieldValue('state');

        return (
            <Card
                title="Target home"
                extra={
                    <Button
                        type="link"
                        size="small"
                        onClick={handleChangeHomeClick}
                        style={{ padding: 0 }}
                    >
                        Change home
                    </Button>
                }
                style={{ backgroundColor: '#1d1f23', marginBottom: '16px' }}
            >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div>
                        <Text strong style={{ fontSize: '16px' }}>{propertyName}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>Price:</Text>
                        <Title level={4} style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
                            {formatCurrency(listPrice)}
                        </Title>
                    </div>
                    {(zipCode || state) && (
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text type="secondary" style={{ fontSize: '13px' }}>Location:</Text>
                            <Text style={{ fontSize: '14px' }}>
                                {zipCode ? `${zipCode}` : ''}
                                {zipCode && state ? ', ' : ''}
                                {state || '—'}
                            </Text>
                        </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text type="secondary" style={{ fontSize: '13px' }}>HOA monthly:</Text>
                        <Text strong style={{ fontSize: '16px' }}>{formatCurrency(hoaMonthly)}</Text>
                    </div>
                    {formatLocalCostAssumptions(response.stress_result) && (
                        <>
                            <Divider style={{ margin: '12px 0' }} />
                            <div style={{ marginTop: '8px' }}>
                                <Text type="secondary" style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                    Local cost assumptions:
                                </Text>
                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                    {formatLocalCostAssumptions(response.stress_result)}
                                </Text>
                            </div>
                        </>
                    )}
                </Space>
            </Card>
        );
    };

    // Helper function to render NL Assistant card
    const renderNlAssistantCard = () => {
        const recognizedFields: string[] = [];
        if (nlAssistantResult?.partial_request) {
            const partial = nlAssistantResult.partial_request;
            if (partial.monthly_income) {
                recognizedFields.push(`Income ≈ ${formatCurrency(partial.monthly_income)}/month`);
            }
            if (partial.list_price) {
                recognizedFields.push(`Home price ≈ ${formatCurrency(partial.list_price)}`);
            }
            if (partial.down_payment_pct !== undefined) {
                recognizedFields.push(`Down payment ≈ ${(partial.down_payment_pct * 100).toFixed(0)}%`);
            }
            if (partial.zip_code) {
                recognizedFields.push(`ZIP ${partial.zip_code}`);
            }
            if (partial.state) {
                recognizedFields.push(`State ${partial.state}`);
            }
        }

        // Show last 5 messages (or fewer) in the chat transcript
        const displayMessages = nlConversation.slice(-5);

        // Build requirement checklist from missing_required_fields
        const missingFields = nlAssistantResult?.missing_required_fields || [];
        const hasEnoughInfo = nlAssistantResult?.router_decision === 'have_enough_info';

        // Field label mapping (backend uses income_monthly, but frontend uses monthly_income)
        const fieldLabelMap: Record<string, string> = {
            'monthly_income': 'Income',
            'income_monthly': 'Income', // Backend field name
            'list_price': 'Home price',
            'down_payment_pct': 'Down payment',
            'zip_code': 'ZIP code',
            'state': 'State',
        };

        const requiredFields = ['monthly_income', 'list_price', 'down_payment_pct', 'zip_code', 'state'];
        const checklistItems = requiredFields.map(field => {
            // Check both frontend and backend field names
            const missing = missingFields.includes(field) || missingFields.includes(field === 'monthly_income' ? 'income_monthly' : field);
            return {
                field,
                label: fieldLabelMap[field] || field,
                missing,
            };
        });

        return (
            <Card
                data-nl-assistant-card
                title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>Talk to the agent (English only)</span>
                        {nlConversation.length > 0 && (
                            <Button
                                type="text"
                                size="small"
                                onClick={() => {
                                    setNlConversation([]);
                                    setNlAssistantResult(null);
                                    setNlAssistantError(null);
                                }}
                                style={{ fontSize: '12px', padding: '0 8px' }}
                            >
                                Clear
                            </Button>
                        )}
                    </div>
                }
                style={{ marginTop: '16px', marginBottom: '16px' }}
            >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '12px' }}>
                        Describe your situation in plain English, I'll help fill the form on the left. You can also use the presets and form on the left.
                    </Text>

                    {/* Chat transcript */}
                    {displayMessages.length > 0 && (
                        <div
                            style={{
                                marginBottom: '16px',
                                padding: '12px',
                                backgroundColor: '#1d1f23',
                                borderRadius: '4px',
                                maxHeight: '300px',
                                overflowY: 'auto',
                            }}
                        >
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                {displayMessages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            display: 'flex',
                                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                            marginBottom: '8px',
                                        }}
                                    >
                                        <div
                                            style={{
                                                maxWidth: '75%',
                                                padding: '8px 12px',
                                                borderRadius: '8px',
                                                backgroundColor: msg.role === 'user' ? '#1890ff' : '#2d2f34',
                                                color: msg.role === 'user' ? '#fff' : '#e6e6e6',
                                            }}
                                        >
                                            <Text
                                                strong
                                                style={{
                                                    fontSize: '11px',
                                                    display: 'block',
                                                    marginBottom: '4px',
                                                    opacity: 0.8,
                                                }}
                                            >
                                                {msg.role === 'user' ? 'You' : 'Agent'}
                                            </Text>
                                            <Text style={{ fontSize: '13px', whiteSpace: 'pre-wrap' }}>
                                                {msg.content}
                                            </Text>
                                        </div>
                                    </div>
                                ))}
                            </Space>
                        </div>
                    )}

                    <TextArea
                        data-nl-assistant-textarea
                        value={nlAssistantText}
                        onChange={(e) => setNlAssistantText(e.target.value)}
                        rows={3}
                        placeholder="I make $150k a year and I'm looking at a $750k home in 90803 with 20% down."
                        autoSize={{ minRows: 3, maxRows: 4 }}
                        disabled={nlAssistantLoading}
                        onPressEnter={(e) => {
                            if (e.ctrlKey || e.metaKey) {
                                handleNlAssistant();
                            }
                        }}
                    />
                    {nlAssistantError && (
                        <Alert
                            type="error"
                            message={nlAssistantError}
                            showIcon
                            style={{ marginTop: '12px' }}
                            closable
                            onClose={() => setNlAssistantError(null)}
                        />
                    )}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                        <Button
                            type="default"
                            onClick={handleNlAssistant}
                            loading={nlAssistantLoading}
                            disabled={nlAssistantLoading || !nlAssistantText.trim()}
                        >
                            Let AI fill for me
                        </Button>
                    </div>
                    {recognizedFields.length > 0 && (
                        <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#24272c', borderRadius: '4px' }}>
                            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                                Understood:
                            </Text>
                            <Space wrap>
                                {recognizedFields.map((field, idx) => (
                                    <Tag key={idx} color="blue">{field}</Tag>
                                ))}
                            </Space>
                        </div>
                    )}

                    {/* Requirement Checklist and Primary CTA */}
                    {nlAssistantResult && (
                        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#24272c', borderRadius: '4px' }}>
                            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                                Requirements:
                            </Text>
                            <Space wrap style={{ marginBottom: '12px' }}>
                                {checklistItems.map((item, idx) => (
                                    <Tag
                                        key={idx}
                                        color={item.missing ? 'error' : 'success'}
                                        style={{ textDecoration: item.missing ? 'none' : 'line-through', opacity: item.missing ? 1 : 0.6 }}
                                    >
                                        {item.label}
                                    </Tag>
                                ))}
                            </Space>

                            <Button
                                type="primary"
                                size="large"
                                block
                                onClick={handleRunMortgageAgentFromNL}
                                loading={loading}
                                disabled={!hasEnoughInfo || loading}
                                title={!hasEnoughInfo ? `We still need ${missingFields.map(f => fieldLabelMap[f] || fieldLabelMap[f === 'income_monthly' ? 'monthly_income' : f] || f).join(', ')} to run the Mortgage Agent.` : undefined}
                            >
                                {loading ? 'Running Mortgage Agent...' : 'Run Mortgage Agent on this plan'}
                            </Button>

                            {!hasEnoughInfo && missingFields.length > 0 && (
                                <Text type="secondary" style={{ fontSize: '11px', display: 'block', marginTop: '8px', textAlign: 'center' }}>
                                    We still need {missingFields.map(f => fieldLabelMap[f] || fieldLabelMap[f === 'income_monthly' ? 'monthly_income' : f] || f).join(', ')} to run the Mortgage Agent.
                                </Text>
                            )}
                        </div>
                    )}
                </Space>
            </Card>
        );
    };

    // Helper function to render AI Answer card (short summary + recommendations)
    const renderAiAnswerCard = (agentResult: SingleHomeAgentResponse | null) => {
        if (!agentResult) return null;

        const { borrower_narrative, recommended_actions, stress_result } = agentResult;
        const stress_band = stress_result?.stress_band;
        const total_monthly_payment = stress_result?.total_monthly_payment;
        const dti_ratio = stress_result?.dti_ratio;

        // Parse AI answer data (handle both direct fields and potential JSON strings)
        const parsedAnswer = parseAiAnswer({
            borrower_narrative,
            recommended_actions,
        });

        // Use parsed data, fallback to direct fields if parsing didn't extract anything
        const borrowerNarrative = parsedAnswer.borrowerNarrative || borrower_narrative || null;
        const recommendedActions = parsedAnswer.recommendedActions || recommended_actions || null;

        // Determine if we have structured content or need to show raw text
        const hasStructuredContent = borrowerNarrative || (Array.isArray(recommendedActions) && recommendedActions.length > 0);
        const showRawText = !hasStructuredContent && parsedAnswer.rawText;

        return (
            <Card
                title="AI Assistant — What does this stress result mean?"
                size="small"
                style={{ marginTop: 16 }}
            >
                {/* Top summary line: stress band + monthly payment + DTI */}
                {stress_result && (
                    <Paragraph style={{ marginBottom: 12 }}>
                        <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                            This is an explanation of your current stress check result, not a new calculation.
                        </Text>
                        <Text strong style={{ fontSize: 16 }}>Summary: </Text>
                        <Text strong style={{ fontSize: 16 }}>
                            Stress band: {stress_band ? getStressBandLabel(stress_band) : '—'} · Total payment:{' '}
                            {formatCurrency(total_monthly_payment, 2, 2)} · DTI:{' '}
                            {formatPercent(dti_ratio, 1)}
                        </Text>
                    </Paragraph>
                )}

                {/* Borrower narrative: normal paragraph formatting */}
                {borrowerNarrative && (
                    <div style={{ marginBottom: 16 }}>
                        <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 8 }}>
                            Borrower narrative:
                        </Text>
                        <Paragraph
                            style={{
                                fontSize: 16,
                                lineHeight: 1.7,
                                marginBottom: 0,
                                color: '#e6e6e6'
                            }}
                        >
                            {borrowerNarrative}
                        </Paragraph>
                    </div>
                )}

                {/* Recommended actions: bullet list */}
                {Array.isArray(recommendedActions) && recommendedActions.length > 0 && (
                    <div>
                        <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 8 }}>
                            Recommended actions:
                        </Text>
                        <ul style={{
                            marginTop: 0,
                            paddingLeft: 24,
                            marginBottom: 0,
                            fontSize: 16,
                            lineHeight: 1.7
                        }}>
                            {recommendedActions.map((item, idx) => (
                                <li key={idx} style={{ marginBottom: 8, color: '#e6e6e6' }}>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Fallback: show raw text if no structured content */}
                {showRawText && (
                    <Paragraph
                        style={{
                            fontSize: 16,
                            lineHeight: 1.7,
                            marginBottom: 0,
                            color: '#e6e6e6',
                            whiteSpace: 'pre-wrap'
                        }}
                    >
                        {parsedAnswer.rawText}
                    </Paragraph>
                )}

                {/* Empty state */}
                {!hasStructuredContent && !showRawText && (
                    <Text type="secondary" style={{ fontSize: 15 }}>
                        AI answer not available yet.
                    </Text>
                )}
            </Card>
        );
    };

    // Helper function to render collapsible AI Explanation section
    const renderAiExplanationSection = (agentResult: SingleHomeAgentResponse | null) => {
        if (!agentResult) return null;

        const fullText = agentResult.stress_result?.llm_explanation || null;

        if (!fullText) return null;

        return (
            <Card
                size="small"
                style={{ marginTop: 16 }}
                title="AI Assistant — What does this stress result mean?"
                extra={
                    <Button type="link" onClick={() => setShowFullExplanation(v => !v)} style={{ padding: 0 }}>
                        {showFullExplanation ? 'Hide details' : 'Show details'}
                    </Button>
                }
            >
                {showFullExplanation ? (
                    <>
                        <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
                            This is an explanation of your current stress check result, not a new calculation.
                        </Text>
                        <Paragraph style={{ fontSize: 14, whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                            {fullText}
                        </Paragraph>
                    </>
                ) : (
                    <Paragraph style={{ fontSize: 13, color: '#999', marginBottom: 0 }}>
                        Detailed explanation of how the AI interpreted your profile and this home.
                    </Paragraph>
                )}
            </Card>
        );
    };

    // Helper function to format risk flag codes to human-readable labels
    const formatRiskFlagLabel = (flag: string): string => {
        const flagMap: Record<string, string> = {
            'high_dti': 'High DTI',
            'very_high_dti': 'Very High DTI',
            'high_risk_band': 'High Risk Band',
            'tight_band': 'Tight Band',
            'payment_above_safe_band': 'Payment Above Safe Band',
            'payment_way_above_safe_band': 'Payment Way Above Safe Band',
            'negative_cashflow': 'Negative Cash Flow',
            'very_low_cashflow_buffer': 'Very Low Cash Flow Buffer',
            'very_high_ltv': 'Very High LTV',
            'high_ltv': 'High LTV',
            'low_down_payment': 'Low Down Payment',
            'below_standard_down_payment': 'Below Standard Down Payment',
            'unlikely_approval': 'Unlikely Approval',
            'borderline_approval': 'Borderline Approval',
            'affordability_gap': 'Affordability Gap',
            'strong_income': 'Strong Income',
        };
        return flagMap[flag] || flag.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    };

    // Helper function to format approval score reason codes to human-readable labels
    const formatApprovalReason = (reason: string): string => {
        const reasonMap: Record<string, string> = {
            'high_dti': 'High DTI',
            'very_high_ltv': 'Very high LTV',
            'strong_income': 'Strong income',
        };

        // Return mapped label if exists, otherwise capitalize the raw string
        if (reasonMap[reason]) {
            return reasonMap[reason];
        }

        // Fallback: convert snake_case to Title Case
        return reason
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    };

    // Helper function to get approval bucket label
    const getApprovalBucketLabel = (bucket: 'likely' | 'borderline' | 'unlikely'): string => {
        switch (bucket) {
            case 'likely':
                return 'Likely to be approved';
            case 'borderline':
                return 'Borderline';
            case 'unlikely':
                return 'Unlikely to be approved';
            default:
                return bucket;
        }
    };

    // Helper function to get approval score color
    const getApprovalScoreColor = (bucket: 'likely' | 'borderline' | 'unlikely'): string => {
        switch (bucket) {
            case 'likely':
                return '#52c41a'; // green
            case 'borderline':
                return '#faad14'; // orange
            case 'unlikely':
                return '#ff4d4f'; // red
            default:
                return '#d9d9d9'; // default gray
        }
    };

    const renderApprovalScoreCard = (response: SingleHomeAgentResponse) => {
        const approvalScore = response.stress_result.approval_score;

        // Don't render if approval_score is missing
        if (!approvalScore) {
            return null;
        }

        const { score, bucket, reasons } = approvalScore;
        const bucketLabel = getApprovalBucketLabel(bucket);
        const scoreColor = getApprovalScoreColor(bucket);

        return (
            <Card
                title={`Approval score · ${bucketLabel}`}
                style={{ marginTop: '16px', marginBottom: '16px' }}
            >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {/* Main score display */}
                    <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                        <Title
                            level={2}
                            style={{
                                margin: 0,
                                fontSize: '48px',
                                fontWeight: 700,
                                color: scoreColor,
                            }}
                        >
                            {Math.round(score)} / 100
                        </Title>
                    </div>

                    {/* Subtext explanation */}
                    <Text type="secondary" style={{ fontSize: '13px', display: 'block', textAlign: 'center' }}>
                        Heuristic approval estimate based on DTI, LTV and stress band. This is not a final underwriting decision.
                    </Text>

                    {/* Reasons tags */}
                    {reasons && reasons.length > 0 && (
                        <div style={{ marginTop: '12px' }}>
                            <Space wrap size="small" style={{ justifyContent: 'center', width: '100%' }}>
                                {reasons.slice(0, 3).map((reason, idx) => (
                                    <Tag key={idx} color="default">
                                        {formatApprovalReason(reason)}
                                    </Tag>
                                ))}
                            </Space>
                        </div>
                    )}
                </Space>
            </Card>
        );
    };

    const renderRiskAssessmentCard = (response: SingleHomeAgentResponse) => {
        const riskAssessment = response?.risk_assessment || response?.stress_result?.risk_assessment;

        // Don't render if risk_assessment is missing or has no flags
        if (!riskAssessment || !riskAssessment.risk_flags || riskAssessment.risk_flags.length === 0) {
            return null;
        }

        const isHard = riskAssessment.hard_block;
        const isSoft = !riskAssessment.hard_block && riskAssessment.soft_warning;

        return (
            <Card
                title="Risk flags & guardrails"
                style={{ marginTop: '16px', marginBottom: '16px', background: '#24272c' }}
            >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {/* Warning message */}
                    <Alert
                        message={
                            isHard
                                ? 'The agent believes this scenario is high risk. Please proceed with caution.'
                                : isSoft
                                    ? 'There are some caution flags you should pay attention to.'
                                    : 'No major risk flags detected.'
                        }
                        type={isHard ? 'error' : isSoft ? 'warning' : 'info'}
                        showIcon
                        style={{ marginBottom: '8px' }}
                    />

                    {/* Risk flags tags */}
                    <div>
                        <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                            Risk indicators:
                        </Text>
                        <Space wrap size="small" style={{ width: '100%' }}>
                            {riskAssessment.risk_flags.slice(0, 6).map((flag, idx) => (
                                <Tag key={idx} color={isHard ? 'red' : 'gold'}>
                                    {formatRiskFlagLabel(flag)}
                                </Tag>
                            ))}
                            {riskAssessment.risk_flags.length > 6 && (
                                <Tag color="default">
                                    +{riskAssessment.risk_flags.length - 6} more
                                </Tag>
                            )}
                        </Space>
                    </div>
                </Space>
            </Card>
        );
    };

    const renderNextStepsSection = (
        response: SingleHomeAgentResponse | null,
        nlAnswer: SingleHomeAgentResponse | null,
        saferHomesResult: SaferHomesResult | null,
        saferHomesLoading: boolean,
        saferHomesError: string | null,
        handleFindSaferHomes: () => void,
        setSaferHomesError: (error: string | null) => void,
        nlQuestion: string,
        setNlQuestion: (value: string) => void,
        nlLoading: boolean,
        nlError: string | null,
        handleAskAi: () => void,
    ) => {
        if (!response) return null;

        // Get safety_upgrade from response or nlAnswer
        const safetyUpgrade = response?.safety_upgrade || nlAnswer?.safety_upgrade || null;
        const band = response.stress_result.stress_band;
        const isLoose = band === 'loose';
        const isOk = band === 'ok';
        const isTight = band === 'tight' || band === 'high_risk';

        // Get ZIP code for safer homes search
        const zipCode = response?.stress_result?.home_snapshot?.zip_code || form.getFieldValue('zip_code');

        // Next steps card: single unified background with three subsections
        // (safety upgrade summary, safer homes list, Ask AI), to make this feel
        // like one coherent agent "action panel" instead of three separate cards.
        return (
            <Card
                title="Next steps · What the agent suggests"
                style={{ backgroundColor: '#1d1f23', marginTop: '16px', marginBottom: '16px' }}
                bodyStyle={{ padding: 16 }}
            >
                {/* A. Safety Upgrade Summary */}
                {safetyUpgrade ? (
                    <div>
                        <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
                            When stress is Tight or High Risk, the agent automatically searches for safer options or ways to fix the plan.
                        </Text>
                        {safetyUpgrade.primary_suggestion && (
                            <>
                                <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 8 }}>
                                    {safetyUpgrade.primary_suggestion.title}
                                </Text>
                                {safetyUpgrade.primary_suggestion.delta_dti !== null &&
                                    safetyUpgrade.primary_suggestion.delta_dti !== undefined && (
                                        <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                                            Best safer option reduces your DTI by ~{formatPercent(Math.abs(safetyUpgrade.primary_suggestion.delta_dti), 1)} percentage points.
                                        </Text>
                                    )}
                                {safetyUpgrade.primary_suggestion.notes &&
                                    safetyUpgrade.primary_suggestion.notes.length > 0 && (
                                        <ul style={{
                                            marginTop: 8,
                                            paddingLeft: 24,
                                            marginBottom: 0,
                                            fontSize: 14,
                                            lineHeight: 1.6
                                        }}>
                                            {safetyUpgrade.primary_suggestion.notes.map((note, idx) => (
                                                <li key={idx} style={{ marginBottom: 4, color: '#d9d9d9' }}>
                                                    {note}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                            </>
                        )}
                        {safetyUpgrade.mortgage_programs_checked && (
                            <Paragraph type="secondary" style={{ marginTop: 12 }}>
                                <Text strong>Mortgage programs (MCP):</Text>{" "}
                                Checked assistance programs for this profile
                                {typeof safetyUpgrade.mortgage_programs_hit_count === "number" &&
                                    safetyUpgrade.mortgage_programs_hit_count >= 0 && (
                                        <>
                                            , found {safetyUpgrade.mortgage_programs_hit_count} match
                                            {safetyUpgrade.mortgage_programs_hit_count === 1 ? "" : "es"}
                                        </>
                                    )}
                                .
                            </Paragraph>
                        )}
                    </div>
                ) : (isLoose || isOk) ? (
                    <div>
                        <Text type="secondary" style={{ fontSize: 13, display: 'block' }}>
                            This plan already looks comfortable. The agent doesn't need a safety upgrade for this case.
                        </Text>
                    </div>
                ) : null}

                {/* Divider between sections if Safety Upgrade section is visible */}
                {((safetyUpgrade || (isLoose || isOk)) && (
                    <Divider style={{ margin: '16px 0', borderColor: '#303030' }} />
                ))}

                {/* Mortgage Programs Section - only show for tight/high_risk */}
                {isTight && (() => {
                    const programs = response?.mortgage_programs_preview || nlAnswer?.mortgage_programs_preview || null;
                    if (!programs || programs.length === 0) {
                        return null;
                    }
                    return (
                        <div style={{ marginTop: 16 }}>
                            <Title level={5} style={{ color: '#fff', marginBottom: 8 }}>
                                Mortgage assistance programs
                            </Title>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                These are example programs that might help improve affordability or approval odds.
                                Always confirm details with a licensed loan officer.
                            </Text>
                            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {programs.map((p) => (
                                    <div
                                        key={p.program_id}
                                        style={{
                                            padding: 12,
                                            borderRadius: 8,
                                            backgroundColor: '#1d1f23',
                                            border: '1px solid #303339',
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                            <Text style={{ color: '#fff', fontWeight: 500 }}>{p.name}</Text>
                                            {p.state && (
                                                <Tag color="geekblue" style={{ borderRadius: 999 }}>
                                                    {p.state}
                                                </Tag>
                                            )}
                                        </div>
                                        {p.summary && (
                                            <Text style={{ fontSize: 12, color: '#b0b3b8' }}>
                                                {p.summary}
                                            </Text>
                                        )}
                                        <div style={{ marginTop: 6, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                            {p.max_dti != null && (
                                                <Tag color="gold" style={{ borderRadius: 999 }}>
                                                    Max DTI ~ {(p.max_dti * 100).toFixed(0)}%
                                                </Tag>
                                            )}
                                            {p.tags && p.tags.slice(0, 3).map((tag) => (
                                                <Tag key={tag} color="default" style={{ borderRadius: 999 }}>
                                                    {tag}
                                                </Tag>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })()}

                {/* Divider before Safer homes if Mortgage Programs section is visible */}
                {isTight && (response?.mortgage_programs_preview || nlAnswer?.mortgage_programs_preview) &&
                    (response?.mortgage_programs_preview?.length || 0) + (nlAnswer?.mortgage_programs_preview?.length || 0) > 0 && (
                        <Divider style={{ margin: '16px 0', borderColor: '#303030' }} />
                    )}

                {/* Strategy Lab Section - between Safety Upgrade and Safer homes */}
                {(() => {
                    const strategyLab = response?.strategy_lab || nlAnswer?.strategy_lab || null;
                    if (!strategyLab || !strategyLab.scenarios || strategyLab.scenarios.length === 0) {
                        return null;
                    }

                    const { baseline_stress_band, baseline_dti, baseline_total_payment, baseline_approval_score } = strategyLab;

                    return (
                        <>
                            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #303030' }}>
                                <Title level={5} style={{ marginBottom: 8, color: '#fff' }}>
                                    Strategy Lab · What if we tweak the plan
                                </Title>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>
                                    The agent ran a few alternative plans (price, down payment, risk preference) to see how your stress could improve.
                                </Text>

                                {/* Baseline 行 */}
                                <div style={{ marginTop: 12, marginBottom: 8 }}>
                                    <Text strong style={{ color: '#fff' }}>Current plan</Text>
                                    <div style={{ fontSize: 12, color: '#aaaaaa', marginTop: 4, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                        <span>
                                            Band:{' '}
                                            {baseline_stress_band ? (
                                                <Tag color={getStressBandColor(baseline_stress_band)} style={{ margin: 0 }}>
                                                    {getStressBandLabel(baseline_stress_band)}
                                                </Tag>
                                            ) : (
                                                <Text>—</Text>
                                            )}
                                        </span>
                                        <span>DTI: {baseline_dti != null ? formatPercent(baseline_dti, 1) : '—'}</span>
                                        <span>Payment: {baseline_total_payment != null ? formatCurrency(baseline_total_payment, 2, 2) : '—'}</span>
                                        {baseline_approval_score && (
                                            <span>Approval: {baseline_approval_score.bucket}</span>
                                        )}
                                    </div>
                                </div>

                                {/* Strategy Lab Summary Text */}
                                {(() => {
                                    const summaryText = getStrategyLabSummaryText(strategyLab);
                                    if (!summaryText) {
                                        return null;
                                    }
                                    return (
                                        <div style={{ marginTop: 8, marginBottom: 12 }}>
                                            <Text type="secondary" style={{ fontSize: 12, color: '#999', fontStyle: 'italic' }}>
                                                {summaryText}
                                            </Text>
                                        </div>
                                    );
                                })()}

                                {/* Scenarios 列表，最多显示 3 个 */}
                                <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 12 }}>
                                    {strategyLab.scenarios.slice(0, 3).map((scenario) => (
                                        <Card
                                            key={scenario.id}
                                            size="small"
                                            style={{ background: '#1d1f23', borderRadius: 8, border: '1px solid #303030' }}
                                            bodyStyle={{ padding: 12 }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                                <div style={{ flex: 1 }}>
                                                    <Text strong style={{ color: '#fff' }}>{scenario.title}</Text>
                                                    {scenario.description && (
                                                        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>{scenario.description}</div>
                                                    )}
                                                </div>
                                                {scenario.stress_band && (
                                                    <Tag color={getStressBandColor(scenario.stress_band)} style={{ marginLeft: 8 }}>
                                                        {getStressBandLabel(scenario.stress_band)}
                                                    </Tag>
                                                )}
                                            </div>
                                            <div style={{ fontSize: 12, color: '#ccc' }}>
                                                {scenario.dti_ratio != null && (
                                                    <span>DTI: {formatPercent(scenario.dti_ratio, 1)} · </span>
                                                )}
                                                {scenario.total_payment != null && (
                                                    <span>Payment: {formatCurrency(scenario.total_payment, 2, 2)}</span>
                                                )}
                                                {scenario.price_delta_pct != null && (
                                                    <>
                                                        {' · '}
                                                        <span>
                                                            Price: {scenario.price_delta_pct > 0 ? '+' : ''}
                                                            {formatPercent(scenario.price_delta_pct, 1)}
                                                        </span>
                                                    </>
                                                )}
                                                {scenario.approval_score && (
                                                    <>
                                                        {' · '}
                                                        <span>Approval: {scenario.approval_score.bucket}</span>
                                                    </>
                                                )}
                                            </div>
                                        </Card>
                                    ))}
                                </Space>
                            </div>
                            <Divider style={{ margin: '16px 0', borderColor: '#303030' }} />
                        </>
                    );
                })()}

                {/* B. Safer homes in this ZIP */}
                <div>
                    <Title level={5} style={{ marginBottom: 12 }}>Safer homes in this ZIP</Title>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>
                        These are mock listings we stress-tested to see which ones look safer for your wallet.
                    </Text>
                    <Button
                        type="primary"
                        onClick={handleFindSaferHomes}
                        loading={saferHomesLoading}
                        disabled={!zipCode || saferHomesLoading}
                        icon={<BankOutlined />}
                    >
                        Find safer homes in this ZIP
                    </Button>
                    {!zipCode && (
                        <Text type="secondary" style={{ display: 'block', marginTop: '8px', fontSize: '12px', color: '#ff4d4f' }}>
                            Please provide a ZIP code to search for safer homes.
                        </Text>
                    )}

                    {saferHomesError && (
                        <Alert
                            message={saferHomesError}
                            type="error"
                            showIcon
                            closable
                            onClose={() => setSaferHomesError(null)}
                            style={{ marginTop: 12 }}
                        />
                    )}

                    {saferHomesResult && (
                        <div style={{ marginTop: 16 }}>
                            {saferHomesResult.candidates.length === 0 ? (
                                <Alert
                                    message="No safer homes found in our mock data"
                                    description="No clearly safer homes found in this ZIP with current settings."
                                    type="info"
                                    showIcon
                                />
                            ) : (
                                <div>
                                    <Text strong style={{ fontSize: '14px', display: 'block', marginBottom: '12px' }}>
                                        Found {saferHomesResult.candidates.length} safer home{saferHomesResult.candidates.length > 1 ? 's' : ''}:
                                    </Text>
                                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                        {saferHomesResult.candidates.slice(0, 3).map((candidate, idx) => (
                                            <div
                                                key={idx}
                                                style={{
                                                    padding: '12px',
                                                    border: '1px solid #303030',
                                                    borderRadius: '4px',
                                                    backgroundColor: 'transparent'
                                                }}
                                            >
                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    <div>
                                                        <Text strong style={{ fontSize: '14px' }}>
                                                            {candidate.listing.title}
                                                        </Text>
                                                        <Text type="secondary" style={{ marginLeft: '8px' }}>
                                                            {candidate.listing.city}, {candidate.listing.state}
                                                        </Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                        <div>
                                                            <Text>Price: </Text>
                                                            <Text strong>{formatCurrency(candidate.listing.list_price, 0, 0)}</Text>
                                                            {candidate.listing.hoa_monthly && candidate.listing.hoa_monthly > 0 && (
                                                                <Text type="secondary" style={{ marginLeft: '8px' }}>
                                                                    HOA: {formatCurrency(candidate.listing.hoa_monthly, 2, 2)}/mo
                                                                </Text>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <Tag color={candidate.stress_band === 'loose' ? 'green' : candidate.stress_band === 'ok' ? 'blue' : candidate.stress_band === 'tight' ? 'orange' : 'red'}>
                                                                Band: {candidate.stress_band.toUpperCase()}
                                                            </Tag>
                                                            {candidate.dti_ratio != null && (
                                                                <Tag style={{ marginLeft: '4px' }}>
                                                                    DTI: {formatPercent(candidate.dti_ratio, 1)}
                                                                </Tag>
                                                            )}
                                                        </div>
                                                    </div>
                                                    {candidate.comment && (
                                                        <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
                                                            {candidate.comment}
                                                        </Text>
                                                    )}
                                                </Space>
                                            </div>
                                        ))}
                                    </Space>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <Divider style={{ margin: '16px 0', borderColor: '#303030' }} />

                {/* C. Ask the AI about this plan */}
                <div>
                    <Title level={5} style={{ marginBottom: 12 }}>Ask the AI about this plan</Title>
                    <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '12px' }}>
                        Ask follow-up questions about this result.
                        <br />
                        Examples: "Could I afford 800k instead?", "What if I put 10% more down?"
                    </Text>
                    <TextArea
                        value={nlQuestion}
                        onChange={(e) => setNlQuestion(e.target.value)}
                        rows={3}
                        placeholder="I make $6k/month. Is this $750k home too tight for me?"
                        autoSize={{ minRows: 3, maxRows: 4 }}
                        disabled={nlLoading || !response}
                    />
                    {nlError && (
                        <Alert
                            type="error"
                            message={nlError}
                            showIcon
                            style={{ marginTop: '12px' }}
                        />
                    )}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                        <Button
                            type="primary"
                            onClick={handleAskAi}
                            loading={nlLoading}
                            disabled={nlLoading || !nlQuestion.trim() || !response}
                        >
                            Ask AI
                        </Button>
                    </div>
                </div>
            </Card>
        );
    };

    const renderStressBandSection = (response: SingleHomeAgentResponse) => {
        const band = response.stress_result.stress_band;
        const dtiRatio = response.stress_result.dti_ratio;
        const isLoose = band === 'loose';
        const isOk = band === 'ok';
        const isTight = band === 'tight' || band === 'high_risk';

        return (
            <Card
                title="Stress level for this home"
                style={{ backgroundColor: '#24272c', marginTop: '16px', marginBottom: '16px' }}
            >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Row gutter={0} style={{ marginBottom: '20px' }}>
                        <Col span={8}>
                            <div
                                style={{
                                    padding: '16px',
                                    textAlign: 'center',
                                    backgroundColor: isLoose ? '#52c41a' : '#1a1a1a',
                                    border: isLoose ? '3px solid #52c41a' : '1px solid #303030',
                                    borderRight: 'none',
                                    borderTopLeftRadius: '4px',
                                    borderBottomLeftRadius: '4px',
                                    fontWeight: isLoose ? 'bold' : 'normal',
                                    color: isLoose ? '#fff' : '#d9d9d9',
                                    fontSize: isLoose ? '18px' : '16px',
                                }}
                            >
                                Loose
                            </div>
                        </Col>
                        <Col span={8}>
                            <div
                                style={{
                                    padding: '16px',
                                    textAlign: 'center',
                                    backgroundColor: isOk ? '#1890ff' : '#1a1a1a',
                                    border: isOk ? '3px solid #1890ff' : '1px solid #303030',
                                    borderRight: 'none',
                                    fontWeight: isOk ? 'bold' : 'normal',
                                    color: isOk ? '#fff' : '#d9d9d9',
                                    fontSize: isOk ? '18px' : '16px',
                                }}
                            >
                                OK
                            </div>
                        </Col>
                        <Col span={8}>
                            <div
                                style={{
                                    padding: '16px',
                                    textAlign: 'center',
                                    backgroundColor: isTight ? '#ff4d4f' : '#1a1a1a',
                                    border: isTight ? '3px solid #ff4d4f' : '1px solid #303030',
                                    borderTopRightRadius: '4px',
                                    borderBottomRightRadius: '4px',
                                    fontWeight: isTight ? 'bold' : 'normal',
                                    color: isTight ? '#fff' : '#d9d9d9',
                                    fontSize: isTight ? '18px' : '16px',
                                }}
                            >
                                {band === 'high_risk' ? 'Tight / High risk' : 'Tight'}
                            </div>
                        </Col>
                    </Row>
                    <div style={{ marginBottom: '12px' }}>
                        <Text strong style={{ fontSize: '18px', display: 'block', marginBottom: '8px' }}>
                            This home looks: {getStressBandLabel(band)} for your current income.
                        </Text>
                        <Text style={{ fontSize: '16px', fontWeight: 600, color: '#1890ff', display: 'block', marginBottom: '4px' }}>
                            DTI: {formatPercent(dtiRatio, 1)} • Total monthly payment: {formatCurrency(response.stress_result.total_monthly_payment, 2, 2)}
                        </Text>
                    </div>
                    <Paragraph style={{ marginBottom: 0, fontSize: '15px' }}>
                        {getStressBandExplanation(band, dtiRatio)}
                    </Paragraph>
                    {(response.stress_result.assumed_tax_rate_pct != null || response.stress_result.assumed_insurance_ratio_pct != null) && (
                        <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}>
                            Includes taxes, insurance and HOA estimated from local ZIP data.
                        </Text>
                    )}
                    {response.stress_result.hard_warning && (
                        <Alert
                            message="Warning"
                            description={response.stress_result.hard_warning}
                            type="error"
                            showIcon
                            icon={<ExclamationCircleOutlined />}
                            style={{ marginTop: '12px' }}
                        />
                    )}
                </Space>
            </Card>
        );
    };

    const renderAgentStepsTable = (steps: AgentStep[]) => (
        <Table
            style={{ background: '#0f0f0f', borderRadius: '8px' }}
            dataSource={steps}
            rowKey="step_id"
            pagination={false}
            size="small"
            columns={[
                {
                    title: 'Step',
                    dataIndex: 'step_name',
                    key: 'step',
                    render: (text: string, record: AgentStep) => (
                        <Text strong>{text || record.step_id}</Text>
                    ),
                },
                {
                    title: 'Status',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                        <Tag color={getStatusColor(status)}>
                            {status.toUpperCase()}
                        </Tag>
                    ),
                    align: 'center',
                },
                {
                    title: 'Duration',
                    dataIndex: 'duration_ms',
                    key: 'duration',
                    render: (value: number | null) => formatDuration(value),
                    align: 'right',
                },
                {
                    title: 'Timestamp',
                    dataIndex: 'timestamp',
                    key: 'timestamp',
                    render: (text: string) => (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            {text}
                        </Text>
                    ),
                },
            ]}
            expandable={{
                expandedRowRender: (step: AgentStep) => (
                    <div
                        style={{
                            padding: '12px',
                            backgroundColor: '#141414',
                            borderRadius: '8px',
                            border: '1px solid #2a2a2a',
                        }}
                    >
                        <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                            <Text type="secondary">Step ID: </Text>
                            <Text code>{step.step_id}</Text>
                        </Paragraph>
                        {step.inputs && (
                            <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                                <Text type="secondary" strong>Inputs:</Text>
                                <pre
                                    style={{
                                        marginTop: '4px',
                                        padding: '8px',
                                        backgroundColor: '#1f1f1f',
                                        color: '#f0f0f0',
                                        borderRadius: '4px',
                                        border: '1px solid #333',
                                        fontSize: '11px',
                                        overflow: 'auto',
                                        maxHeight: '150px',
                                    }}
                                >
                                    {formatJsonPreview(step.inputs, 150)}
                                </pre>
                            </Paragraph>
                        )}
                        {step.outputs && (
                            <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                                <Text type="secondary" strong>Outputs:</Text>
                                <pre
                                    style={{
                                        marginTop: '4px',
                                        padding: '8px',
                                        backgroundColor: '#1f1f1f',
                                        color: '#f0f0f0',
                                        borderRadius: '4px',
                                        border: '1px solid #333',
                                        fontSize: '11px',
                                        overflow: 'auto',
                                        maxHeight: '150px',
                                    }}
                                >
                                    {formatJsonPreview(step.outputs, 150)}
                                </pre>
                            </Paragraph>
                        )}
                        {step.error && (
                            <Alert
                                message="Error"
                                description={step.error}
                                type="error"
                                style={{ marginTop: '8px', fontSize: '12px' }}
                            />
                        )}
                    </div>
                ),
            }}
        />
    );

    // ========================================
    // Agent Stage Timeline Types and Functions
    // ========================================

    type AgentStageKey =
        | 'input'
        | 'stress_check'
        | 'risk_approval'
        | 'safety_upgrade'
        | 'mcp_programs'
        | 'strategy_lab'
        | 'llm_explanation';

    interface AgentStageSummary {
        key: AgentStageKey;
        label: string;
        description: string;
        status: 'not_run' | 'running' | 'completed' | 'skipped';
        hasGuardrailWarning?: boolean;
    }

    // Build agent stage timeline from SingleHomeAgentResponse
    const buildAgentStageTimeline = (
        response: SingleHomeAgentResponse | null,
        nlAnswer: SingleHomeAgentResponse | null
    ): AgentStageSummary[] => {
        if (!response?.stress_result) {
            // No stress result means workflow hasn't started
            return [
                { key: 'input', label: 'Input', description: 'User inputs', status: 'completed' },
                { key: 'stress_check', label: 'Stress Check', description: 'Calculate affordability', status: 'not_run' },
                { key: 'risk_approval', label: 'Risk & Approval', description: 'Assess risk and approval score', status: 'not_run' },
                { key: 'safety_upgrade', label: 'Safety Upgrade', description: 'Suggest safer alternatives', status: 'not_run' },
                { key: 'mcp_programs', label: 'Mortgage Programs', description: 'Search assistance programs', status: 'not_run' },
                { key: 'strategy_lab', label: 'Strategy Lab', description: 'Explore alternative scenarios', status: 'not_run' },
                { key: 'llm_explanation', label: 'LLM Explanation', description: 'Generate borrower narrative', status: 'not_run' },
            ];
        }

        const stressResult = response.stress_result;
        const safetyUpgrade = response?.safety_upgrade || nlAnswer?.safety_upgrade || null;
        const mortgagePrograms = response?.mortgage_programs_preview || nlAnswer?.mortgage_programs_preview || null;
        const strategyLab = response?.strategy_lab || nlAnswer?.strategy_lab || null;
        const riskAssessment = response?.risk_assessment || response?.stress_result?.risk_assessment || null;
        const borrowerNarrative = response?.borrower_narrative || nlAnswer?.borrower_narrative || null;

        const stages: AgentStageSummary[] = [];

        // 1. Input stage - always completed if we have a stress result
        stages.push({
            key: 'input',
            label: 'Input',
            description: 'User inputs',
            status: 'completed',
        });

        // 2. Stress Check stage - completed if stress_result exists
        stages.push({
            key: 'stress_check',
            label: 'Stress Check',
            description: 'Calculate affordability',
            status: stressResult ? 'completed' : 'not_run',
        });

        // 3. Risk & Approval stage - completed if risk_assessment or approval_score exists
        const hasRiskOrApproval = riskAssessment || stressResult?.approval_score;
        let hasGuardrailWarning = false;
        if (riskAssessment) {
            hasGuardrailWarning = riskAssessment.hard_block || riskAssessment.soft_warning || false;
        }
        stages.push({
            key: 'risk_approval',
            label: 'Risk & Approval',
            description: 'Assess risk and approval score',
            status: hasRiskOrApproval ? 'completed' : 'not_run',
            hasGuardrailWarning,
        });

        // 4. Safety Upgrade stage - completed if safety_upgrade exists and baseline_is_tight_or_worse is true, otherwise skipped
        let safetyUpgradeStatus: 'completed' | 'skipped' | 'not_run' = 'not_run';
        if (safetyUpgrade) {
            safetyUpgradeStatus = safetyUpgrade.baseline_is_tight_or_worse ? 'completed' : 'skipped';
        }
        stages.push({
            key: 'safety_upgrade',
            label: 'Safety Upgrade',
            description: 'Suggest safer alternatives',
            status: safetyUpgradeStatus,
        });

        // 5. MCP Programs stage - completed if mortgage_programs_preview exists with entries, otherwise skipped
        let mcpProgramsStatus: 'completed' | 'skipped' | 'not_run' = 'not_run';
        if (mortgagePrograms && mortgagePrograms.length > 0) {
            mcpProgramsStatus = 'completed';
        } else if (safetyUpgrade?.mortgage_programs_checked !== undefined) {
            // MCP was checked but returned no results
            mcpProgramsStatus = 'skipped';
        }
        stages.push({
            key: 'mcp_programs',
            label: 'Mortgage Programs',
            description: 'Search assistance programs',
            status: mcpProgramsStatus,
        });

        // 6. Strategy Lab stage - completed if strategy_lab exists with scenarios, otherwise skipped
        let strategyLabStatus: 'completed' | 'skipped' | 'not_run' = 'not_run';
        if (strategyLab) {
            strategyLabStatus = strategyLab.scenarios && strategyLab.scenarios.length > 0 ? 'completed' : 'skipped';
        }
        stages.push({
            key: 'strategy_lab',
            label: 'Strategy Lab',
            description: 'Explore alternative scenarios',
            status: strategyLabStatus,
        });

        // 7. LLM Explanation stage - completed if borrower_narrative exists
        stages.push({
            key: 'llm_explanation',
            label: 'LLM Explanation',
            description: 'Generate borrower narrative',
            status: borrowerNarrative ? 'completed' : 'not_run',
        });

        return stages;
    };

    // Render agent stage timeline UI
    const renderAgentStageTimeline = (
        response: SingleHomeAgentResponse | null,
        nlAnswer: SingleHomeAgentResponse | null
    ) => {
        const stages = buildAgentStageTimeline(response, nlAnswer);

        if (!response?.stress_result) {
            // No stress result - show empty state
            return (
                <Card style={{ marginTop: '16px', marginBottom: '16px' }}>
                    <div style={{ padding: '16px', textAlign: 'center' }}>
                        <Text type="secondary">Run a stress check to see the agent workflow.</Text>
                    </div>
                </Card>
            );
        }

        return (
            <Card data-stage-timeline style={{ marginTop: '16px', marginBottom: '16px' }}>
                <div style={{ marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                        <Title level={5} style={{ margin: 0 }}>
                            Stage Timeline · LangGraph Workflow
                        </Title>
                        <Tag color="geekblue">Overview</Tag>
                        {lastRunStartedFromNL ? (
                            <Tag color="cyan">Started from conversation</Tag>
                        ) : response ? (
                            <Tag color="default">Started from form</Tag>
                        ) : null}
                    </div>
                    <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
                        This shows the Mortgage Agent workflow for your current plan. High-level view of the LangGraph workflow stages: input → stress check → risk & approval → safety upgrade → programs → strategy lab → LLM explanation.
                        {lastRunStartedFromNL && (
                            <span style={{ display: 'block', marginTop: '4px', fontStyle: 'italic' }}>
                                This Mortgage Agent run was initiated from your natural-language conversation.
                            </span>
                        )}
                    </Text>
                </div>
                <div
                    style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '8px',
                        alignItems: 'flex-start',
                        marginBottom: '12px',
                    }}
                >
                    {stages.map((stage, index) => {
                        const isLast = index === stages.length - 1;
                        const statusColors: Record<string, string> = {
                            completed: '#52c41a', // green
                            skipped: '#8c8c8c', // gray
                            not_run: '#434343', // dark gray
                            running: '#1890ff', // blue
                        };
                        const statusLabels: Record<string, string> = {
                            completed: 'Completed',
                            skipped: 'Skipped',
                            not_run: 'Not run',
                            running: 'Running',
                        };
                        const borderColor =
                            stage.status === 'completed' ? statusColors.completed :
                                stage.status === 'skipped' ? statusColors.skipped :
                                    '#2a2a2a';

                        return (
                            <React.Fragment key={stage.key}>
                                {/* Stage Card */}
                                <div
                                    style={{
                                        flex: '0 0 auto',
                                        padding: '12px',
                                        backgroundColor: '#141414',
                                        borderRadius: '8px',
                                        border: `1px solid ${borderColor}`,
                                        position: 'relative',
                                        minWidth: '130px',
                                        maxWidth: '150px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '6px',
                                    }}
                                >
                                    {stage.hasGuardrailWarning && (
                                        <div
                                            style={{
                                                position: 'absolute',
                                                top: '8px',
                                                right: '8px',
                                                width: '10px',
                                                height: '10px',
                                                borderRadius: '50%',
                                                backgroundColor: '#ff4d4f',
                                                border: '2px solid #141414',
                                                boxShadow: '0 0 4px rgba(255, 77, 79, 0.8)',
                                            }}
                                            title="Guardrails: high risk / hard block"
                                        />
                                    )}
                                    <Text
                                        strong
                                        style={{
                                            fontSize: '13px',
                                            color: stage.status === 'completed' ? statusColors.completed :
                                                stage.status === 'skipped' ? statusColors.skipped : '#aaa',
                                        }}
                                    >
                                        {stage.label}
                                    </Text>
                                    <Text
                                        type="secondary"
                                        style={{
                                            fontSize: '11px',
                                            lineHeight: '1.4',
                                            marginBottom: '2px',
                                        }}
                                    >
                                        {stage.description}
                                    </Text>
                                    <Tag
                                        color={
                                            stage.status === 'completed'
                                                ? 'success'
                                                : stage.status === 'skipped'
                                                    ? 'default'
                                                    : 'default'
                                        }
                                        style={{
                                            fontSize: '10px',
                                            alignSelf: 'flex-start',
                                            marginTop: 'auto',
                                        }}
                                    >
                                        {statusLabels[stage.status]}
                                    </Tag>
                                </div>
                                {/* Arrow connector (except for last item) */}
                                {!isLast && (
                                    <div
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: '20px',
                                            marginTop: '50px',
                                            color:
                                                stage.status === 'completed' && stages[index + 1]?.status === 'completed'
                                                    ? statusColors.completed
                                                    : '#434343',
                                            fontSize: '16px',
                                        }}
                                    >
                                        →
                                    </div>
                                )}
                            </React.Fragment>
                        );
                    })}
                </div>
            </Card>
        );
    };

    // Helper function to render combined Agent Steps (Stress check + Ask AI)
    const renderCombinedAgentSteps = (
        stressResult?: StressCheckResponse | null,
        nlAnswer?: SingleHomeAgentResponse | null,
        safetyUpgrade?: SafetyUpgradeResult | null,
    ) => {
        const stressSteps = stressResult?.agent_steps ?? [];
        const askAiSteps = nlAnswer?.stress_result?.agent_steps ?? [];

        if (!stressSteps.length && !askAiSteps.length && !safetyUpgrade?.mortgage_programs_checked) {
            return null;
        }

        return (
            <Card style={{ marginTop: '16px' }}>
                <Collapse defaultActiveKey={[]} ghost>
                    <Panel
                        header={
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                    <span style={{ fontSize: '16px', fontWeight: 500 }}>
                                        Agent Steps · LangGraph Orchestrated Workflow
                                    </span>
                                    <Tag color="geekblue">LangGraph</Tag>
                                </div>
                                <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
                                    This view shows the step-by-step Mortgage Agent workflow (stress check → safety upgrade → explanation), orchestrated by LangGraph.
                                </Text>
                            </div>
                        }
                        key="combined-agent-steps"
                    >
                        {loading || nlLoading ? (
                            <div style={{ padding: '16px' }}>
                                <Skeleton active paragraph={{ rows: 3 }} />
                                <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}>
                                    Thinking…
                                </Text>
                            </div>
                        ) : (
                            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                {/* Stress check steps */}
                                {stressSteps.length > 0 && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: '8px' }}>
                                            Stress check steps
                                        </Text>
                                        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
                                            {renderAgentStepsTable(stressSteps)}
                                        </div>
                                    </div>
                                )}

                                {/* Ask AI steps */}
                                {askAiSteps.length > 0 && (
                                    <div>
                                        {stressSteps.length > 0 && (
                                            <Divider style={{ margin: '16px 0' }} />
                                        )}
                                        <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: '8px' }}>
                                            Ask AI steps
                                        </Text>
                                        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
                                            {renderAgentStepsTable(askAiSteps)}
                                        </div>
                                    </div>
                                )}

                                {/* External tools (MCP) */}
                                {safetyUpgrade?.mortgage_programs_checked && (
                                    <>
                                        {(stressSteps.length > 0 || askAiSteps.length > 0) && (
                                            <Divider style={{ margin: '16px 0' }} />
                                        )}
                                        <Title level={5} style={{ marginTop: 24, color: "rgba(255,255,255,0.85)" }}>
                                            External tools
                                        </Title>
                                        <Table
                                            size="small"
                                            pagination={false}
                                            rowKey="key"
                                            style={{ background: '#0f0f0f', borderRadius: '8px' }}
                                            columns={[
                                                {
                                                    title: "Step",
                                                    dataIndex: "step",
                                                    key: "step",
                                                    render: (text: string) => (
                                                        <Text strong>{text}</Text>
                                                    ),
                                                },
                                                {
                                                    title: "Status",
                                                    dataIndex: "status",
                                                    key: "status",
                                                    render: (status: string) => (
                                                        <Tag color={getStatusColor(status)}>
                                                            {status.toUpperCase()}
                                                        </Tag>
                                                    ),
                                                    align: 'center',
                                                },
                                                {
                                                    title: "Duration",
                                                    dataIndex: "duration",
                                                    key: "duration",
                                                    render: (value: string) => (
                                                        <Text type="secondary">{value}</Text>
                                                    ),
                                                    align: 'right',
                                                },
                                                {
                                                    title: "Timestamp",
                                                    dataIndex: "timestamp",
                                                    key: "timestamp",
                                                    render: (text: string) => (
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            {text}
                                                        </Text>
                                                    ),
                                                },
                                            ]}
                                            dataSource={[
                                                {
                                                    key: "mcp_mortgage_programs",
                                                    step: "Mortgage programs lookup (MCP Server)",
                                                    status: "completed",
                                                    duration: "—",
                                                    timestamp: "via LangGraph MCP node",
                                                },
                                            ]}
                                        />
                                    </>
                                )}

                                {/* Empty state */}
                                {stressSteps.length === 0 && askAiSteps.length === 0 && !safetyUpgrade?.mortgage_programs_checked && (
                                    <div style={{ padding: '16px', textAlign: 'center' }}>
                                        <Text type="secondary">No agent steps available</Text>
                                    </div>
                                )}
                            </Space>
                        )}
                    </Panel>
                </Collapse>
            </Card>
        );
    };

    return (
        <div style={{ padding: '24px' }}>
            <Title level={2}>
                <BankOutlined /> Single Home Stress · powered by Mortgage Agent
            </Title>
            <Paragraph>
                Evaluate whether a specific home is affordable for your financial situation using the Mortgage Agent.
            </Paragraph>

            <Row gutter={24}>
                {/* Left Column: Input Form - Narrower (30-35% on desktop) */}
                <Col xs={24} lg={8}>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        {/* Preset Scenarios Selector */}
                        <Card title="Demo Presets" size="small">
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                                    Select a preset to auto-fill the form and run a stress check:
                                </Text>
                                <Select
                                    placeholder="Choose a preset scenario..."
                                    style={{ width: '100%' }}
                                    onChange={handlePresetSelect}
                                    disabled={loading}
                                >
                                    {PRESET_SCENARIOS.map((preset) => (
                                        <Select.Option key={preset.id} value={preset.id}>
                                            <div>
                                                <div style={{ fontWeight: 500 }}>{preset.name}</div>
                                                <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                                                    {preset.description}
                                                </div>
                                            </div>
                                        </Select.Option>
                                    ))}
                                </Select>
                            </Space>
                        </Card>

                        <Card title="Input Parameters">
                            <Form
                                form={form}
                                layout="vertical"
                                initialValues={{
                                    down_payment_pct: 20,
                                    risk_preference: 'neutral',
                                    hoa_monthly: 0,
                                }}
                            >
                                <Form.Item
                                    label="Property"
                                    name="property_id"
                                    tooltip="Select a property or enter custom details below"
                                >
                                    <Select
                                        placeholder="Select a property"
                                        allowClear
                                        loading={loadingProperties}
                                        onChange={handlePropertyChange}
                                        showSearch
                                        optionFilterProp="children"
                                    >
                                        {properties.map((prop) => (
                                            <Select.Option key={prop.id} value={prop.id}>
                                                {prop.city}, {prop.state} - {prop.name} (${prop.purchase_price.toLocaleString()})
                                            </Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>

                                <Form.Item
                                    label="Home Listing Price"
                                    name="list_price"
                                    rules={[{ required: true, message: 'Please enter listing price' }]}
                                >
                                    <InputNumber
                                        style={{ width: '100%' }}
                                        prefix="$"
                                        min={0}
                                        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                        parser={(value) => parseFloat(value!.replace(/\$\s?|(,*)/g, '')) || 0 as any}
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="State"
                                    name="state"
                                >
                                    <Select placeholder="Select state" allowClear>
                                        <Select.Option value="CA">California</Select.Option>
                                        <Select.Option value="WA">Washington</Select.Option>
                                        <Select.Option value="TX">Texas</Select.Option>
                                        <Select.Option value="OR">Oregon</Select.Option>
                                        <Select.Option value="NY">New York</Select.Option>
                                        <Select.Option value="FL">Florida</Select.Option>
                                    </Select>
                                </Form.Item>

                                <Form.Item
                                    label="ZIP Code (Optional)"
                                    name="zip_code"
                                    tooltip="ZIP code helps estimate local tax and insurance rates. Required for finding safer homes nearby."
                                >
                                    <Input
                                        placeholder="e.g., 90803"
                                        maxLength={5}
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="Monthly Income"
                                    name="monthly_income"
                                    rules={[{ required: true, message: 'Please enter monthly income' }]}
                                >
                                    <InputNumber
                                        style={{ width: '100%' }}
                                        prefix="$"
                                        min={0}
                                        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                        parser={(value) => parseFloat(value!.replace(/\$\s?|(,*)/g, '')) || 0 as any}
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="Other Debts per Month"
                                    name="other_debts_monthly"
                                    rules={[{ required: true, message: 'Please enter monthly debts' }]}
                                >
                                    <InputNumber
                                        style={{ width: '100%' }}
                                        prefix="$"
                                        min={0}
                                        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                        parser={(value) => parseFloat(value!.replace(/\$\s?|(,*)/g, '')) || 0 as any}
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="Down Payment %"
                                    name="down_payment_pct"
                                    rules={[{ required: true, message: 'Please enter down payment percentage' }]}
                                >
                                    <InputNumber
                                        style={{ width: '100%' }}
                                        min={0}
                                        max={100}
                                        suffix="%"
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="HOA Monthly (Optional)"
                                    name="hoa_monthly"
                                >
                                    <InputNumber
                                        style={{ width: '100%' }}
                                        prefix="$"
                                        min={0}
                                        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                        parser={(value) => parseFloat(value!.replace(/\$\s?|(,*)/g, '')) || 0 as any}
                                    />
                                </Form.Item>

                                <Form.Item
                                    label="Risk Preference"
                                    name="risk_preference"
                                >
                                    <Radio.Group>
                                        <Radio value="conservative">Conservative</Radio>
                                        <Radio value="neutral">Neutral</Radio>
                                        <Radio value="aggressive">Aggressive</Radio>
                                    </Radio.Group>
                                </Form.Item>

                                <Divider style={{ margin: '16px 0' }} />

                                <Form.Item>
                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                        <Button
                                            type="default"
                                            size="small"
                                            onClick={handleSaveSessionProfile}
                                            block
                                        >
                                            Save as baseline (this session)
                                        </Button>
                                        <Button
                                            type="default"
                                            size="small"
                                            onClick={handleApplySessionProfile}
                                            disabled={!sessionProfile}
                                            block
                                        >
                                            Apply baseline for this session
                                        </Button>
                                        {!sessionProfile && (
                                            <Text type="secondary" style={{ fontSize: '12px', display: 'block', textAlign: 'center' }}>
                                                No baseline saved yet this session
                                            </Text>
                                        )}
                                        {sessionProfile && (
                                            <div style={{ textAlign: 'center' }}>
                                                {usingSessionProfile ? (
                                                    <Tag color="success" style={{ fontSize: '11px' }}>
                                                        Using session baseline
                                                    </Tag>
                                                ) : (
                                                    <Tag color="default" style={{ fontSize: '11px' }}>
                                                        Baseline saved
                                                    </Tag>
                                                )}
                                            </div>
                                        )}
                                    </Space>
                                </Form.Item>

                                <Form.Item>
                                    <Button
                                        type="primary"
                                        size="large"
                                        onClick={handleStressCheck}
                                        loading={loading}
                                        block
                                    >
                                        Quick stress-only run
                                    </Button>
                                </Form.Item>
                            </Form>
                        </Card>
                    </Space>
                </Col>

                {/* Right Column: Results Dashboard - Wider (65-70% on desktop) */}
                <Col xs={24} lg={16}>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        {/* NL Assistant Card - Help fill the form (always visible) */}
                        {renderNlAssistantCard()}

                        {!response && !loading ? (
                            <Card>
                                <Alert
                                    message="Run the Mortgage Agent to see results here"
                                    description="Fill in the form on the left or use the conversation assistant, then click 'Run Mortgage Agent on this plan' to evaluate affordability."
                                    type="info"
                                    showIcon
                                />
                            </Card>
                        ) : response ? (
                            <>
                                {/* Top Row: Your Wallet + Target Home */}
                                <Row gutter={16}>
                                    <Col xs={24} sm={12}>
                                        {renderWalletCard(response)}
                                    </Col>
                                    <Col xs={24} sm={12}>
                                        {renderTargetHomeCard(response)}
                                    </Col>
                                </Row>

                                {/* Stress Band Bar */}
                                {renderStressBandSection(response)}

                                {/* Approval Score Card */}
                                {renderApprovalScoreCard(response)}

                                {/* Risk Assessment Card */}
                                {renderRiskAssessmentCard(response)}

                                {/* What-if Scenarios */}
                                <Card
                                    title="What-if Scenarios"
                                    style={{ marginTop: '16px', marginBottom: '16px' }}
                                >
                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                        <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                                            Quickly see how different scenarios affect your stress level.
                                        </Text>
                                        <Space wrap>
                                            <Button
                                                type="dashed"
                                                size="small"
                                                onClick={handleIncomeMinus10Percent}
                                                disabled={loading}
                                            >
                                                -10% income
                                            </Button>
                                            <Button
                                                type="dashed"
                                                size="small"
                                                onClick={handlePriceMinus50k}
                                                disabled={loading}
                                            >
                                                -$50k price
                                            </Button>
                                        </Space>
                                        {/* AI Suggested Next Steps - inline with What-if */}
                                        {response.stress_result.recommended_scenarios && response.stress_result.recommended_scenarios.length > 0 && (
                                            <>
                                                <Divider style={{ margin: '12px 0' }} />
                                                <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
                                                    AI suggested scenarios:
                                                </Text>
                                                <Space wrap>
                                                    {response.stress_result.recommended_scenarios.map((s) => (
                                                        <Button
                                                            key={s.id}
                                                            size="small"
                                                            onClick={() => handleSuggestedScenarioClick(s.scenario_key)}
                                                            disabled={loading}
                                                        >
                                                            {s.title}
                                                        </Button>
                                                    ))}
                                                </Space>
                                                {response.stress_result.recommended_scenarios.some((s) => s.reason) && (
                                                    <ul style={{ paddingLeft: 20, marginTop: 8, marginBottom: 0 }}>
                                                        {response.stress_result.recommended_scenarios.map((s) =>
                                                            s.reason ? (
                                                                <li key={s.id}>
                                                                    <Text type="secondary" style={{ fontSize: '12px' }}>{s.reason}</Text>
                                                                </li>
                                                            ) : null
                                                        )}
                                                    </ul>
                                                )}
                                            </>
                                        )}
                                    </Space>
                                </Card>

                                {/* Payment Breakdown */}
                                <Card
                                    title="Payment Breakdown"
                                    style={{ marginTop: '16px', marginBottom: '16px' }}
                                >
                                    <Row gutter={16}>
                                        <Col span={12}>
                                            <div style={{ marginBottom: '8px' }}>
                                                <Text type="secondary" style={{ fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                                                    Total Monthly Payment
                                                </Text>
                                                <Title level={2} style={{ margin: 0, fontSize: '32px', fontWeight: 700, color: '#1890ff' }}>
                                                    {formatCurrency(response.stress_result.total_monthly_payment, 2, 2)}
                                                </Title>
                                            </div>
                                        </Col>
                                        <Col span={12}>
                                            <Statistic
                                                title="DTI Ratio"
                                                value={response.stress_result.dti_ratio * 100}
                                                suffix="%"
                                                precision={1}
                                                valueStyle={{ fontSize: '24px', fontWeight: 600 }}
                                            />
                                        </Col>
                                    </Row>
                                    <Divider />
                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Text>Principal & Interest:</Text>
                                            <Text strong>${response.stress_result.principal_interest_payment.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Text>Tax, Insurance & HOA:</Text>
                                            <Text strong>${response.stress_result.estimated_tax_ins_hoa.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
                                        </div>
                                        {response.stress_result.home_snapshot.hoa_monthly > 0 && (
                                            <div style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: 16 }}>
                                                <Text type="secondary">HOA:</Text>
                                                <Text type="secondary">${response.stress_result.home_snapshot.hoa_monthly.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
                                            </div>
                                        )}
                                        {response.stress_result.assumed_interest_rate_pct != null && (
                                            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    Assumptions: rate {response.stress_result.assumed_interest_rate_pct.toFixed(2)}%,
                                                    tax {response.stress_result.assumed_tax_rate_pct?.toFixed(2) ?? '--'}%,
                                                    insurance {response.stress_result.assumed_insurance_ratio_pct?.toFixed(2) ?? '--'}%.
                                                </Text>
                                            </div>
                                        )}
                                    </Space>
                                </Card>

                                {/* Next steps · What the agent suggests */}
                                {renderNextStepsSection(
                                    response,
                                    nlAnswer,
                                    saferHomesResult,
                                    saferHomesLoading,
                                    saferHomesError,
                                    handleFindSaferHomes,
                                    setSaferHomesError,
                                    nlQuestion,
                                    setNlQuestion,
                                    nlLoading,
                                    nlError,
                                    handleAskAi,
                                )}

                                {/* AI Answer / AI Explanation - Show AI Answer if Ask AI was used, otherwise show AI Explanation */}
                                {nlAnswer ? (
                                    /* When Ask AI has been used, show AI Answer card only */
                                    renderAiAnswerCard(nlAnswer)
                                ) : response ? (
                                    /* When no Ask AI result, show AI Explanation from stress check */
                                    renderAiExplanationSection(response)
                                ) : null}
                            </>
                        ) : null}

                        {/* Agent Stage Timeline - High-level workflow overview */}
                        {renderAgentStageTimeline(response, nlAnswer)}

                        {/* Combined Agent Steps - Stress check + Ask AI */}
                        {renderCombinedAgentSteps(
                            response?.stress_result,
                            nlAnswer,
                            response?.safety_upgrade || nlAnswer?.safety_upgrade || null
                        )}
                    </Space>
                </Col>
            </Row>
            <style>{`
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};

