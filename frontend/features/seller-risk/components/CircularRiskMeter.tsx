import React from 'react';

interface CircularRiskMeterProps {
  score: number; // 0 - 100
  size?: number; // width and height in px
  strokeWidth?: number;
}

export const CircularRiskMeter: React.FC<CircularRiskMeterProps> = ({
  score,
  size = 80,
  strokeWidth = 8,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Determine risk level color
  let strokeColor = '#10B981'; // Green (0 - 30)
  let badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  let tierLabel = 'Low';

  if (score >= 70) {
    strokeColor = '#EF4444'; // Red-orange (70 - 100)
    badgeBg = 'bg-rose-50 text-rose-800 border-rose-200';
    tierLabel = 'High Risk';
  } else if (score >= 30) {
    strokeColor = '#F59E0B'; // Amber (30 - 69)
    badgeBg = 'bg-amber-50 text-amber-800 border-amber-200';
    tierLabel = 'Medium';
  }

  return (
    <div className="flex items-center space-x-3">
      <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Animated score ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Score */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="font-bold text-slate-900 font-mono leading-none" style={{ fontSize: size * 0.28 }}>
            {score}
          </span>
          <span className="text-[9px] uppercase font-mono font-semibold text-slate-400 mt-0.5">/ 100</span>
        </div>
      </div>

      <div className="flex flex-col space-y-1">
        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-full border text-center ${badgeBg}`}>
          {tierLabel}
        </span>
        <span className="text-[10px] text-slate-400 font-mono uppercase">Risk Index</span>
      </div>
    </div>
  );
};
