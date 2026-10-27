import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../stores/auth';

interface Price {
  id: number; crop_name: string; variety?: string | null; market_name: string;
  district?: string | null; state?: string | null; min_price?: number | string | null;
  max_price?: number | string | null; modal_price?: number | string | null;
  price_unit: string; currency: string; reporting_date: string; source_name?: string | null;
  freshness?: string | null;
}
interface PriceResponse { items: Price[]; total: number; page: number; page_size: number }
const money = (value: number | string | null | undefined) => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN')}`;

export default function MarketPricesPage() {
  const { user } = useAuth();
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');
  const [crop, setCrop] = useState('');
  const [district, setDistrict] = useState('');
  const [state, setState] = useState('');
  const [market, setMarket] = useState('');
  const [prices, setPrices] = useState<PriceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    const params = new URLSearchParams({ page: '1', page_size: '100' });
    if (crop.trim()) params.set('crop_name', crop.trim());
    if (district.trim()) params.set('district', district.trim());
    if (state.trim()) params.set('state', state.trim());
    if (market.trim()) params.set('market_name', market.trim());
    try {
      const response = await fetch(`/api/v1/market-prices?${params}`);
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `API error ${response.status}`);
      setPrices(await response.json());
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load market prices'); }
    finally { setLoading(false); }
  }, [crop, district, state, market]);
  useEffect(() => { void load(); }, [load]);
  async function syncOfficialSource() {
    setSyncing(true); setSyncMessage(''); setError('');
    try { const r = await fetch('/api/v1/market-prices/sync?limit=500', { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` } }); const data = await r.json().catch(() => ({})); if (!r.ok) throw new Error(data.detail || `Sync failed (${r.status})`); setSyncMessage(`Official source sync complete: ${data.inserted} inserted, ${data.updated} updated, ${data.skipped} skipped.`); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Official source sync failed'); } finally { setSyncing(false); }
  }
  return <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
    <header className="rounded-2xl bg-gradient-to-r from-green-950 to-emerald-700 p-6 text-white">
      <p className="text-sm font-semibold uppercase tracking-widest text-green-200">KrishiSetu • Verified data only</p>
      <h1 className="mt-2 text-3xl font-bold">Market Prices</h1>
      <p className="mt-2 text-green-50">Market-reported prices stored in the application database. No prices are invented or shown as live without a source.</p>
    </header>
    {syncMessage && <div role="status" className="rounded-lg bg-green-50 p-3 text-green-800">{syncMessage}</div>}
    {user?.role === 'admin' && <section className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4"><div><h2 className="font-semibold">Official Agmarknet sync</h2><p className="text-sm text-gray-600">Requires DATA_GOV_IN_API_KEY in the backend environment. No demo prices are created.</p></div><button type="button" disabled={syncing} onClick={() => void syncOfficialSource()} className="rounded-lg bg-green-800 px-4 py-2 font-semibold text-white disabled:opacity-50">{syncing ? 'Syncing…' : 'Sync official prices'}</button></section>}
    <form className="grid gap-3 rounded-xl border bg-white p-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_1fr_auto_auto]" onSubmit={e => { e.preventDefault(); void load(); }}>
      <input value={crop} onChange={e => setCrop(e.target.value)} placeholder="Search crop (e.g. wheat)" className="rounded-lg border p-3" />
      <input value={district} onChange={e => setDistrict(e.target.value)} placeholder="District" className="rounded-lg border p-3" />
      <input value={state} onChange={e => setState(e.target.value)} placeholder="State (e.g. Maharashtra)" className="rounded-lg border p-3" />
      <input value={market} onChange={e => setMarket(e.target.value)} placeholder="Mandi / market (optional)" className="rounded-lg border p-3" />
      <button className="rounded-lg bg-green-800 px-5 py-3 font-semibold text-white">Search</button>
      <button type="button" onClick={() => { setCrop(''); setDistrict(''); setState(''); setMarket(''); }} className="rounded-lg border px-5 py-3">Clear</button>
    </form>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error} <button className="ml-2 underline" onClick={() => void load()}>Retry</button></div>}
    {loading ? <p className="rounded-xl border bg-white p-8 text-center">Loading prices from the backend…</p> : !prices?.items.length ? <section className="rounded-xl border border-dashed bg-white p-8 text-center sm:p-10"><h2 className="text-xl font-semibold">No saved prices match this region</h2><p className="mx-auto mt-2 max-w-2xl text-gray-600">This app only displays prices that have been fetched from the official source and saved in PostgreSQL. Your crop/region may not be in the current database yet. You can search the official mandi portal directly below.</p><div className="mt-5 flex flex-wrap justify-center gap-3"><a href="https://agmarknet.gov.in/" target="_blank" rel="noreferrer" className="rounded-lg bg-green-800 px-5 py-3 font-semibold text-white hover:bg-green-900">Search official Agmarknet ↗</a><a href="https://www.data.gov.in/" target="_blank" rel="noreferrer" className="rounded-lg border px-5 py-3 font-semibold">Open data.gov.in ↗</a></div><p className="mt-4 text-xs text-gray-500">For automatic results inside KrishiSetu, the backend administrator must configure a valid DATA_GOV_IN_API_KEY and sync the official dataset. No sample prices are substituted.</p></section> : <section className="overflow-x-auto rounded-xl border bg-white"><div className="border-b p-4 text-sm text-gray-600">{prices.total} database record(s) returned</div><table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-gray-50"><tr>{['Crop','Market','District','Min price','Modal price','Max price','Unit','Reported','Source'].map(h => <th key={h} className="p-3 font-semibold">{h}</th>)}</tr></thead><tbody>{prices.items.map(p => <tr key={p.id} className="border-t"><td className="p-3 font-semibold">{p.crop_name}{p.variety ? <span className="block font-normal text-gray-500">{p.variety}</span> : null}</td><td className="p-3">{p.market_name}</td><td className="p-3">{p.district || '—'}</td><td className="p-3">{money(p.min_price)}</td><td className="p-3 font-semibold text-green-800">{money(p.modal_price)}</td><td className="p-3">{money(p.max_price)}</td><td className="p-3">₹ / {p.price_unit}</td><td className="p-3">{p.reporting_date}</td><td className="p-3">{p.source_name || 'Unspecified'}</td></tr>)}</tbody></table></section>}
  </main>;
}
