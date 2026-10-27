
import { useCallback, useEffect, useState } from 'react';
import { offersApi, type Offer } from '../../api/client';
import { useAuth } from '../../stores/auth';

type Tab = 'received' | 'sent';

function money(value: number | string, currency = 'INR') {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function date(value: string) {
  return new Date(value).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function statusStyle(status: string) {
  switch (status.toLowerCase()) {
    case 'accepted':
      return 'bg-green-100 text-green-800';
    case 'rejected':
    case 'withdrawn':
    case 'expired':
      return 'bg-red-100 text-red-700';
    case 'pending':
      return 'bg-amber-100 text-amber-800';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export default function BuyerRequestsPage() {
  const { user } = useAuth();
  const isBuyer = ['buyer', 'businessman', 'business', 'fpo_admin'].includes(
    user?.role?.toLowerCase() ?? '',
  );

  const [tab, setTab] = useState<Tab>(isBuyer ? 'sent' : 'received');
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState('');
  const [counterId, setCounterId] = useState<number | null>(null);
  const [counterPrice, setCounterPrice] = useState('');
  const [counterQuantity, setCounterQuantity] = useState('');
  const [counterNotes, setCounterNotes] = useState('');

  const loadOffers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = tab === 'received'
        ? await offersApi.received()
        : await offersApi.sent();
      setOffers(result.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load offers.');
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    void loadOffers();
  }, [loadOffers]);

  async function performAction(
    offer: Offer,
    action: 'accept' | 'reject' | 'withdraw',
  ) {
    const labels = {
      accept: 'accept this offer',
      reject: 'reject this offer',
      withdraw: 'withdraw this offer',
    };

    if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) return;

    setBusyId(offer.id);
    setError('');
    setNotice('');

    try {
      await offersApi.action(offer.id, action);
      setNotice(`Offer #${offer.id} ${action}ed successfully.`);
      await loadOffers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The action failed.');
    } finally {
      setBusyId(null);
    }
  }

  async function submitCounter(offer: Offer) {
    const price = Number(counterPrice);
    const quantity = counterQuantity.trim() ? Number(counterQuantity) : undefined;

    if (!Number.isFinite(price) || price <= 0) {
      setError('Enter a valid counteroffer price.');
      return;
    }
    if (quantity !== undefined && (!Number.isFinite(quantity) || quantity <= 0)) {
      setError('Enter a valid quantity.');
      return;
    }

    setBusyId(offer.id);
    setError('');
    setNotice('');

    try {
      await offersApi.counter(offer.id, {
        offered_price: price,
        ...(quantity !== undefined ? { quantity } : {}),
        notes: counterNotes.trim() || undefined,
      });
      setCounterId(null);
      setCounterPrice('');
      setCounterQuantity('');
      setCounterNotes('');
      setNotice('Counteroffer submitted successfully.');
      await loadOffers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit counteroffer.');
    } finally {
      setBusyId(null);
    }
  }

  function changeTab(nextTab: Tab) {
    setTab(nextTab);
    setNotice('');
    setError('');
    setCounterId(null);
  }

  return (
    <main className="mx-auto max-w-6xl p-4 sm:p-6">
      <header className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-green-700">
          KrishiSetu Marketplace
        </p>
        <h1 className="mt-1 text-2xl font-bold text-green-950 sm:text-3xl">
          Buyer Requests & Offers
        </h1>
        <p className="mt-2 text-gray-600">
          Review offers, negotiate prices, and manage crop transactions.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => changeTab('received')}
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${
            tab === 'received'
              ? 'bg-green-800 text-white'
              : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          Incoming offers
        </button>
        <button
          type="button"
          onClick={() => changeTab('sent')}
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${
            tab === 'sent'
              ? 'bg-green-800 text-white'
              : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          My sent offers
        </button>
        <button
          type="button"
          onClick={() => void loadOffers()}
          disabled={loading}
          className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {notice && (
        <div role="status" className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          {notice}
        </div>
      )}

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <p>{error}</p>
          <button type="button" onClick={() => void loadOffers()} className="mt-2 font-semibold underline">
            Try again
          </button>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-gray-200 bg-white p-10 text-center text-gray-500">
          Loading offers from the server…
        </div>
      ) : offers.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-10 text-center">
          <h2 className="text-lg font-semibold text-gray-800">
            {tab === 'received' ? 'No incoming offers yet' : 'No sent offers yet'}
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            {tab === 'received'
              ? 'Offers from buyers will appear here when they make an offer on your listings.'
              : 'Offers you submit for available crops will appear here.'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {offers.map((offer) => {
            const canAct = offer.status.toLowerCase() === 'pending';
            const counterOpen = counterId === offer.id;

            return (
              <article key={offer.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">
                      {offer.listing_crop_name || `Crop listing #${offer.listing_id}`}
                    </h2>
                    <p className="mt-1 text-sm text-gray-600">
                      {tab === 'received'
                        ? `Buyer: ${offer.buyer_name || `User #${offer.buyer_id}`}`
                        : `Seller: ${offer.seller_name || `User #${offer.seller_id}`}`}
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${statusStyle(offer.status)}`}>
                    {offer.status.replaceAll('_', ' ')}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div className="rounded-lg bg-green-50 p-3">
                    <p className="text-xs text-gray-600">Offered price</p>
                    <p className="mt-1 font-bold text-green-900">
                      {money(offer.offered_price, offer.currency)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-600">Quantity</p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {Number(offer.quantity).toLocaleString('en-IN')} {offer.unit}
                    </p>
                  </div>
                  <div className="col-span-2 rounded-lg bg-gray-50 p-3 sm:col-span-1">
                    <p className="text-xs text-gray-600">Submitted</p>
                    <p className="mt-1 font-semibold text-gray-900">{date(offer.created_at)}</p>
                  </div>
                </div>

                {offer.notes && (
                  <p className="mt-3 whitespace-pre-wrap text-sm text-gray-700">
                    <span className="font-semibold">Notes: </span>{offer.notes}
                  </p>
                )}

                {canAct && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {tab === 'received' ? (
                      <>
                        <button
                          type="button"
                          disabled={busyId === offer.id}
                          onClick={() => void performAction(offer, 'accept')}
                          className="rounded-lg bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-800 disabled:opacity-50"
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          disabled={busyId === offer.id}
                          onClick={() => void performAction(offer, 'reject')}
                          className="rounded-lg border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                        >
                          Reject
                        </button>
                        <button
                          type="button"
                          disabled={busyId === offer.id}
                          onClick={() => {
                            setCounterId(counterOpen ? null : offer.id);
                            setCounterPrice(String(offer.offered_price));
                            setCounterQuantity(String(offer.quantity));
                            setCounterNotes('');
                            setError('');
                          }}
                          className="rounded-lg border border-green-200 px-4 py-2 text-sm font-semibold text-green-800 hover:bg-green-50 disabled:opacity-50"
                        >
                          Counteroffer
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        disabled={busyId === offer.id}
                        onClick={() => void performAction(offer, 'withdraw')}
                        className="rounded-lg border border-red-200 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                      >
                        Withdraw offer
                      </button>
                    )}
                  </div>
                )}

                {counterOpen && tab === 'received' && canAct && (
                  <form
                    className="mt-4 grid gap-3 rounded-lg border border-green-100 bg-green-50 p-4 sm:grid-cols-2"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void submitCounter(offer);
                    }}
                  >
                    <label className="text-sm font-medium text-gray-700">
                      Counter price (INR)
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        value={counterPrice}
                        onChange={(event) => setCounterPrice(event.target.value)}
                        className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
                      />
                    </label>
                    <label className="text-sm font-medium text-gray-700">
                      Quantity ({offer.unit})
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={counterQuantity}
                        onChange={(event) => setCounterQuantity(event.target.value)}
                        className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
                      />
                    </label>
                    <label className="text-sm font-medium text-gray-700 sm:col-span-2">
                      Message (optional)
                      <textarea
                        rows={2}
                        value={counterNotes}
                        onChange={(event) => setCounterNotes(event.target.value)}
                        className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
                      />
                    </label>
                    <div className="flex gap-2 sm:col-span-2">
                      <button
                        type="submit"
                        disabled={busyId === offer.id}
                        className="rounded-lg bg-green-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                      >
                        {busyId === offer.id ? 'Submitting…' : 'Send counteroffer'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setCounterId(null)}
                        className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
