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
  const [ranking, setRanking] = useState('HIPOTECARIO');
  const [rows, setRows] = useState<Row[]>([]);
  const [quality, setQuality] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    setStatus('loading');
    fetch(`${API}/api/rankings?ranking=${ranking}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('No se pudo cargar el ranking')))
      .then((body) => { setRows(body.rankings); setQuality(body.quality); setStatus('ready'); })
      .catch((reason) => { setError(reason.message); setStatus('error'); });
  }, [ranking]);

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
    <section className="mx-auto mt-8 max-w-7xl rounded-3xl bg-white p-5 shadow-xl md:p-8">
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
    </section>
  </main>;
}
