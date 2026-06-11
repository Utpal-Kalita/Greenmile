import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const DELHI_CENTER = [28.555, 77.2090];

// Fits map bounds to all stop markers
function FitBounds({ stops }) {
  const map = useMap();
  useEffect(() => {
    if (stops.length === 0) return;
    const bounds = stops.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [stops.length]); // eslint-disable-line
  return null;
}

// Sequentially renders polyline segments for an animated "drawing" effect
function AnimatedPolyline({ points, color, weight, opacity, dashArray }) {
  const polyRef = useRef(null);

  useEffect(() => {
    if (!polyRef.current || points.length < 2) return;
    const layer = polyRef.current;

    // Reset to invisible, then animate via CSS
    const el = layer.getElement?.();
    if (el) {
      el.style.transition = 'none';
      el.style.opacity = '0';
      el.style.strokeDasharray = '3000';
      el.style.strokeDashoffset = '3000';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          el.style.transition = 'opacity 0.4s ease, stroke-dashoffset 1.8s ease-in-out';
          el.style.opacity = String(opacity ?? 0.9);
          el.style.strokeDashoffset = '0';
        });
      });
    }
  }, [points]); // re-animate whenever points change

  return (
    <Polyline
      ref={polyRef}
      positions={points}
      pathOptions={{ color, weight: weight ?? 3, opacity: opacity ?? 0.9, dashArray }}
    />
  );
}

export default function RouteMap({ stops, route, optimized }) {
  const deliveries = stops.filter(s => s.type === 'DELIVERY');
  const returns    = stops.filter(s => s.type === 'RETURN');

  // Before state: delivery route + separate empty return trip
  const deliveryPoints = deliveries.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);
  const returnPoints   = returns.map(s => [parseFloat(s.lat), parseFloat(s.lng)]);

  // After state: single optimised green loop
  const optimizedPoints = route.length > 0
    ? route.map(s => [parseFloat(s.lat), parseFloat(s.lng)])
    : [];

  return (
    <MapContainer
      center={DELHI_CENTER}
      zoom={12}
      style={{ height: '100%', width: '100%', borderRadius: '0.75rem' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
      />

      <FitBounds stops={stops} />

      {/* ── BEFORE: two separate trip lines ──────────────────────── */}
      {!optimized && (
        <>
          {deliveryPoints.length > 1 && (
            <AnimatedPolyline points={deliveryPoints} color="#ef4444" weight={2} opacity={0.7} dashArray="6 4" />
          )}
          {returnPoints.length > 1 && (
            <AnimatedPolyline points={returnPoints} color="#3b82f6" weight={2} opacity={0.7} dashArray="6 4" />
          )}
        </>
      )}

      {/* ── AFTER: single optimised green loop ───────────────────── */}
      {optimized && optimizedPoints.length > 1 && (
        <AnimatedPolyline key="optimized" points={optimizedPoints} color="#22c55e" weight={3} opacity={0.9} />
      )}

      {/* ── Delivery stop markers ─────────────────────────────────── */}
      {deliveries.map(s => (
        <CircleMarker
          key={s.stop_id}
          center={[parseFloat(s.lat), parseFloat(s.lng)]}
          radius={7}
          pathOptions={{
            fillColor: optimized ? '#22c55e' : '#3b82f6',
            color: '#fff',
            weight: 1.5,
            fillOpacity: 0.9,
          }}
        >
          <Tooltip>
            <span className="text-xs font-medium">{s.stop_id} — {s.address}</span><br />
            <span className="text-xs text-gray-500">{s.weight_kg}kg · {s.time_window_start}–{s.time_window_end}</span>
          </Tooltip>
        </CircleMarker>
      ))}

      {/* ── Return stop markers (flagged = red, normal = amber) ───── */}
      {returns.map(s => {
        const flagged = s.flag || s.return_count_30d >= 3 || s.dispute_history_count >= 1;
        const riskScore = s.risk_score;
        return (
          <CircleMarker
            key={s.stop_id}
            center={[parseFloat(s.lat), parseFloat(s.lng)]}
            radius={flagged ? 9 : 7}
            pathOptions={{
              fillColor: flagged ? '#ef4444' : '#f59e0b',
              color: flagged ? '#fca5a5' : '#fff',
              weight: flagged ? 2 : 1.5,
              fillOpacity: 0.9,
            }}
          >
            <Tooltip>
              <span className="text-xs font-medium">{s.stop_id} — {s.address}</span>
              {flagged && (
                <>
                  <br />
                  <span className="text-xs text-red-500">
                    ⚠ Risk {riskScore != null ? riskScore.toFixed(2) : 'flagged'} — {s.suggested_action ?? 'VERIFY'}
                  </span>
                  {s.reason && <><br /><span className="text-xs text-gray-400">{s.reason}</span></>}
                </>
              )}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
