import type { ReplayScenarioStep } from './simulationReplaySteps';

/** Shared shape for JSON + Role D generated Add-Car replay scenarios. */
export type AddCarReplayScenario = {
    id: string;
    role: string;
    title: string;
    subtitle: string;
    risk: string;
    placeholder?: boolean;
    placeholder_note?: string;
    turns: ReplayScenarioStep[];
    /** When true, autoplay stops after a system turn with `action_ready` (if reached before last step). */
    stopOnActionReady?: boolean;
};
