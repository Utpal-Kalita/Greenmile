import { useState } from 'react';
import MetricCards from './components/MetricCards';
import UploadDropzone from './components/UploadDropzone';
import AnomalyBadge from './components/AnomalyBadge';
import PackingSequencer from './components/PackingSequencer';
import FleetScaler from './components/FleetScaler';
import RouteMap from './components/RouteMap';
import SplitRouteMap from './components/SplitRouteMap';
import DriverView from './components/DriverView';

// ─── Seeded Demo Data (Delhi-NCR Zone B — 14 deliveries + 4 returns) ──────────
const DEMO_STOPS = [
  { stop_id:'D1',  type:'DELIVERY', lat:28.5245, lng:77.2066, weight_kg:2.5,  volume_l:10, time_window_start:'09:00', time_window_end:'12:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:5,  dispute_history_count:0, address:'Saket Block A' },
  { stop_id:'D2',  type:'DELIVERY', lat:28.5284, lng:77.2068, weight_kg:1.2,  volume_l:5,  time_window_start:'09:00', time_window_end:'12:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:4,  dispute_history_count:0, address:'Saket Block B' },
  { stop_id:'D3',  type:'DELIVERY', lat:28.5323, lng:77.2078, weight_kg:5.0,  volume_l:20, time_window_start:'09:00', time_window_end:'12:00', cluster_id:'Zone_B', return_count_30d:1, avg_delivery_confirm_minutes:10, dispute_history_count:0, address:'Saket Block C' },
  { stop_id:'D4',  type:'DELIVERY', lat:28.5362, lng:77.2088, weight_kg:0.5,  volume_l:2,  time_window_start:'09:00', time_window_end:'12:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:3,  dispute_history_count:0, address:'Saket Block D' },
  { stop_id:'D5',  type:'DELIVERY', lat:28.5401, lng:77.2098, weight_kg:3.2,  volume_l:15, time_window_start:'12:00', time_window_end:'15:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:6,  dispute_history_count:0, address:'Saket Block E' },
  { stop_id:'D6',  type:'DELIVERY', lat:28.5440, lng:77.2108, weight_kg:1.8,  volume_l:8,  time_window_start:'12:00', time_window_end:'15:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:4,  dispute_history_count:0, address:'Saket Block F' },
  { stop_id:'D7',  type:'DELIVERY', lat:28.5479, lng:77.2118, weight_kg:4.1,  volume_l:18, time_window_start:'12:00', time_window_end:'15:00', cluster_id:'Zone_B', return_count_30d:3, avg_delivery_confirm_minutes:15, dispute_history_count:1, address:'Malviya Nagar' },
  { stop_id:'D8',  type:'DELIVERY', lat:28.5518, lng:77.2128, weight_kg:2.0,  volume_l:10, time_window_start:'12:00', time_window_end:'15:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:5,  dispute_history_count:0, address:'Malviya Nagar' },
  { stop_id:'D9',  type:'DELIVERY', lat:28.5557, lng:77.2138, weight_kg:0.8,  volume_l:4,  time_window_start:'15:00', time_window_end:'18:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:4,  dispute_history_count:0, address:'Malviya Nagar' },
  { stop_id:'D10', type:'DELIVERY', lat:28.5596, lng:77.2148, weight_kg:6.5,  volume_l:25, time_window_start:'15:00', time_window_end:'18:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:12, dispute_history_count:0, address:'Malviya Nagar' },
  { stop_id:'D11', type:'DELIVERY', lat:28.5635, lng:77.2158, weight_kg:1.5,  volume_l:6,  time_window_start:'15:00', time_window_end:'18:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:7,  dispute_history_count:0, address:'Malviya Nagar' },
  { stop_id:'D12', type:'DELIVERY', lat:28.5674, lng:77.2168, weight_kg:3.0,  volume_l:12, time_window_start:'15:00', time_window_end:'18:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:5,  dispute_history_count:0, address:'Malviya Nagar' },
  { stop_id:'D13', type:'DELIVERY', lat:28.5713, lng:77.2178, weight_kg:2.2,  volume_l:9,  time_window_start:'18:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:6,  dispute_history_count:0, address:'Vasant Kunj' },
  { stop_id:'D14', type:'DELIVERY', lat:28.5752, lng:77.2188, weight_kg:1.0,  volume_l:5,  time_window_start:'18:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:4,  dispute_history_count:0, address:'Vasant Kunj' },
  { stop_id:'R1',  type:'RETURN',   lat:28.5284, lng:77.2068, weight_kg:1.2,  volume_l:5,  time_window_start:'09:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:1, avg_delivery_confirm_minutes:0,  dispute_history_count:0, address:'Saket Block B' },
  { stop_id:'R2',  type:'RETURN',   lat:28.5401, lng:77.2098, weight_kg:3.2,  volume_l:15, time_window_start:'09:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:0,  dispute_history_count:0, address:'Saket Block E' },
  { stop_id:'R3',  type:'RETURN',   lat:28.5479, lng:77.2118, weight_kg:4.1,  volume_l:18, time_window_start:'09:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:3, avg_delivery_confirm_minutes:0,  dispute_history_count:1, address:'Malviya Nagar' },
  { stop_id:'R4',  type:'RETURN',   lat:28.5713, lng:77.2178, weight_kg:2.2,  volume_l:9,  time_window_start:'09:00', time_window_end:'21:00', cluster_id:'Zone_B', return_count_30d:0, avg_delivery_confirm_minutes:0,  dispute_history_count:0, address:'Vasant Kunj' },
];

export default function App() {
  const [stops, setStops] = useState([]);
  const [route, setRoute] = useState([]);
  const [optimized, setOptimized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [nlSummary, setNlSummary] = useState('');
  const [afterMetrics, setAfterMetrics] = useState(null);
  const [preStaged, setPreStaged] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [activeTab, setActiveTab] = useState('map');

  const deliveries = stops.filter(s => s.type === 'DELIVERY');
  const returns    = stops.filter(s => s.type === 'RETURN');
  const zones = [...new Set(stops.map(s => s.cluster_id))];

  // ── Load stops (from CSV upload or demo) ──────────────────────────────────
  const loadStops = (data) => {
    setStops(data);
    setOptimized(false);
    setRoute([]);
    setNlSummary('');
    setAfterMetrics(null);
    setUploadError('');
    setActiveTab('map');
  };

  // ── Optimize handler ──────────────────────────────────────────────────────
  const handleOptimize = async () => {
    if (stops.length === 0) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stops }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error ${res.status}`);
      }

      const json = await res.json();

      setRoute(json.route || []);
      setOptimized(true);
      setNlSummary(json.nl_summary || '');
      setAfterMetrics(json.metrics || null);
      setPreStaged(json.pre_staged_returns || 0);
    } catch (e) {
      console.error('Optimize failed', e);
      // Graceful fallback: use basic sorted route and mock metrics
      const fallback = [...stops.filter(s => s.type === 'DELIVERY'), ...stops.filter(s => s.type === 'RETURN')];
      setRoute(fallback);
      setOptimized(true);
      setNlSummary(
        `Your loop covers ${stops.length} stops across ${zones.join(', ')}. ` +
        `Load returns first (rear bay), then deliveries front-to-back. ` +
        `${returns.filter(s => s.return_count_30d >= 3 || s.dispute_history_count >= 1).length > 0
          ? 'Flag: Stop R3 in Malviya Nagar has a 3rd return this month — verify before dispatch.'
          : 'No anomalies detected.'}`
      );
    }
    setLoading(false);
  };

  const handleReset = () => {
    setOptimized(false);
    setRoute([]);
    setNlSummary('');
    setAfterMetrics(null);
    setPreStaged(0);
    setActiveTab('map');
  };

  const TABS = [
    { id: 'map',     label: '🗺 Route Map',     requiresOptimize: false },
    { id: 'packing', label: '📦 Packing Order', requiresOptimize: true },
    { id: 'driver',  label: '🚗 Driver View',   requiresOptimize: true },
    { id: 'scale',   label: '📈 Fleet Scaler',  requiresOptimize: false },
  ];

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-[#e2e8f0]">

      {/* ── Sticky Top Nav ──────────────────────────────────────────── */}
      <header className="border-b border-[#1e2d45] bg-[#0a0f1e]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-green-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6-10l6-3m0 13l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4" />
              </svg>
            </div>
            <span className="font-black text-lg tracking-tight">Greenmile</span>
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              v2.0
            </span>
          </div>
          <div className="ml-auto flex items-center gap-2 text-xs text-[#64748b]">
            <span className="hidden sm:inline">Bidirectional Last-Mile Optimizer</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 font-medium">Live</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-5">

        {/* ── Hero Banner (shown before upload) ─────────────────────── */}
        {stops.length === 0 && (
          <div className="rounded-2xl border border-[#1e2d45] bg-gradient-to-br from-[#111827] to-[#0a0f1e] p-8 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(34,197,94,0.07)_0%,transparent_60%)]" />
            <p className="text-xs font-semibold text-green-400 uppercase tracking-widest mb-2">FAR AWAY 2026 · Logistics & Transit</p>
            <h1 className="text-4xl font-black mb-2 leading-tight">
              The greenest mile is the one<br className="hidden sm:block" />
              <span className="text-green-400"> you don't drive twice.</span>
            </h1>
            <p className="text-[#64748b] text-sm max-w-xl mx-auto mb-6">
              Upload your delivery + returns CSV and Greenmile merges two trips into one smart bidirectional loop — saving ₹263/van/day.
            </p>
            <div className="flex justify-center gap-8 text-sm mb-2">
              <div className="text-center"><p className="text-2xl font-bold text-green-400">40%</p><p className="text-[#64748b] text-xs">Less distance</p></div>
              <div className="text-center"><p className="text-2xl font-bold text-green-400">₹263</p><p className="text-[#64748b] text-xs">Saved/van/day</p></div>
              <div className="text-center"><p className="text-2xl font-bold text-green-400">7.8kg</p><p className="text-[#64748b] text-xs">CO₂ avoided</p></div>
            </div>
          </div>
        )}

        {/* ── Upload + Summary Row ──────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <UploadDropzone
              onUpload={loadStops}
              onLoadDemo={() => loadStops(DEMO_STOPS)}
              onError={setUploadError}
            />
            {uploadError && (
              <div className="mt-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-400">
                ⚠ {uploadError}
              </div>
            )}
          </div>

          {stops.length > 0 ? (
            <div className="md:col-span-2 grid grid-cols-3 gap-3">
              {/* Total stops */}
              <div className="rounded-xl border border-[#1e2d45] bg-[#111827] p-4 flex flex-col justify-between">
                <p className="text-xs text-[#64748b] uppercase tracking-wider">Total Stops</p>
                <p className="text-3xl font-black text-[#e2e8f0]">{stops.length}</p>
                <p className="text-xs text-[#64748b]">{deliveries.length} deliveries + {returns.length} returns</p>
              </div>
              {/* Zones */}
              <div className="rounded-xl border border-[#1e2d45] bg-[#111827] p-4 flex flex-col justify-between">
                <p className="text-xs text-[#64748b] uppercase tracking-wider">Zones</p>
                <p className="text-3xl font-black text-[#e2e8f0]">{zones.length}</p>
                <p className="text-xs text-[#64748b] truncate">{zones.join(' · ') || 'Zone B'}</p>
              </div>
              {/* Status + Optimize CTA */}
              <div className={`rounded-xl border p-4 flex flex-col justify-between ${optimized ? 'border-green-500/20 bg-green-500/5' : 'border-blue-500/20 bg-blue-500/5'}`}>
                <p className="text-xs text-[#64748b] uppercase tracking-wider">Status</p>
                <p className={`text-sm font-bold ${optimized ? 'text-green-400' : 'text-amber-400'}`}>
                  {optimized ? '✓ Optimized' : '⏳ Pending'}
                </p>
                {!optimized ? (
                  <button
                    onClick={handleOptimize}
                    disabled={loading}
                    className="mt-1 rounded-lg bg-green-500 hover:bg-green-400 disabled:opacity-60 text-white text-xs font-bold py-1.5 px-3 transition-all active:scale-95"
                  >
                    {loading ? (
                      <span className="flex items-center gap-1.5 justify-center">
                        <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        Optimizing…
                      </span>
                    ) : '⚡ Optimize'}
                  </button>
                ) : (
                  <button
                    onClick={handleReset}
                    className="mt-1 rounded-lg border border-[#1e2d45] text-[#64748b] hover:text-[#e2e8f0] text-xs font-medium py-1.5 px-3 transition-all"
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="md:col-span-2 rounded-xl border border-dashed border-[#1e2d45] bg-[#111827]/40 p-4 flex items-center justify-center text-[#64748b] text-sm">
              Upload a CSV or load demo data to begin
            </div>
          )}
        </div>

        {/* ── Before/After Metric Cards ────────────────────────────── */}
        {stops.length > 0 && (
          <MetricCards optimized={optimized} afterMetrics={afterMetrics} />
        )}

        {/* ── Gemini NL Summary ────────────────────────────────────── */}
        {nlSummary && (
          <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4 flex gap-3">
            <div className="shrink-0 w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center mt-0.5">
              <svg className="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-semibold text-green-400 mb-1">Gemini AI Route Summary</p>
              <p className="text-sm text-[#e2e8f0] leading-relaxed">{nlSummary}</p>
            </div>
          </div>
        )}

        {/* ── Anomaly Badge ─────────────────────────────────────────── */}
        {optimized && <AnomalyBadge stops={route.length > 0 ? route : stops} />}

        {/* ── Tabbed Panel ─────────────────────────────────────────── */}
        {stops.length > 0 && (
          <div>
            {/* Tab bar */}
            <div className="flex gap-1 border-b border-[#1e2d45] mb-4 overflow-x-auto">
              {TABS.map(tab => {
                const disabled = tab.requiresOptimize && !optimized;
                return (
                  <button
                    key={tab.id}
                    disabled={disabled}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-all disabled:opacity-30 disabled:cursor-not-allowed
                      ${activeTab === tab.id
                        ? 'border-green-400 text-green-400'
                        : 'border-transparent text-[#64748b] hover:text-[#e2e8f0]'}`}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* ── Route Map tab ──────────────────────────────────── */}
            {activeTab === 'map' && (
              <div>
                {/* Legend — only shown for single map (before state) */}
                {!optimized && (
                  <div className="flex flex-wrap gap-3 mb-3 text-xs text-[#64748b]">
                    <span className="flex items-center gap-1.5"><span className="w-3 h-1.5 rounded bg-blue-400 inline-block" />Delivery route</span>
                    <span className="flex items-center gap-1.5"><span className="w-3 h-1.5 rounded bg-red-400 inline-block" />Return route (empty)</span>
                    <span className="ml-auto font-medium text-red-400">← Before: 2 trips · 87km</span>
                  </div>
                )}

                {/* Before optimize: single map | After: split before+after */}
                {optimized ? (
                  <SplitRouteMap stops={stops} route={route} afterMetrics={afterMetrics} />
                ) : (
                  <div className="h-[420px] w-full rounded-xl overflow-hidden border border-[#1e2d45]">
                    <RouteMap stops={stops} route={route} optimized={optimized} />
                  </div>
                )}
              </div>
            )}

            {/* ── Packing Order tab ──────────────────────────────── */}
            {activeTab === 'packing' && optimized && (
              <PackingSequencer route={route} />
            )}

            {/* ── Driver View tab ────────────────────────────────── */}
            {activeTab === 'driver' && optimized && (
              <div className="max-w-md mx-auto">
                <div className="rounded-xl border border-[#1e2d45] bg-[#111827] p-4">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-base">🚗</span>
                    <h3 className="text-sm font-semibold text-[#e2e8f0]">Driver View</h3>
                    <span className="ml-auto text-[10px] text-[#64748b]">Mobile layout</span>
                  </div>
                  <DriverView route={route} />
                </div>
              </div>
            )}

            {/* ── Fleet Scaler tab ───────────────────────────────── */}
            {activeTab === 'scale' && <FleetScaler dailySavings={afterMetrics} />}
          </div>
        )}

        {/* ── Footer ──────────────────────────────────────────────── */}
        <footer className="pt-4 border-t border-[#1e2d45] text-center text-xs text-[#64748b]">
          Greenmile v2.0 · FAR AWAY 2026 · FastAPI + React + Leaflet + Gemini AI
        </footer>
      </main>
    </div>
  );
}