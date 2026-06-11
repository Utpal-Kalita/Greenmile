import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const DELHI_CENTER = [28.555, 77.209];
const ZOOM = 12;

// ─── Mini map label overlay ───────────────────────────────────────────────────
function MapLabel({ label, km, color }) {
  return (
    <div
      style={{ position: 'absolute', top: 10, left: 10, zIndex: 1000 }}
      className={`rounded-lg px-2.5 py-1.5 text-xs font-bold backdrop-blur-sm border
        ${color === 'red'
          ? 'bg-[#0a0f1e]/85 text-red-400 border-red-500/30'
          : 'bg-[#0a0f1e]/85 text-green-400 border-green-500/30'
        }`}
    >
      {label}<br />
      <span className="text-[10px] font-normal opacity-70">{km}</span>
    </div>
  );
}

// ─── Savings pop badge (after panel) ─────────────────────────────────────────
function SavingsBadge({ afterMetrics, visible }) {
  const saved = afterMetrics
    ? {
        km:   Math.max(0, Math.round(87 - (afterMetrics.total_distance_km ?? 52))),
        cost: Math.max(0, Math.round(653 - (afterMetrics.estimated_fuel_cost ?? 390))),
        co2:  Math.max(0, (19.4 - (afterMetrics.estimated_co2_kg ?? 11.6)).toFixed(1)),
      }
    : { km: 35, cost: 263, co2: 7.8 };

  return (
    <div
      style={{
        position: 'absolute', bottom: 40, left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        transition: 'opacity 0.6s ease, transform 0.6s ease',
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(12px)',
        pointerEvents: 'none',
      }}
    >
      <div className="flex gap-2 flex-wrap justify-center">
        {[
          { v: `▼ ${saved.km} km`, label: 'saved' },
          { v: `₹${saved.cost}`, label: 'saved/day' },
          { v: `${saved.co2} kg`, label: 'CO₂ avoided' },
        ].map(({ v, label }) => (
          <span key={label}
            className="text-[10px] font-bold px-2 py-1 rounded-full bg-green-500/20 text-green-300 border border-green-500/30 whitespace-nowrap backdrop-blur-sm"
          >
            {v} <span className="font-normal opacity-70">{label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Before map (2 separate trips) ───────────────────────────────────────────
function BeforeMap({ stops, faded }) {
  const deliveries = stops.filter(s => s.type === 'DELIVERY');
  const returns    = stops.filter(s => s.type === 'RETURN');
  const delPts  = deliveries.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);
  const retPts  = returns.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);

  return (
    <div style={{
      height: '100%', width: '100%',
      transition: 'opacity 0.8s ease',
      opacity: faded ? 0.45 : 1,
    }}>
      <MapContainer
        center={DELHI_CENTER}
        zoom={ZOOM}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {delPts.length > 1 && (
          <Polyline positions={delPts} pathOptions={{ color: '#ef4444', weight: 2.5, opacity: 0.75, dashArray: '8 5' }} />
        )}
        {retPts.length > 1 && (
          <Polyline positions={retPts} pathOptions={{ color: '#3b82f6', weight: 2.5, opacity: 0.75, dashArray: '8 5' }} />
        )}

        {deliveries.map(s => (
          <CircleMarker key={s.stop_id} center={[parseFloat(s.lat), parseFloat(s.lng)]} radius={6}
            pathOptions={{ fillColor: '#3b82f6', color: '#fff', weight: 1.5, fillOpacity: 0.9 }}>
            <Tooltip><span className="text-xs">{s.stop_id} — {s.address}</span></Tooltip>
          </CircleMarker>
        ))}
        {returns.map(s => (
          <CircleMarker key={s.stop_id} center={[parseFloat(s.lat), parseFloat(s.lng)]} radius={6}
            pathOptions={{ fillColor: '#ef4444', color: '#fff', weight: 1.5, fillOpacity: 0.9 }}>
            <Tooltip><span className="text-xs">{s.stop_id} — {s.address}</span></Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

// ─── After map — progressively draws the green loop ──────────────────────────
function AfterMap({ stops, route, onDrawComplete }) {
  const deliveries = stops.filter(s => s.type === 'DELIVERY');
  const returns    = stops.filter(s => s.type === 'RETURN');
  const fullPts    = route.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);

  // Animate: start with 0 points, grow to fullPts.length
  const [visibleCount, setVisibleCount] = useState(0);
  const [drawDone, setDrawDone] = useState(false);

  useEffect(() => {
    if (fullPts.length === 0) return;
    let count = 0;
    // Draw one new segment every ~60ms → total ~(n * 60)ms for n stops
    const interval = setInterval(() => {
      count += 1;
      setVisibleCount(count);
      if (count >= fullPts.length) {
        clearInterval(interval);
        setDrawDone(true);
        if (onDrawComplete) onDrawComplete();
      }
    }, 70);
    return () => clearInterval(interval);
  }, [route.length]); // eslint-disable-line

  const animatedPts = fullPts.slice(0, Math.max(2, visibleCount));

  return (
    <MapContainer
      center={DELHI_CENTER}
      zoom={ZOOM}
      style={{ height: '100%', width: '100%' }}
      zoomControl={false}
      attributionControl={false}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* Animated green loop — grows progressively */}
      {animatedPts.length > 1 && (
        <Polyline
          positions={animatedPts}
          pathOptions={{ color: '#22c55e', weight: 3, opacity: 0.95 }}
        />
      )}

      {/* Delivery markers — fade in after route is drawn */}
      {deliveries.map(s => (
        <CircleMarker key={s.stop_id} center={[parseFloat(s.lat), parseFloat(s.lng)]} radius={6}
          pathOptions={{ fillColor: '#22c55e', color: '#fff', weight: 1.5, fillOpacity: drawDone ? 0.9 : 0.3 }}>
          <Tooltip><span className="text-xs">{s.stop_id} — {s.address}</span></Tooltip>
        </CircleMarker>
      ))}
      {returns.map(s => {
        const flagged = s.flag || s.return_count_30d >= 3 || s.dispute_history_count >= 1;
        return (
          <CircleMarker key={s.stop_id} center={[parseFloat(s.lat), parseFloat(s.lng)]}
            radius={flagged ? 8 : 6}
            pathOptions={{ fillColor: flagged ? '#ef4444' : '#f59e0b', color: '#fff', weight: 1.5, fillOpacity: drawDone ? 0.9 : 0.3 }}>
            <Tooltip>
              <span className="text-xs">{s.stop_id} — {s.address}</span>
              {flagged && <><br /><span className="text-xs text-red-500">⚠ {s.suggested_action ?? 'VERIFY'}</span></>}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}

// ─── Split Map (exported) ─────────────────────────────────────────────────────
export default function SplitRouteMap({ stops, route, afterMetrics }) {
  const afterKm = afterMetrics?.total_distance_km ?? 52;

  // Panel slide-in animation state
  const [panelsVisible, setPanelsVisible] = useState(false);
  // Savings badge appears after route is fully drawn
  const [savingsVisible, setSavingsVisible] = useState(false);
  // Dim the before map while after map draws
  const [beforeFaded, setBeforeFaded] = useState(false);

  useEffect(() => {
    // Trigger panel fade-in immediately on mount
    const t1 = setTimeout(() => setPanelsVisible(true), 50);
    // Start dimming the before map after a short delay
    const t2 = setTimeout(() => setBeforeFaded(true), 400);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  const handleDrawComplete = () => {
    setTimeout(() => setSavingsVisible(true), 200);
  };

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        height: '420px',
        opacity: panelsVisible ? 1 : 0,
        transform: panelsVisible ? 'translateY(0)' : 'translateY(16px)',
        transition: 'opacity 0.5s ease, transform 0.5s ease',
      }}
    >
      {/* ── BEFORE panel ─────────────────────────────────────────── */}
      <div className="relative rounded-xl overflow-hidden border border-red-500/25"
        style={{ transition: 'border-color 0.8s ease', borderColor: beforeFaded ? 'rgba(239,68,68,0.1)' : undefined }}
      >
        <MapLabel label="⚡ Before — 2 Trips" km="87 km · 8.2 hrs · ₹653" color="red" />
        <BeforeMap stops={stops} faded={beforeFaded} />
        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-[1000] flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-[10px] text-white bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full">
            <span className="w-3 h-0.5 bg-red-400 inline-block rounded" />Delivery trip
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-white bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full">
            <span className="w-3 h-0.5 bg-blue-400 inline-block rounded" />Return trip (empty van)
          </span>
        </div>
      </div>

      {/* ── AFTER panel ──────────────────────────────────────────── */}
      <div className="relative rounded-xl overflow-hidden border border-green-500/25">
        <MapLabel label="✅ After — 1 Loop" km={`${afterKm} km · ₹390 · 5.1 hrs`} color="green" />
        <AfterMap stops={stops} route={route} onDrawComplete={handleDrawComplete} />

        {/* Animated route drawing label */}
        <div
          className="absolute top-10 left-3 z-[1000]"
          style={{ transition: 'opacity 0.5s ease', opacity: beforeFaded && !savingsVisible ? 1 : 0 }}
        >
          <span className="text-[10px] text-green-400 bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse inline-block" />
            Drawing route…
          </span>
        </div>

        {/* Savings pop badges */}
        <SavingsBadge afterMetrics={afterMetrics} visible={savingsVisible} />

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-[1000] flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-[10px] text-white bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full">
            <span className="w-2.5 h-2.5 rounded-full bg-green-400 inline-block" />Delivery
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-white bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />Return
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-white bg-[#0a0f1e]/80 px-2 py-0.5 rounded-full">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block" />⚠ Flagged
          </span>
        </div>
      </div>
    </div>
  );
}
