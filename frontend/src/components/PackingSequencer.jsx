// ─── SVG Van Top-View Diagram ────────────────────────────────────────────────
// Renders a proper SVG bird's-eye van with colour-coded cargo blocks.
function VanDiagramSVG({ returns, deliveries, preStaged }) {
  const W = 400, H = 140;
  const bodyX = 20, bodyY = 20, bodyW = W - 40, bodyH = H - 40;

  // Bay divider: rear = left 45%, front = right 55%
  const divX = bodyX + Math.round(bodyW * 0.45);

  // Item slot layout helper
  const itemSize = 28, gap = 4;

  const rearItems  = [
    ...returns.map(s  => ({ id: s.stop_id, color: '#ef4444', fill: 'rgba(239,68,68,0.25)', label: s.stop_id, dashed: false })),
    ...preStaged.map(s => ({ id: `ps-${s.stop_id}`, color: '#f59e0b', fill: 'rgba(245,158,11,0.2)', label: s.stop_id, dashed: true })),
  ];
  const frontItems = deliveries.map(s => {
    const isRisk = s.return_probability != null && s.return_probability >= 0.5;
    return { id: s.stop_id, color: isRisk ? '#f59e0b' : '#3b82f6', fill: isRisk ? 'rgba(245,158,11,0.2)' : 'rgba(59,130,246,0.22)', label: s.stop_id, dashed: false };
  });

  function renderSlots(items, startX, maxW) {
    const cols = Math.max(1, Math.floor((maxW - 8) / (itemSize + gap)));
    return items.map((item, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const x = startX + 6 + col * (itemSize + gap);
      const y = bodyY + 20 + row * (itemSize + gap);
      return (
        <g key={item.id}>
          <rect x={x} y={y} width={itemSize} height={itemSize} rx={4}
            fill={item.fill} stroke={item.color} strokeWidth={item.dashed ? 0 : 1.5}
            strokeDasharray={item.dashed ? '4 2' : undefined} />
          <text x={x + itemSize / 2} y={y + itemSize / 2 + 3.5}
            textAnchor="middle" fontSize="7" fill={item.color} fontWeight="bold">
            {item.label.slice(0, 3)}
          </text>
        </g>
      );
    });
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxHeight: 140, display: 'block' }} aria-label="Van packing diagram top view">
      {/* Van body */}
      <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx={8}
        fill="rgba(30,45,69,0.6)" stroke="#334155" strokeWidth={1.5} />

      {/* Cabin (front) — rightmost 16% */}
      <rect x={bodyX + bodyW - Math.round(bodyW * 0.16)} y={bodyY} width={Math.round(bodyW * 0.16)} height={bodyH} rx={8}
        fill="rgba(15,23,42,0.8)" stroke="#475569" strokeWidth={1} />
      <text x={bodyX + bodyW - Math.round(bodyW * 0.08)} y={bodyY + bodyH / 2 + 3}
        textAnchor="middle" fontSize="7" fill="#64748b" transform={`rotate(90,${bodyX + bodyW - Math.round(bodyW * 0.08)},${bodyY + bodyH / 2})`}>
        CABIN
      </text>

      {/* Rear door (left edge) */}
      <rect x={bodyX} y={bodyY + 10} width={6} height={bodyH - 20} rx={2}
        fill="rgba(100,116,139,0.3)" stroke="#64748b" strokeWidth={1} />

      {/* Bay divider line */}
      <line x1={divX} y1={bodyY + 4} x2={divX} y2={bodyY + bodyH - 4}
        stroke="#334155" strokeWidth={1.5} strokeDasharray="4 3" />

      {/* Bay labels */}
      <text x={bodyX + (divX - bodyX) / 2} y={bodyY + 13} textAnchor="middle" fontSize="7" fill="#ef4444" fontWeight="bold">
        ↑ REAR (Returns)
      </text>
      <text x={divX + (bodyX + bodyW - Math.round(bodyW * 0.16) - divX) / 2} y={bodyY + 13}
        textAnchor="middle" fontSize="7" fill="#3b82f6" fontWeight="bold">
        ↓ FRONT (Deliveries)
      </text>

      {/* Rear items (returns + pre-staged) */}
      {renderSlots(rearItems, bodyX + 6, divX - bodyX - 10)}

      {/* Front items (deliveries) */}
      {renderSlots(frontItems, divX + 4, bodyX + bodyW - Math.round(bodyW * 0.16) - divX - 8)}

      {/* Empty state labels */}
      {rearItems.length === 0 && (
        <text x={bodyX + (divX - bodyX) / 2} y={bodyY + bodyH / 2 + 3}
          textAnchor="middle" fontSize="8" fill="#475569">None</text>
      )}
      {frontItems.length === 0 && (
        <text x={divX + (bodyX + bodyW - Math.round(bodyW * 0.16) - divX) / 2} y={bodyY + bodyH / 2 + 3}
          textAnchor="middle" fontSize="8" fill="#475569">None</text>
      )}

      {/* Driver door indicator */}
      <text x={bodyX + 3} y={bodyY + bodyH + 14} fontSize="8" fill="#475569">← Driver door</text>
    </svg>
  );
}

