
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  listingsApi,
  type Listing,
  type CropCatalogueItem,
} from '../../api/client';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import {
  Search, MapPin, IndianRupee, Package, Filter, Plus, X,
} from 'lucide-react';

type ListingForm = {
  crop_name: string;
  crop_variety: string;
  quantity: string;
  unit: string;
  asking_price: string;
  negotiability: string;
  district: string;
  state: string;
  village: string;
  pincode: string;
  delivery_preference: string;
};

const initialForm: ListingForm = {
  crop_name: '',
  crop_variety: '',
  quantity: '',
  unit: 'quintal',
  asking_price: '',
  negotiability: 'negotiable',
  district: '',
  state: 'Maharashtra',
  village: '',
  pincode: '',
  delivery_preference: 'both',
};

export function MarketplacePage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [district, setDistrict] = useState('');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ListingForm>(initialForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [catalogue, setCatalogue] = useState<CropCatalogueItem[]>([]);
  const [role, setRole] = useState('');

  const loadListings = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page, page_size: 20,
      };
      if (query.trim()) params.q = query.trim();
      if (district.trim()) params.district = district.trim();

      const result = await listingsApi.search(params);
      setListings(result.items ?? []);
      setTotal(result.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load listings.');
    } finally {
      setLoading(false);
    }
  }, [page, query, district]);

  useEffect(() => {
    void loadListings();
  }, [loadListings]);

  useEffect(() => {
    listingsApi.catalogue()
      .then(setCatalogue)
      .catch(() => setCatalogue([]));
  }, []);

  useEffect(() => {
    // Read the role from the authenticated profile, not from user input.
    import('../../api/client').then(({ authApi }) => {
      authApi.me()
        .then(user => setRole(user.role?.toLowerCase() ?? ''))
        .catch(() => setRole(''));
    });
  }, []);

  const update = (key: keyof ListingForm, value: string) => {
    setForm(old => ({ ...old, [key]: value }));
  };

  const submitListing = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    const quantity = Number(form.quantity);
    const price = Number(form.asking_price);

    if (!form.crop_name.trim() || !Number.isFinite(quantity) ||
        quantity <= 0 || !Number.isFinite(price) || price <= 0) {
      setError('Enter a crop name, a quantity greater than zero, and a valid price.');
      return;
    }
    if (form.pincode && !/^\d{6}$/.test(form.pincode)) {
      setError('Pincode must contain exactly 6 digits.');
      return;
    }

    setSaving(true);
    try {
      await listingsApi.create({
        crop_name: form.crop_name.trim(),
        crop_variety: form.crop_variety.trim() || undefined,
        quantity,
        unit: form.unit,
        asking_price: price,
        price_currency: 'INR',
        negotiability: form.negotiability,
        district: form.district.trim() || undefined,
        state: form.state.trim() || 'Maharashtra',
        village: form.village.trim() || undefined,
        pincode: form.pincode || undefined,
        delivery_preference: form.delivery_preference,
      });

      setForm(initialForm);
      setShowForm(false);
      setPage(1);
      setSuccess('Listing created successfully.');
      await loadListings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Listing creation failed.');
    } finally {
      setSaving(false);
    }
  };

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    setPage(1);
    void loadListings();
  };

  const isFarmer = ['farmer', 'fpo_admin'].includes(role);

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-forest">Marketplace</h1>
          <p className="mt-1 text-sm text-gray-600">
            Discover crops and connect directly with farmers.
          </p>
        </div>
        {isFarmer && (
          <Button onClick={() => {
            setShowForm(value => !value);
            setError('');
            setSuccess('');
          }}>
            {showForm ? <X className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
            {showForm ? 'Cancel' : 'Sell Crops / Create Listing'}
          </Button>
        )}
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div role="status" className="rounded-lg border border-green-300 bg-green-50 p-3 text-sm text-green-800">
          {success}
        </div>
      )}

      {showForm && isFarmer && (
        <Card className="!p-5">
          <h2 className="mb-4 text-xl font-semibold">Create crop listing</h2>
          <form onSubmit={submitListing} className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block text-sm font-medium">
              Crop name *
              <input
                required list="crop-catalogue" value={form.crop_name}
                onChange={e => update('crop_name', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
                placeholder="e.g. Wheat"
              />
              <datalist id="crop-catalogue">
                {catalogue.map(crop => (
                  <option key={crop.id} value={crop.name_en} />
                ))}
              </datalist>
            </label>

            <label className="block text-sm font-medium">
              Variety
              <input value={form.crop_variety}
                onChange={e => update('crop_variety', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
                placeholder="Optional variety"
              />
            </label>

            <label className="block text-sm font-medium">
              Quantity *
              <input required type="number" min="0.01" step="0.01"
                value={form.quantity} onChange={e => update('quantity', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
              />
            </label>

            <label className="block text-sm font-medium">
              Unit *
              <select value={form.unit} onChange={e => update('unit', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2">
                {['kg', 'quintal', 'ton', 'piece', 'dozen', 'bag'].map(unit =>
                  <option key={unit} value={unit}>{unit}</option>
                )}
              </select>
            </label>

            <label className="block text-sm font-medium">
              Asking price (₹ per unit) *
              <input required type="number" min="0.01" step="0.01"
                value={form.asking_price}
                onChange={e => update('asking_price', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
              />
            </label>

            <label className="block text-sm font-medium">
              Price type
              <select value={form.negotiability}
                onChange={e => update('negotiability', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2">
                <option value="negotiable">Negotiable</option>
                <option value="fixed">Fixed</option>
                <option value="auction">Auction</option>
              </select>
            </label>

            <label className="block text-sm font-medium">
              Village
              <input value={form.village} onChange={e => update('village', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2" />
            </label>

            <label className="block text-sm font-medium">
              District
              <input value={form.district} onChange={e => update('district', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2" />
            </label>

            <label className="block text-sm font-medium">
              State
              <input value={form.state} onChange={e => update('state', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2" />
            </label>

            <label className="block text-sm font-medium">
              Pincode
              <input inputMode="numeric" maxLength={6} value={form.pincode}
                onChange={e => update('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
                placeholder="6 digits"
              />
            </label>

            <label className="block text-sm font-medium">
              Delivery preference
              <select value={form.delivery_preference}
                onChange={e => update('delivery_preference', e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2">
                <option value="both">Pickup or delivery</option>
                <option value="pickup">Buyer pickup</option>
                <option value="delivery">Seller delivery</option>
              </select>
            </label>

            <div className="flex items-end">
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving listing...' : 'Publish listing'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <form onSubmit={handleSearch} className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          <input value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search crops, varieties..."
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4"
          />
        </div>
        <Button type="button" variant="outline"
          onClick={() => setShowFilters(value => !value)}>
          <Filter className="mr-1 h-4 w-4" /> Filters
        </Button>
        <Button type="submit" variant="outline">Search</Button>
      </form>

      {showFilters && (
        <Card className="mb-4 !p-4">
          <Input label="District" value={district}
            onChange={e => setDistrict(e.target.value)}
            placeholder="e.g. Jalgaon"
          />
        </Card>
      )}

      <p className="mb-4 text-sm text-gray-500">
        {total} listing{total !== 1 ? 's' : ''} found
      </p>

      {loading ? (
        <div className="py-12 text-center text-gray-500">Loading listings...</div>
      ) : listings.length === 0 ? (
        <Card className="py-12 text-center">
          <Package className="mx-auto mb-3 h-12 w-12 text-gray-300" />
          <p className="text-gray-600">No active listings found. Farmers can publish the first listing.</p>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {listings.map(listing => (
            <Link key={listing.id} to={`/marketplace/${listing.id}`}>
              <Card className="h-full cursor-pointer transition hover:shadow-md">
                <div className="mb-2 flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">{listing.crop_name}</h3>
                    {listing.crop_variety && <span className="text-sm text-gray-500">{listing.crop_variety}</span>}
                  </div>
                  <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-700">
                    {listing.negotiability}
                  </span>
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <IndianRupee className="h-4 w-4" />
                    <strong className="text-base text-forest">
                      {Number(listing.asking_price).toLocaleString('en-IN')}
                    </strong> / {listing.unit}
                  </div>
                  <div className="flex items-center gap-1">
                    <Package className="h-4 w-4" />
                    {Number(listing.quantity).toLocaleString('en-IN')} {listing.unit}
                  </div>
                  {listing.district && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {listing.district}, {listing.state}
                    </div>
                  )}
                </div>
                <div className="mt-3 flex justify-between border-t pt-3 text-xs text-gray-400">
                  <span>{listing.seller_name || 'Farmer'}</span>
                  <span>{new Date(listing.created_at).toLocaleDateString()}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {total > 20 && (
        <div className="mt-6 flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1}
            onClick={() => setPage(current => current - 1)}>Previous</Button>
          <span className="px-4 py-2 text-sm">Page {page}</span>
          <Button variant="outline" size="sm" disabled={listings.length < 20}
            onClick={() => setPage(current => current + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
