import { useRef, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function UploadDropzone({ onUpload, onLoadDemo, onError }) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      onError?.('Only .csv files are accepted.');
      return;
    }
    setFileName(file.name);
    setUploading(true);
    onError?.('');

    const form = new FormData();
    form.append('file', file);

    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
      const json = await res.json();

      if (!res.ok) {
        onError?.(json.detail || 'Upload failed — check your CSV format.');
        setFileName('');
      } else {
        onUpload(json.data || []);
      }
    } catch (e) {
      onError?.('Cannot reach backend. Is the server running on port 8000?');
      setFileName('');
    }
    setUploading(false);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFile(e.dataTransfer.files[0]); }}
      onClick={() => fileRef.current.click()}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all duration-200 select-none
        ${isDragging
          ? 'border-green-400 bg-green-400/10 scale-[1.01]'
          : 'border-[#1e2d45] bg-[#111827] hover:border-green-500/50 hover:bg-[#1a2235]'
        }`}
    >
      <input
        ref={fileRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {/* Upload icon */}
      <div className="mx-auto w-10 h-10 rounded-lg bg-green-400/10 flex items-center justify-center mb-3">
        {uploading ? (
          <svg className="w-5 h-5 text-green-400 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        ) : (
          <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        )}
      </div>

      {/* Status text */}
      {uploading
        ? <p className="text-sm font-medium text-green-400">Uploading…</p>
        : fileName
          ? <p className="text-sm font-medium text-green-400">{fileName} ✓</p>
          : (
            <>
              <p className="text-sm font-semibold text-[#e2e8f0]">Drop CSV here or click to upload</p>
              <p className="text-xs text-[#64748b] mt-1">stop_id, type, lat, lng, weight_kg…</p>
            </>
          )
      }

      {/* Demo data link */}
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); onLoadDemo(); }}
        className="mt-3 text-xs font-medium text-green-400 hover:text-green-300 underline underline-offset-2"
      >
        or load seeded demo data ↗
      </button>
    </div>
  );
}
