
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
interface Auction {
  id: number;
  seller_id: number;
  crop_name: string;
  crop_variety?: string | null;
  category?: string | null;
  quantity: number | string;
  unit: string;
  starting_price: number | string;
  expected_price?: number | string | null;
  location?: string | null;
  start_time: string;
  end_time: string;
  status: string;
  created_at: string;
  updated_at: string;
  highest_bid?: number | string | null;
  bid_count: number;
}

interface AuctionResponse {
  items: Auction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const API = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) {
      throw new Error('Please log in to perform this action.');
    }
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

const rupees = (value?: number | string | null) =>
  value == null
    ? '—'
    : `₹${Number(value).toLocaleString('en-IN', {
        maximumFractionDigits: 2,
      })}`;

const formatDate = (value: string) =>
  new Date(value).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

const emptyForm = {
  crop_name: '',
  crop_variety: '',
  category: '',
  quantity: '',
  unit: 'kg',
  starting_price: '',
  expected_price: '',
  location: '',
  start_time: '',
  end_time: '',
};

export default function AuctionsPage() {
  const [auctions, setAuctions] = useState<AuctionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(emptyForm);
  const [bidAmounts, setBidAmounts] = useState<Record<number, string>>({});
  const [biddingOn, setBiddingOn] = useState<number | null>(null);

  const loadAuctions = useCallback(async () => {
    setLoading(true);
    setLoadError('');

    try {
      const result = await request<AuctionResponse>(
        `/auctions/?page=${page}&page_size=20`,
      );
      setAuctions(result);
    } catch (err) {
      setLoadError(
        err instanceof Error ? err.message : 'Unable to load auctions.',
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void loadAuctions();
  }, [loadAuctions]);

  function updateField(key: keyof typeof emptyForm, value: string) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function createAuction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setMessage('');

    if (!localStorage.getItem('token')) {
      setError('Please log in before creating an auction.');
      return;
    }

    if (new Date(form.start_time) >= new Date(form.end_time)) {
      setError('End time must be later than start time.');
      return;
    }

    setSaving(true);

    try {
      const payload = {
        crop_name: form.crop_name.trim(),
        crop_variety: form.crop_variety.trim() || null,
        category: form.category.trim() || null,
        quantity: Number(form.quantity),
        unit: form.unit,
        starting_price: Number(form.starting_price),
        expected_price: form.expected_price
          ? Number(form.expected_price)
          : null,
        location: form.location.trim() || null,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
      };

      await request<Auction>('/auctions/', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setForm(emptyForm);
      setShowForm(false);
      setMessage('Auction created successfully.');
      setPage(1);

      // Reload the first page so the new auction appears.
      if (page !== 1) {
        setPage(1);
      } else {
        await loadAuctions();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not create auction.',
      );
    } finally {
      setSaving(false);
    }
  }

  async function placeBid(
    event: FormEvent<HTMLFormElement>,
    auction: Auction,
  ) {
    event.preventDefault();
    setError('');
    setMessage('');

    if (!localStorage.getItem('token')) {
      setError('Please log in before placing a bid.');
      return;
    }

    const amount = Number(bidAmounts[auction.id]);
    const currentHighest =
      auction.highest_bid == null
        ? Number(auction.starting_price)
        : Number(auction.highest_bid);

    if (!Number.isFinite(amount) || amount <= currentHighest) {
      setError(`Your bid must be higher than ${rupees(currentHighest)}.`);
      return;
    }

    setBiddingOn(auction.id);

    try {
      await request(`/auctions/${auction.id}/bid`, {
        method: 'POST',
        body: JSON.stringify({ amount }),
      });

      setBidAmounts((previous) => ({ ...previous, [auction.id]: '' }));
      setMessage(`Bid submitted for ${auction.crop_name}.`);
      await loadAuctions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not place bid.');
    } finally {
      setBiddingOn(null);
    }
  }

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
      <section className="flex flex-col justify-between gap-4 rounded-2xl bg-gradient-to-r from-green-950 to-emerald-700 p-6 text-white sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-green-200">
            KrishiSetu Marketplace
          </p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Crop Auctions
          </h1>
          <p className="mt-2 text-green-50">
            Discover crop auctions, publish your harvest, and participate in
            live bidding.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setShowForm((previous) => !previous);
            setError('');
            setMessage('');
          }}
          className="rounded-xl bg-white px-5 py-3 font-semibold text-green-900 hover:bg-green-50"
        >
          {showForm ? 'Close form' : '+ Create Auction'}
        </button>
      </section>

      {message && (
        <div
          role="status"
          className="rounded-xl border border-green-200 bg-green-50 p-4 text-green-800"
        >
          {message}
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800"
        >
          {error}
        </div>
      )}

      {showForm && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <h2 className="text-xl font-bold text-slate-900">
            Create a Crop Auction
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Enter the crop details and auction schedule.
          </p>

          <form
            onSubmit={createAuction}
            className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            <label className="text-sm font-medium text-slate-700">
              Crop name *
              <input
                required
                maxLength={255}
                value={form.crop_name}
                onChange={(e) => updateField('crop_name', e.target.value)}
                placeholder="e.g. Onion"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Variety
              <input
                value={form.crop_variety}
                onChange={(e) => updateField('crop_variety', e.target.value)}
                placeholder="e.g. Red onion"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Category
              <input
                value={form.category}
                onChange={(e) => updateField('category', e.target.value)}
                placeholder="e.g. Vegetables"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Quantity *
              <input
                required
                type="number"
                min="0.01"
                step="0.01"
                value={form.quantity}
                onChange={(e) => updateField('quantity', e.target.value)}
                placeholder="Available quantity"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Unit *
              <select
                required
                value={form.unit}
                onChange={(e) => updateField('unit', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              >
                <option value="kg">Kilogram (kg)</option>
                <option value="quintal">Quintal</option>
                <option value="ton">Ton</option>
                <option value="piece">Piece</option>
                <option value="dozen">Dozen</option>
                <option value="bag">Bag</option>
              </select>
            </label>

            <label className="text-sm font-medium text-slate-700">
              Starting price (₹) *
              <input
                required
                type="number"
                min="0.01"
                step="0.01"
                value={form.starting_price}
                onChange={(e) => updateField('starting_price', e.target.value)}
                placeholder="Minimum price"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Expected price (₹)
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={form.expected_price}
                onChange={(e) => updateField('expected_price', e.target.value)}
                placeholder="Optional target price"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700 sm:col-span-2">
              Location
              <input
                value={form.location}
                onChange={(e) => updateField('location', e.target.value)}
                placeholder="Village, market, district"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Start date and time *
              <input
                required
                type="datetime-local"
                value={form.start_time}
                onChange={(e) => updateField('start_time', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              End date and time *
              <input
                required
                type="datetime-local"
                value={form.end_time}
                onChange={(e) => updateField('end_time', e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              />
            </label>

            <div className="sm:col-span-2 lg:col-span-3">
              <button
                disabled={saving}
                type="submit"
                className="rounded-xl bg-green-800 px-5 py-3 font-semibold text-white hover:bg-green-900 disabled:opacity-60"
              >
                {saving ? 'Saving...' : 'Save Auction'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              Available Auctions
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Listings are fetched from the backend.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadAuctions()}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {loading && (
          <div className="rounded-xl border bg-white p-8 text-center text-slate-600">
            Loading auctions...
          </div>
        )}

        {!loading && loadError && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
            <p className="font-semibold">Could not load auctions</p>
            <p className="mt-1 text-sm">{loadError}</p>
            <button
              type="button"
              onClick={() => void loadAuctions()}
              className="mt-3 rounded-lg bg-amber-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Try Again
            </button>
          </div>
        )}

        {!loading && !loadError && auctions?.items.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <div className="text-4xl">🌾</div>
            <h3 className="mt-3 text-lg font-bold">No auctions yet</h3>
            <p className="mt-1 text-slate-600">
              Create an auction to list your crop.
            </p>
          </div>
        )}

        {!loading && !loadError && auctions && auctions.items.length > 0 && (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {auctions.items.map((auction) => {
                const currentPrice =
                  auction.highest_bid == null
                    ? Number(auction.starting_price)
                    : Number(auction.highest_bid);

                const isLive = auction.status.toLowerCase() === 'live';

                const badge =
                  auction.status.toLowerCase() === 'live'
                    ? 'bg-green-100 text-green-800'
                    : auction.status.toLowerCase() === 'scheduled'
                      ? 'bg-blue-100 text-blue-800'
                      : auction.status.toLowerCase() === 'completed'
                        ? 'bg-slate-100 text-slate-700'
                        : 'bg-amber-100 text-amber-800';

                return (
                  <article
                    key={auction.id}
                    className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-green-700">
                          {auction.category || 'Crop auction'}
                        </p>
                        <h3 className="mt-1 text-xl font-bold text-slate-900">
                          {auction.crop_name}
                        </h3>
                        {auction.crop_variety && (
                          <p className="text-sm text-slate-600">
                            {auction.crop_variety}
                          </p>
                        )}
                      </div>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${badge}`}
                      >
                        {auction.status}
                      </span>
                    </div>

                    <div className="mt-5 grid grid-cols-2 gap-3">
                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">Quantity</p>
                        <p className="mt-1 font-semibold">
                          {Number(auction.quantity).toLocaleString('en-IN')}{' '}
                          {auction.unit}
                        </p>
                      </div>

                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">Highest bid</p>
                        <p className="mt-1 font-semibold text-green-800">
                          {rupees(auction.highest_bid ?? auction.starting_price)}
                        </p>
                      </div>

                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">Starting price</p>
                        <p className="mt-1 font-semibold">
                          {rupees(auction.starting_price)}
                        </p>
                      </div>

                      <div className="rounded-xl bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">Total bids</p>
                        <p className="mt-1 font-semibold">
                          {auction.bid_count}
                        </p>
                      </div>
                    </div>

                    {auction.expected_price != null && (
                      <p className="mt-3 text-sm text-slate-600">
                        Expected price:{' '}
                        <strong>{rupees(auction.expected_price)}</strong>
                      </p>
                    )}

                    {auction.location && (
                      <p className="mt-3 text-sm text-slate-600">
                        📍 {auction.location}
                      </p>
                    )}

                    <div className="mt-4 space-y-1 text-xs text-slate-500">
                      <p>Starts: {formatDate(auction.start_time)}</p>
                      <p>Ends: {formatDate(auction.end_time)}</p>
                    </div>

                    <div className="mt-auto pt-5">
                      {isLive ? (
                        <form
                          onSubmit={(event) => void placeBid(event, auction)}
                          className="flex gap-2"
                        >
                          <label
                            htmlFor={`bid-${auction.id}`}
                            className="sr-only"
                          >
                            Bid amount
                          </label>
                          <input
                            id={`bid-${auction.id}`}
                            required
                            type="number"
                            min={currentPrice + 0.01}
                            step="0.01"
                            value={bidAmounts[auction.id] || ''}
                            onChange={(event) =>
                              setBidAmounts((previous) => ({
                                ...previous,
                                [auction.id]: event.target.value,
                              }))
                            }
                            placeholder={`Above ${rupees(currentPrice)}`}
                            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2"
                          />
                          <button
                            type="submit"
                            disabled={biddingOn === auction.id}
                            className="rounded-lg bg-green-800 px-4 py-2 font-semibold text-white hover:bg-green-900 disabled:opacity-60"
                          >
                            {biddingOn === auction.id ? 'Bidding...' : 'Bid'}
                          </button>
                        </form>
                      ) : (
                        <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
                          {auction.status.toLowerCase() === 'scheduled'
                            ? 'Scheduled — bidding is not open yet.'
                            : auction.status.toLowerCase() === 'completed'
                              ? 'This auction has ended.'
                              : auction.status.toLowerCase() === 'cancelled'
                                ? 'This auction was cancelled.'
                                : 'Bidding is unavailable.'}
                        </p>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-slate-600">
                {auctions.total} auctions · Page {auctions.page} of{' '}
                {Math.max(auctions.total_pages, 1)}
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={page >= auctions.total_pages}
                  onClick={() => setPage((value) => value + 1)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
