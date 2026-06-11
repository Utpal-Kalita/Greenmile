import { useEffect, useState } from 'react';

// Static "before" baseline (2-trip model, Delhi-NCR seeded data)
const BEFORE = { km: 87, hrs: 8.2, cost: 653, co2: 19.4 };

function AnimatedNumber({ value, prefix = '', suffix = '', decimals = 0 }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = parseFloat(value);
    if (isNaN(end)) return;
    const duration = 1200;
    const step = (end / duration) * 16;
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setDisplay(end); clearInterval(timer); }
      else setDisplay(start);
    }, 16);
    return () => clearInterval(timer);
  }, [value]);
  return <>{prefix}{display.toFixed(decimals)}{suffix}</>;
}

export default function MetricCards({ optimized, afterMetrics }) {
  // Use real backend metrics when available, otherwise fall back to PRD demo numbers
  const after = afterMetrics
    ? {
        km:   afterMetrics.total_distance_km   ?? 52,
        hrs:  afterMetrics.driver_hours        ?? 5.1,
        cost: afterMetrics.estimated_fuel_cost ?? 390,
        co2:  afterMetrics.estimated_co2_kg    ?? 11.6,
      }
    : { km: 52, hrs: 5.1, cost: 390, co2: 11.6 };

  const savings = {
    km:   Math.max(0, Math.round(BEFORE.km - after.km)),
    hrs:  Math.max(0, (BEFORE.hrs - after.hrs).toFixed(1)),
    cost: Math.max(0, Math.round(BEFORE.cost - after.cost)),
    co2:  Math.max(0, (BEFORE.co2 - after.co2).toFixed(1)),
  };

  const savingPct = Math.round((savings.km / BEFORE.km) * 100);

  const cards = [
    {
      label: 'Distance',
      before: `${BEFORE.km} km`,
      after:  <AnimatedNumber value={after.km} suffix=" km" decimals={1} />,
      saving: `▼ ${savings.km} km saved (${savingPct}%)`,
      color: 'text-green-400',
    },
    {
      label: 'Driver Hours',
      before: `${BEFORE.hrs} hrs`,
      after:  <AnimatedNumber value={after.hrs} suffix=" hrs" decimals={1} />,
      saving: `▼ ${savings.hrs} hrs recovered`,
      color: 'text-green-400',
    },
    {
      label: 'Fuel Cost',
      before: `₹${BEFORE.cost}`,
      after:  <AnimatedNumber value={after.cost} prefix="₹" decimals={0} />,
      saving: `▼ ₹${savings.cost} saved/day`,
      color: 'text-green-400',
    },
    {
      label: 'CO₂ Emitted',
      before: `${BEFORE.co2} kg`,
      after:  <AnimatedNumber value={after.co2} suffix=" kg" decimals={1} />,
      saving: `▼ ${savings.co2} kg CO₂ avoided`,
      color: 'text-emerald-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl border ${optimized ? 'border-green-500/20' : 'border-[#1e2d45]'} bg-[#111827] p-4 transition-all duration-500`}
        >
          {/* Label row */}
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-[#64748b] uppercase tracking-wider">{card.label}</p>
            {optimized && (
              <span className="text-[9px] font-semibold text-green-400 bg-green-400/10 border border-green-400/20 rounded-full px-1.5 py-0.5">
                SAVED
              </span>
            )}
          </div>

          {/* Main value */}
          <p className={`text-2xl font-bold ${optimized ? card.color : 'text-[#e2e8f0]'}`}>
            {optimized ? card.after : card.before}
          </p>

          {/* Before baseline or saving */}
          {optimized ? (
            <p className="text-xs text-green-400 mt-1 flex items-center gap-1">{card.saving}</p>
          ) : (
            <p className="text-xs text-[#64748b] mt-1">Before optimization</p>
          )}
        </div>
      ))}
    </div>
  );
}