export default function PackingSequencer({ route }) {
  if (!route || route.length === 0) return null;

  const deliveries = route.filter(s => s.type === 'DELIVERY');
  const returns    = route.filter(s => s.type === 'RETURN');

  // Pre-staged return slots: deliveries with return_probability > 0.5
  const preStaged  = deliveries.filter(s => s.pre_stage_return);

  // Load order: returns first (rear), pre-staged slots next (rear), deliveries (front)
  const loadOrder = [
    ...returns.map((s, i) => ({ ...s, position: 'REAR', slotIndex: i + 1, slotType: 'confirmed-return' })),
    ...preStaged.map((s, i) => ({ ...s, position: 'REAR (pre-staged)', slotIndex: returns.length + i + 1, slotType: 'pre-staged' })),
    ...deliveries.map((s, i) => ({ ...s, position: 'FRONT', slotIndex: i + 1, slotType: 'delivery' })),
  ];

  const probColor = (p) => {
    if (p == null) return '';
    if (p >= 0.7) return 'text-red-400';
    if (p >= 0.5) return 'text-amber-400';
    return 'text-green-400';
  };

  return (
    <div className="rounded-xl border border-[#1e2d45] bg-[#111827] p-4">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
        <h3 className="text-sm font-semibold text-[#e2e8f0]">Packing Sequencer</h3>
        {preStaged.length > 0 && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            {preStaged.length} pre-staged return{preStaged.length > 1 ? 's' : ''}
          </span>
        )}
        <span className="ml-auto text-[10px] text-[#64748b]">Load in this order →</span>
      </div>

      {/* ── Van SVG Diagram ─────────────────────────────── */}
      <div className="relative rounded-lg bg-[#0a0f1e] border border-[#1e2d45] p-3 mb-4 overflow-hidden">
        <div className="text-[10px] text-[#64748b] text-center mb-2 uppercase tracking-widest">Van Top View (SVG)</div>
        <VanDiagramSVG returns={returns} deliveries={deliveries} preStaged={preStaged} />
      </div>

      {/* ── Pre-staged return alert ──────────────────────── */}
      {preStaged.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 mb-3 text-xs text-amber-300">
          <span className="font-semibold text-amber-400">⚠ {preStaged.length} pre-staged return bay slot{preStaged.length > 1 ? 's' : ''}</span>
          {' '}— Confirm with fleet manager before dispatch.
          <div className="mt-1 text-[10px] text-amber-300/70">
            {preStaged.map(s => `${s.stop_id} (${Math.round((s.return_probability ?? 0) * 100)}%)`).join(' · ')}
          </div>
        </div>
      )}

      {/* ── Load order checklist ─────────────────────────── */}
      <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
        {loadOrder.map((s, i) => {
          const prob = s.return_probability;
          const isPreStaged = s.slotType === 'pre-staged';

          return (
            <div key={`${s.stop_id}-${i}`}
              className={`flex items-center gap-3 rounded-lg px-3 py-2
                ${isPreStaged ? 'bg-amber-500/5 border border-amber-500/10' : 'bg-[#0a0f1e]'}`}>
              <span className="text-xs font-bold text-[#64748b] w-4">{i + 1}</span>
              <div className={`w-2 h-2 rounded-full shrink-0
                ${isPreStaged ? 'bg-amber-400' : s.type === 'RETURN' ? 'bg-red-400' : 'bg-blue-400'}`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-[#e2e8f0] truncate">{s.stop_id} — {s.address}</p>
                <p className="text-[10px] text-[#64748b]">
                  {s.weight_kg}kg · {s.volume_l}L · {s.position}
                  {isPreStaged && ' ← pre-staged slot'}
                </p>
              </div>
              {/* Return probability badge (delivery stops only) */}
              {prob != null && (
                <div className="text-right shrink-0">
                  <p className="text-[9px] text-[#64748b]">return prob</p>
                  <p className={`text-xs font-bold ${probColor(prob)}`}>{Math.round(prob * 100)}%</p>
                </div>
              )}
              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0
                ${isPreStaged
                  ? 'text-amber-400 bg-amber-500/10'
                  : s.type === 'RETURN'
                    ? 'text-red-400 bg-red-500/10'
                    : 'text-blue-400 bg-blue-500/10'
                }`}>
                {isPreStaged ? 'PRE-STAGE' : s.type}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
