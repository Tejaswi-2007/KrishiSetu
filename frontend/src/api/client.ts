/** Typed API client for Digi-Mandi backend. */

const BASE = '/api/v1';

class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || 'Request failed');
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string; language_pref?: string }) =>
    api.post<{ access_token: string; user: User }>('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; user: User }>('/auth/login', data),
  me: () => api.get<User>('/auth/me'),
  updateProfile: (data: Partial<User>) => api.patch<User>('/auth/me', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
};

// Listings
export const listingsApi = {
  search: (params?: Record<string, string | number>) => {
    const qs = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
    return api.get<PaginatedResponse<Listing>>(`/listings${qs}`);
  },
  get: (id: number) => api.get<Listing>(`/listings/${id}`),
  create: (data: Partial<Listing>) => api.post<Listing>('/listings', data),
  update: (id: number, data: Partial<Listing>) => api.patch<Listing>(`/listings/${id}`, data),
  my: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<PaginatedResponse<Listing>>(`/listings/my${qs}`);
  },
  catalogue: () => api.get<CropCatalogueItem[]>('/listings/catalogue'),
};

// Offers
export const offersApi = {
  create: (data: { listing_id: number; offered_price: number; quantity: number; unit: string; notes?: string }) =>
    api.post<Offer>('/offers', data),
  get: (id: number) => api.get<Offer>(`/offers/${id}`),
  sent: () => api.get<PaginatedResponse<Offer>>('/offers/my/sent'),
  received: (listing_id?: number) => {
    const qs = listing_id ? `?listing_id=${listing_id}` : '';
    return api.get<PaginatedResponse<Offer>>(`/offers/my/received${qs}`);
  },
  action: (id: number, action: 'accept' | 'reject' | 'withdraw', notes?: string) =>
    api.post<Offer>(`/offers/${id}/action?action=${action}`, { action, notes }),
  counter: (id: number, data: { offered_price: number; quantity?: number; notes?: string }) =>
    api.post<Offer>(`/offers/${id}/counter`, data),
  history: (id: number) => api.get<OfferEvent[]>(`/offers/${id}/history`),
};

// Market Prices
export const pricesApi = {
  search: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<PaginatedResponse<MarketPrice>>(`/market-prices${qs}`);
  },
  crops: () => api.get<string[]>('/market-prices/crops'),
  markets: () => api.get<{ market_name: string; district: string }[]>('/market-prices/markets'),
  latest: (crop_name: string) => api.get<MarketPrice[]>(`/market-prices/latest?crop_name=${encodeURIComponent(crop_name)}`),
};

// Calculator
export const calculatorApi = {
  netProceeds: (data: {
    rate_per_unit: number; quantity: number; unit: string;
    transportation_cost?: number; commission_percent?: number;
    loading_unloading_cost?: number; packaging_cost?: number; other_costs?: number;
  }) => api.post<NetProceedsResult>('/calculator/net-proceeds', data),
};

// Deal Rooms
export const dealRoomsApi = {
  list: () => api.get<DealRoom[]>('/deal-rooms'),
  get: (id: number) => api.get<DealRoom>(`/deal-rooms/${id}`),
  create: (data: { title: string; listing_id?: number; offer_id?: number; participant_ids: number[]; video_enabled?: boolean }) =>
    api.post<DealRoom>('/deal-rooms', data),
  messages: (id: number) => api.get<ChatMessage[]>(`/deal-rooms/${id}/messages`),
  sendMessage: (id: number, content: string) => api.post<ChatMessage>(`/deal-rooms/${id}/messages?content=${encodeURIComponent(content)}`),
};

// Notifications
export const notificationsApi = {
  list: (unread_only = false) => api.get<{ items: Notification[]; total: number; unread_count: number }>(`/notifications?unread_only=${unread_only}`),
  markRead: (id: number) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};

// Admin
export const adminApi = {
  dashboard: () => api.get<AdminDashboard>('/admin/dashboard'),
  users: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return api.get<PaginatedResponse<User>>(`/admin/users${qs}`);
  },
};

// Types
export interface User {
  id: number; email: string; phone?: string; full_name: string;
  role: string; is_active: boolean; is_verified: boolean;
  language_pref: string; avatar_url?: string; created_at: string;
}

export interface Listing {
  id: number; seller_id: number; crop_name: string; crop_variety?: string;
  category?: string; grade?: string; quality_description?: string;
  quantity: number; unit: string; asking_price: number; price_currency: string;
  negotiability: string; available_from?: string; harvest_date?: string;
  location?: string; village?: string; taluka?: string; district?: string;
  state?: string; pincode?: string; delivery_preference: string;
  images?: string; status: string; view_count: number; offer_count: number;
  quantity_remaining?: number; created_at: string; updated_at: string;
  seller_name?: string; seller_verified?: boolean;
}

export interface Offer {
  id: number; listing_id: number; buyer_id: number; seller_id: number;
  offered_price: number; currency: string; quantity: number; unit: string;
  delivery_terms?: string; payment_terms?: string; notes?: string;
  status: string; version: number; parent_offer_id?: number;
  created_at: string; buyer_name?: string; seller_name?: string; listing_crop_name?: string;
}

export interface OfferEvent {
  id: number; event_type: string; actor_id: number;
  old_price?: string; new_price?: string; notes?: string; created_at: string;
}

export interface MarketPrice {
  id: number; crop_name: string; variety?: string;
  market_name: string; district?: string;
  min_price?: number; max_price?: number; modal_price?: number;
  price_unit: string; currency: string; reporting_date: string; freshness: string;
}

export interface DealRoom {
  id: number; title: string; description?: string;
  listing_id?: number; offer_id?: number;
  jitsi_room_name?: string; jitsi_domain: string;
  video_enabled: boolean; status: string;
  participants: { user_id: number; role: string; name?: string; is_online: boolean }[];
  created_at: string;
}

export interface ChatMessage {
  id: number; room_id: number; sender_id?: number;
  sender_name?: string; content: string; message_type: string; created_at: string;
}

export interface NetProceedsResult {
  gross_value: number; transportation_cost?: number; loading_unloading_cost?: number;
  packaging_cost?: number; commission_amount?: number; commission_percent?: number;
  other_costs?: number; total_deductions: number; estimated_net_proceeds: number;
  unknown_costs_note: string; currency: string; unit: string; quantity: number; rate_per_unit: number;
}

export interface CropCatalogueItem {
  id: number; name_en: string; name_mr?: string; category?: string; variety?: string; unit_options: string;
}

export interface Notification {
  id: number; type: string; title: string; message?: string;
  link?: string; is_read: boolean; created_at: string;
}

export interface AdminDashboard {
  users: { total: number; farmers: number; buyers: number; active: number };
  listings: { total: number; active: number; sold: number };
  offers: { total: number; pending: number; accepted: number };
  deal_rooms: number; agreements: number; transactions: number;
}

export interface PaginatedResponse<T> {
  items: T[]; total: number; page: number; page_size: number; total_pages?: number;
}

export { ApiError };
