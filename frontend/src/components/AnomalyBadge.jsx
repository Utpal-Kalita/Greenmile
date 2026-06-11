export default function AnomalyBadge({ stops }) {
  if (!stops || stops.length === 0) return null;
  const flagged = stops.filter(s =>
    s.type === 'RETURN' && (s.return_count_30d >= 3 || s.dispute_history_count >= 1)
  );
  if (flagged.length === 0) return null;

  return (
    <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500/20 text-red-400 text-xs font-bold">!</span>
        <h3 className="text-sm font-semibold text-red-400">
          {flagged.length} Anomaly {flagged.length > 1 ? 'Flags' : 'Flag'} Detected
        </h3>
        <span className="ml-auto text-[10px] font-medium px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">
          AI Risk Analysis
        </span>
      </div>
      <div className="space-y-2">
        {flagged.map((s) => {
          const score = Math.min(0.95, 0.5 + s.return_count_30d * 0.12 + s.dispute_history_count * 0.2).toFixed(2);
          const action = parseFloat(score) > 0.8 ? 'HOLD' : parseFloat(score) > 0.65 ? 'VERIFY' : 'PROCEED';
          const actionColor = action === 'HOLD' ? 'text-red-400 bg-red-500/20' : action === 'VERIFY' ? 'text-amber-400 bg-amber-500/20' : 'text-green-400 bg-green-500/20';
          return (
            <div key={s.stop_id} className="flex items-start gap-3 rounded-lg bg-[#0a0f1e] p-3 text-sm">
              <div className="flex-1">
                <p className="font-medium text-[#e2e8f0]">{s.stop_id} — {s.address}</p>
                <p className="text-xs text-[#64748b] mt-0.5">
                  {s.return_count_30d}x returns in 30d · {s.dispute_history_count} dispute{s.dispute_history_count !== 1 ? 's' : ''}
                  {s.return_count_30d >= 3 ? ' — Freq returning address, verify before dispatch.' : ' — Prior dispute found.'}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-[#64748b]">Risk</p>
                <p className="text-base font-bold text-red-400">{score}</p>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${actionColor}`}>{action}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
