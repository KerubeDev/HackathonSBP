'use client';

import { useEffect, useMemo, useState } from 'react';
import Chart from '../components/Chart';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const activities = ['HIPOTECARIO', 'CONSTRUCCION', 'INDUSTRIA', 'AGROPECUARIO', 'COMERCIO', 'CONSUMO'];

type Row = {
  Posicion: number; Codigo_Banco: string; Banco: string; Saldo_Actividad: string;
  Total_Cartera_Local_Valida: string; Ponderacion_Pct: string;
};

export default function Home() {
  const [profile, setProfile] = useState('publico');
  const [view, setView] = useState('rankings');
  const [ranking, setRanking] = useState('HIPOTECARIO');
  const [rows, setRows] = useState<Row[]>([]);
  const [quality, setQuality] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const [comparison, setComparison] = useState<any>(null);
  const [upload, setUpload] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState('');

  const navigation = profile === 'publico'
    ? [{ id: 'rankings', label: 'Rankings' }, { id: 'exports', label: 'Descargas' }]
    : profile === 'analista'
      ? [{ id: 'rankings', label: 'Rankings' }, { id: 'comparisons', label: 'Comparaciones' }, { id: 'exports', label: 'Reportes' }]
      : [{ id: 'rankings', label: 'Rankings' }, { id: 'quality', label: 'Calidad' }, { id: 'admin', label: 'Cargar período' }, { id: 'exports', label: 'Exportaciones' }];

  useEffect(() => {
    setStatus('loading');
    fetch(`${API}/api/rankings?ranking=${ranking}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('No se pudo cargar el ranking')))
      .then((body) => { setRows(body.rankings); setQuality(body.quality); setStatus('ready'); })
      .catch((reason) => { setError(reason.message); setStatus('error'); });
  }, [ranking]);

  useEffect(() => {
    if (view === 'comparisons' && !comparison) {
      fetch(`${API}/api/comparisons`).then((response) => response.json()).then(setComparison)
        .catch(() => setError('No se pudieron cargar las comparaciones'));
    }
  }, [view, comparison]);

  function download(extension: string) {
    window.open(`${API}/api/exports/rankings.${extension}?ranking=${ranking}`, '_blank');
  }

  async function previewUpload() {
    if (!upload) return;
    setUploadMessage('Validando archivo…');
    const form = new FormData();
    form.append('file', upload);
    const response = await fetch(`${API}/api/rankings/preview`, { method: 'POST', headers: { 'x-profile': 'administrador' }, body: form });
    const body = await response.json();
    setUploadMessage(body.errors?.length ? `Archivo inválido: ${body.errors.join(', ')}` : `Preview correcto: ${body.rows} filas · SHA-256 ${body.sha256}`);
  }

  const visibleRows = useMemo(() => rows.filter((row) =>
    !query || `${row.Banco} ${row.Codigo_Banco}`.toLowerCase().includes(query.toLowerCase())), [rows, query]);
  const chart = { xAxis: { type: 'category', data: visibleRows.map((r) => r.Codigo_Banco) },
    yAxis: { type: 'value' }, series: [{ type: 'bar', data: visibleRows.map((r) => Number(r.Saldo_Actividad)) }] };

  return <main className="min-h-screen px-5 py-8 md:px-12">
    <header className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
      <div><span className="rounded-full bg-[var(--lime)] px-4 py-2 text-sm font-bold">SBP RANKING</span>
        <h1 className="mt-5 text-4xl font-black md:text-6xl">Crédito por actividad</h1></div>
      <label className="text-sm font-bold">Perfil
        <select value={profile} onChange={(e) => setProfile(e.target.value)} className="ml-2 rounded-lg border-2 p-2">
          <option value="publico">Público</option><option value="analista">Analista</option><option value="administrador">Administrador</option>
        </select>
      </label>
    </header>
    <nav aria-label="Navegación principal" className="mx-auto mt-8 flex max-w-7xl flex-wrap gap-2">
      {navigation.map((item) => <button key={item.id} onClick={() => setView(item.id)}
        className={`rounded-xl px-4 py-2 font-bold ${view === item.id ? 'bg-[var(--ink)] text-white' : 'bg-white'}`}>{item.label}</button>)}
    </nav>
    <section className="mx-auto mt-8 max-w-7xl rounded-3xl bg-white p-5 shadow-xl md:p-8">
      {view === 'comparisons' && <section aria-labelledby="comparison-title">
        <h2 id="comparison-title" className="text-2xl font-black">Movimientos entre períodos</h2>
        {!comparison ? <p className="py-8" aria-live="polite">Cargando comparaciones…</p> :
          <div className="mt-4 overflow-x-auto"><table className="w-full text-left"><thead><tr className="border-b-2"><th>Ranking</th><th>Banco</th><th>Cambio posición</th><th>Variación saldo</th><th>Significativo</th></tr></thead>
            <tbody>{comparison.movements.map((item: any) => <tr key={`${item.Ranking}-${item.Codigo_Banco}`} className="border-b"><td className="py-2">{item.Ranking}</td><td>{item.Banco}</td><td>{item.Cambio_Posicion}</td><td>{item.Var_Saldo_Pct}%</td><td>{item.significant ? 'Sí' : 'No'}</td></tr>)}</tbody>
          </table></div>}
      </section>}
      {view === 'admin' && <section aria-labelledby="upload-title">
        <h2 id="upload-title" className="text-2xl font-black">Carga administrativa</h2>
        <p className="mt-2 text-sm opacity-70">Solo se publica después de validar el preview. El backend exige la capacidad administrador.</p>
        <input className="mt-5 block" type="file" accept=".csv" onChange={(event) => setUpload(event.target.files?.[0] || null)} />
        <button onClick={previewUpload} disabled={!upload} className="mt-4 rounded-xl bg-[var(--ink)] px-4 py-2 font-bold text-white disabled:opacity-40">Validar preview</button>
        {uploadMessage && <p className="mt-4" aria-live="polite">{uploadMessage}</p>}
      </section>}
      {view === 'quality' && <section aria-labelledby="quality-title"><h2 id="quality-title" className="text-2xl font-black">Calidad de datos</h2>
        <p className="mt-4">Período: {quality?.period || '—'} · Válidas: {quality?.valid_universe || 0}</p>
        <ul className="mt-3 grid gap-2 md:grid-cols-4">{['E1', 'E2', 'E3', 'E4'].map((code) => <li key={code} className="rounded-xl bg-[var(--mint)] p-3">{code}: {quality?.[code] || 0}</li>)}</ul>
      </section>}
      {view === 'exports' && <section aria-labelledby="exports-title"><h2 id="exports-title" className="text-2xl font-black">Descargas</h2>
        <div className="mt-5 flex flex-wrap gap-3">{['csv', 'json', 'xlsx', 'pdf'].map((extension) => <button key={extension} onClick={() => download(extension)} className="rounded-xl bg-[var(--ink)] px-4 py-2 font-bold text-white">{extension.toUpperCase()}</button>)}</div>
      </section>}
      {view !== 'rankings' && <div className="mt-8 border-t pt-8" />}
      {view === 'rankings' && <div>
      <div className="flex flex-wrap gap-3">{activities.map((name) =>
        <button key={name} onClick={() => setRanking(name)} className={`rounded-full px-4 py-2 text-sm font-bold ${ranking === name ? 'bg-[var(--ink)] text-white' : 'bg-[var(--mint)]'}`}>{name}</button>)}</div>
      <div className="mt-6 grid gap-4 md:grid-cols-[1fr_auto]">
        <input aria-label="Buscar banco" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar banco o código" className="rounded-xl border-2 p-3" />
        <div className="rounded-xl bg-[var(--mint)] px-4 py-3 text-sm">Datos ficticios · Corte {quality?.period || '—'} · Regla sbp-2026-v2</div>
      </div>
      {status === 'loading' && <p className="py-10" aria-live="polite">Cargando ranking…</p>}
      {status === 'error' && <p className="py-10 text-red-700" role="alert">{error}</p>}
      {status === 'ready' && <><div className="mt-6"><Chart config={chart} /></div>
        <div className="mt-6 overflow-x-auto"><table className="w-full text-left">
          <caption className="sr-only">Ranking {ranking}</caption><thead><tr className="border-b-2"><th>Posición</th><th>Banco</th><th>Saldo</th><th>Cartera válida</th><th>Ponderación</th></tr></thead>
          <tbody>{visibleRows.map((row) => <tr key={row.Codigo_Banco} className="border-b"><td className="py-3">{row.Posicion}</td><td>{row.Banco} ({row.Codigo_Banco})</td><td>{row.Saldo_Actividad}</td><td>{row.Total_Cartera_Local_Valida}</td><td>{row.Ponderacion_Pct}%</td></tr>)}</tbody>
        </table></div><p className="mt-4 text-sm opacity-70">Calidad: {quality?.valid_universe} filas válidas · E1 {quality?.E1} · E2 {quality?.E2} · E3 {quality?.E3} · E4 {quality?.E4}</p></>}
      </div>}
      </section>
  </main>;
}
