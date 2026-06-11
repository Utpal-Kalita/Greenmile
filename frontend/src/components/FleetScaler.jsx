import { useState } from 'react';

// PRD baseline for "before" model (hardcoded as demo comparison)
const BEFORE = { cost: 653, co2: 19.4, hrs: 8.2, km: 87 };
const WORKING_DAYS = 250;

export default function FleetScaler({ dailySavings }) {
  const [vans, setVans] = useState(1);

  // Compute per-van daily savings from real backend metrics vs before baseline
  const perVan = dailySavings
    ? {
        cost: Math.max(0, Math.round(BEFORE.cost - (dailySavings.estimated_fuel_cost ?? 390))),
        co2:  Math.max(0, parseFloat((BEFORE.co2 - (dailySavings.estimated_co2_kg ?? 11.6)).toFixed(1))),
        hrs:  Math.max(0, parseFloat((BEFORE.hrs - 5.1).toFixed(1))),  // driver hrs not in backend yet
        km:   Math.max(0, Math.round(BEFORE.km - (dailySavings.total_distance_km ?? 52))),
      }
    : { cost: 263, co2: 7.8, hrs: 3.1, km: 35 };

  const annualCost = Math.round(vans * perVan.cost * WORKING_DAYS);
  const annualCO2  = (vans * perVan.co2 * WORKING_DAYS / 1000).toFixed(1);
  const annualHrs  = Math.round(vans * perVan.hrs * WORKING_DAYS);
  const annualKm   = Math.round(vans * perVan.km * WORKING_DAYS);
  const trees      = Math.round(parseFloat(annualCO2) * 1000 / 21); // ~21kg CO₂/tree/yr

  return (
    <div className="rounded-xl border border-[#1e2d45] bg-[#111827] p-4">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <h3 className="text-sm font-semibold text-[#e2e8f0]">Fleet Scaler</h3>
        {dailySavings && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
            Using real savings
          </span>
        )}
        <span className="ml-auto text-[10px] text-[#64748b]">Annual projection</span>
      </div>

      {/* ── Per-van daily savings row ───────────────────── */}
      <div className="flex gap-3 mb-4 pb-3 border-b border-[#1e2d45]">
        {[
          { label: 'Per van/day', value: `₹${perVan.cost}`, sub: 'fuel saved' },
          { label: 'CO₂/van/day', value: `${perVan.co2}kg`, sub: 'avoided' },
          { label: 'Hours/van/day', value: `${perVan.hrs}hrs`, sub: 'recovered' },
          { label: 'Km/van/day', value: `${perVan.km}km`, sub: 'less driving' },
        ].map(({ label, value, sub }) => (
          <div key={label} className="flex-1 text-center rounded-lg bg-[#0a0f1e] p-2">
            <p className="text-[9px] text-[#64748b] uppercase tracking-wider">{label}</p>
            <p className="text-sm font-bold text-green-400">{value}</p>
            <p className="text-[9px] text-[#64748b]">{sub}</p>
          </div>
        ))}
      </div>

      {/* ── Slider ─────────────────────────────────────── */}
      <div className="mb-4">
        <div className="flex justify-between mb-2">
          <span className="text-xs text-[#64748b]">1 van</span>
          <span className="text-sm font-bold text-green-400">{vans} van{vans > 1 ? 's' : ''}</span>
          <span className="text-xs text-[#64748b]">50 vans</span>
        </div>
        <input
          type="range" min={1} max={50} value={vans}
          onChange={(e) => setVans(Number(e.target.value))}
          className="w-full accent-green-400"
        />
        <div className="flex gap-2 mt-2 flex-wrap">
          {[1, 5, 10, 25, 50].map(v => (
            <button key={v} onClick={() => setVans(v)}
              className={`text-xs px-2 py-0.5 rounded-full border transition-all
                ${vans === v
                  ? 'border-green-400 bg-green-400/10 text-green-400'
                  : 'border-[#1e2d45] text-[#64748b] hover:border-green-500/50'}`}>
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* ── Annual Stats ────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-[#0a0f1e] p-3">
          <p className="text-[10px] text-[#64748b] uppercase tracking-wider">Annual Savings</p>
          <p className="text-lg font-bold text-green-400">₹{(annualCost / 100000).toFixed(1)}L</p>
          <p className="text-[10px] text-[#64748b]">₹{annualCost.toLocaleString()}/yr</p>
        </div>
        <div className="rounded-lg bg-[#0a0f1e] p-3">
          <p className="text-[10px] text-[#64748b] uppercase tracking-wider">CO₂ Avoided</p>
          <p className="text-lg font-bold text-green-400">{annualCO2}t</p>
          <p className="text-[10px] text-[#64748b]">≈ {trees} trees/yr</p>
        </div>
        <div className="rounded-lg bg-[#0a0f1e] p-3">
          <p className="text-[10px] text-[#64748b] uppercase tracking-wider">Hours Recovered</p>
          <p className="text-lg font-bold text-blue-400">{annualHrs.toLocaleString()} hrs</p>
          <p className="text-[10px] text-[#64748b]">≈ {Math.round(annualHrs / 8)} driver-days</p>
        </div>
        <div className="rounded-lg bg-[#0a0f1e] p-3">
          <p className="text-[10px] text-[#64748b] uppercase tracking-wider">Km Eliminated</p>
          <p className="text-lg font-bold text-purple-400">{(annualKm / 1000).toFixed(1)}K km</p>
          <p className="text-[10px] text-[#64748b]">{annualKm.toLocaleString()} km/yr</p>
        </div>
      </div>
    </div>
  );
}
