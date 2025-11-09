import React from 'react';
import './RiskIndicator.css';

const RiskIndicator = ({ riskIndex }) => {
    if (riskIndex === undefined || riskIndex === null) {
        return null;
    }

    // Determine risk level and color
    const getRiskLevel = (score) => {
        if (score < 4) return { level: 'Low', color: '#4CAF50', bgColor: '#E8F5E8' };
        if (score < 7) return { level: 'Medium', color: '#FF9800', bgColor: '#FFF3E0' };
        return { level: 'High', color: '#F44336', bgColor: '#FFEBEE' };
    };

    const riskInfo = getRiskLevel(riskIndex);

    return (
        <div className="risk-indicator">
            <div className="risk-header">
                <h4>Risk Index</h4>
            </div>
            <div className="risk-content">
                <div
                    className="risk-bar"
                    style={{
                        backgroundColor: riskInfo.bgColor,
                        borderColor: riskInfo.color
                    }}
                >
                    <div
                        className="risk-fill"
                        style={{
                            backgroundColor: riskInfo.color,
                            width: `${Math.min((riskIndex / 10) * 100, 100)}%`
                        }}
                    />
                    <div className="risk-text">
                        <span className="risk-score">{riskIndex}</span>
                        <span className="risk-level" style={{ color: riskInfo.color }}>
                            {riskInfo.level} Risk
                        </span>
                    </div>
                </div>
                <div className="risk-description">
                    {riskIndex < 4 && "Low complexity and connectivity"}
                    {riskIndex >= 4 && riskIndex < 7 && "Moderate complexity and connectivity"}
                    {riskIndex >= 7 && "High complexity and connectivity - consider refactoring"}
                </div>
            </div>
        </div>
    );
};

export default RiskIndicator;



