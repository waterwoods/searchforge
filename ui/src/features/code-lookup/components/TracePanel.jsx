import React from 'react';
import useStore from '../store';
import './TracePanel.css';

const TracePanel = () => {
    const { actionLogEvents, trace } = useStore();

    // If we have action log events, display them
    if (actionLogEvents && actionLogEvents.length > 0) {
        return (
            <div className="trace-panel">
                <h3>Action Log</h3>
                <div className="action-log-content">
                    {actionLogEvents.map((event, index) => (
                        <div key={index} className="action-log-event">
                            <div className="event-header">
                                <span className="event-type">{event.event || 'Action'}</span>
                                {event.step && <span className="event-step">Step {event.step}</span>}
                            </div>

                            {event.tool && (
                                <div className="event-tool">
                                    <strong>Tool:</strong> {event.tool}
                                </div>
                            )}

                            {event.observation_summary && (
                                <div className="event-observation">
                                    <strong>Observation:</strong> {event.observation_summary}
                                </div>
                            )}

                            {event.cost && (
                                <div className="event-cost">
                                    <strong>Cost:</strong>
                                    <pre>{JSON.stringify(event.cost, null, 2)}</pre>
                                </div>
                            )}

                            {event.tokens && (
                                <div className="event-tokens">
                                    <strong>Tokens:</strong>
                                    <pre>{JSON.stringify(event.tokens, null, 2)}</pre>
                                </div>
                            )}

                            {event.args_redacted && (
                                <div className="event-args">
                                    <strong>Arguments:</strong>
                                    <pre>{JSON.stringify(event.args_redacted, null, 2)}</pre>
                                </div>
                            )}

                            {event.evidence && (
                                <div className="event-evidence">
                                    <strong>Evidence:</strong>
                                    <pre>{JSON.stringify(event.evidence, null, 2)}</pre>
                                </div>
                            )}

                            {event.timestamp && (
                                <div className="event-timestamp">
                                    <small>{new Date(event.timestamp).toLocaleTimeString()}</small>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // Fallback to original trace display if no action log events but we have trace data
    if (trace && trace.plan) {
        const { plan, verdict } = trace;

        return (
            <div className="trace-panel">
                <h3>Execution Trace</h3>

                <div className="trace-content">
                    <div className="trace-section">
                        <h4>Goal</h4>
                        <p className="trace-goal">{plan.goal || 'N/A'}</p>
                    </div>

                    <div className="trace-section">
                        <h4>Execution Steps</h4>
                        {plan.steps && plan.steps.length > 0 ? (
                            <ol className="trace-steps">
                                {plan.steps.map((step, index) => (
                                    <li key={index} className="trace-step">
                                        <div className="step-tool">
                                            <strong>Tool:</strong> {step.tool}
                                        </div>
                                        <div className="step-args">
                                            <strong>Arguments:</strong>
                                            <pre>{JSON.stringify(step.args, null, 2)}</pre>
                                        </div>
                                    </li>
                                ))}
                            </ol>
                        ) : (
                            <p className="no-data">No steps defined</p>
                        )}
                    </div>

                    {plan.stop && (
                        <div className="trace-section">
                            <h4>Stop Conditions</h4>
                            <ul className="trace-stops">
                                <li>Max Rounds: {plan.stop.max_rounds || 'N/A'}</li>
                                <li>Budget: {plan.stop.budget_s || 'N/A'}s</li>
                            </ul>
                        </div>
                    )}

                    <div className="trace-section">
                        <h4>Final Verdict</h4>
                        <div className={`verdict-badge verdict-${verdict}`}>
                            {verdict === 'pass' ? '✓ PASS' : '✗ REVISE'}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Default state when no data is available
    return (
        <div className="trace-panel">
            <h3>Action Log</h3>
            <p className="no-trace-message">No execution trace available yet.</p>
        </div>
    );
};

export default TracePanel;
