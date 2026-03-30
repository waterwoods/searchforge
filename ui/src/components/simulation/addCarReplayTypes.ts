/** Shared shape for JSON + Role D generated Add-Car replay scenarios. */
export type AddCarReplayScenario = {
    id: string;
    role: string;
    title: string;
    subtitle: string;
    risk: string;
    placeholder?: boolean;
    placeholder_note?: string;
    turns: Array<{ text: string }>;
};
