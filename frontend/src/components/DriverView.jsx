import { useState } from 'react';

const TYPE_STYLE = {
  DELIVERY: {
    dot: 'bg-green-400',
    badge: 'text-green-400 bg-green-500/10 border-green-500/20',
    icon: '📦',
  },
  RETURN: {
    dot: 'bg-amber-400',
    badge: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    icon: '↩',
  },
};

export default function DriverView({ route }) {
  const [currentIdx, setCurrentIdx] = useState(0);

  if (!route || route.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-[#64748b] text-sm">
        No route loaded yet — press ⚡ Optimize first.
      </div>
    );
  }

  const current = route[currentIdx];
  const remaining = route.length - currentIdx - 1;
  const style = TYPE_STYLE[current.type] || TYPE_STYLE.DELIVERY;
  const flagged = current.flag || current.return_count_30d >= 3 || current.dispute_history_count >= 1;

  const prev = () => setCurrentIdx(i => Math.max(0, i - 1));
  const next = () => setCurrentIdx(i => Math.min(route.length - 1, i + 1));

  return (
    <div className="space-y-4">
      {/* ── Current Stop Hero ──────────────────────────────────── */}
      <div className={`rounded-2xl border p-5 ${flagged ? 'border-red-500/40 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'}`}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-[#64748b]">
            Stop {currentIdx + 1} of {route.length}
          </span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${style.badge}`}>
            {style.icon} {current.type}
          </span>
        </div>

        <h2 className="text-2xl font-black text-[#e2e8f0] mt-1">{current.stop_id}</h2>
        <p className="text-sm text-[#94a3b8] mt-0.5">{current.address}</p>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-3 mt-4">
          <div className="flex items-center gap-1.5 text-xs text-[#64748b]">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {current.time_window_start} – {current.time_window_end}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-[#64748b]">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
            </svg>
            {current.weight_kg} kg · {current.volume_l} L
          </div>
        </div>

        {/* Anomaly warning */}
        {flagged && (
          <div className="mt-3 flex items-start gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2">
            <span className="text-red-400 text-sm mt-px">⚠</span>
            <div>
              <p className="text-xs font-semibold text-red-400">Anomaly Flagged</p>
              <p className="text-xs text-red-300/70 mt-0.5">
                {current.reason || `${current.return_count_30d} returns in 30d — verify before handover.`}
              </p>
              {current.suggested_action && (
                <span className={`inline-block mt-1 text-[10px] font-bold px-2 py-0.5 rounded
                  ${current.suggested_action === 'HOLD'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-amber-500/20 text-amber-400'}`}>
                  {current.suggested_action}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Navigation controls ───────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={prev}
          disabled={currentIdx === 0}
          className="rounded-xl border border-[#1e2d45] bg-[#111827] py-3 text-sm font-semibold text-[#64748b]
            hover:text-[#e2e8f0] hover:border-[#2a3f5f] disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
        >
          ← Previous
        </button>
        <button
          onClick={next}
          disabled={currentIdx === route.length - 1}
          className="rounded-xl bg-green-500 hover:bg-green-400 py-3 text-sm font-semibold text-white
            disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
        >
          {currentIdx === route.length - 1 ? '✓ All Done' : 'Next Stop →'}
        </button>
      </div>

      {/* ── Remaining stops mini-list ─────────────────────────── */}
      <div>
        <p className="text-xs text-[#64748b] uppercase tracking-wider mb-2 flex items-center gap-2">
          <span>Upcoming</span>
          <span className="px-1.5 py-0.5 rounded-full bg-[#1e2d45] text-[#94a3b8] font-bold">{remaining}</span>
        </p>
        <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
          {route.slice(currentIdx + 1).map((s, relIdx) => {
            const st = TYPE_STYLE[s.type] || TYPE_STYLE.DELIVERY;
            const isFlagged = s.flag || s.return_count_30d >= 3 || s.dispute_history_count >= 1;
            return (
              <button
                key={s.stop_id}
                onClick={() => setCurrentIdx(currentIdx + 1 + relIdx)}
                className="w-full flex items-center gap-3 rounded-lg bg-[#0a0f1e] hover:bg-[#111827] px-3 py-2 text-left transition-colors group"
              >
                <span className="text-xs font-bold text-[#64748b] w-5 shrink-0">
                  {currentIdx + 2 + relIdx}
                </span>
                <span className={`w-2 h-2 rounded-full shrink-0 ${st.dot}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#e2e8f0] truncate group-hover:text-white">
                    {s.stop_id} — {s.address}
                  </p>
                  <p className="text-[10px] text-[#64748b]">{s.time_window_start}–{s.time_window_end} · {s.weight_kg}kg</p>
                </div>
                {isFlagged && <span className="text-red-400 text-xs shrink-0">⚠</span>}
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${st.badge} shrink-0`}>
                  {s.type === 'DELIVERY' ? 'DEL' : 'RET'}
                </span>
              </button>
            );
          })}
          {remaining === 0 && (
            <p className="text-xs text-green-400 text-center py-3">🎉 All stops completed!</p>
          )}
        </div>
      </div>

      {/* ── Progress bar ─────────────────────────────────────────── */}
      <div>
        <div className="flex justify-between text-[10px] text-[#64748b] mb-1">
          <span>Progress</span>
          <span>{currentIdx + 1}/{route.length} stops</span>
        </div>
        <div className="h-1.5 rounded-full bg-[#1e2d45] overflow-hidden">
          <div
            className="h-full rounded-full bg-green-400 transition-all duration-500"
            style={{ width: `${((currentIdx + 1) / route.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
