// ─── Enums ────────────────────────────────────────────────────────────────────

export enum UserRole {
  FARMER = 'farmer',
  BUYER = 'buyer',
  ADMIN = 'admin',
}

export enum ListingStatus {
  ACTIVE = 'active',
  SOLD = 'sold',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled',
}

export enum OfferStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
  COUNTERED = 'countered',
  WITHDRAWN = 'withdrawn',
}

export enum QuantityUnit {
  KG = 'kg',
  QUINTAL = 'quintal',
  TON = 'ton',
}

export enum QualityGrade {
  A = 'A',
  B = 'B',
  C = 'C',
}

// ─── Core Interfaces ─────────────────────────────────────────────────────────

export interface User {
  id: string;
  full_name: string;
  phone: string;
  role: UserRole;
  district: string;
  taluka: string;
  village: string;
  is_verified: boolean;
  preferred_language: string;
  created_at: string;
  updated_at: string;
}

export interface Commodity {
  id: string;
  name_en: string;
  name_mr: string;
  category: string;
  icon_url?: string;
}

export interface Listing {
  id: string;
  farmer_id: string;
  farmer: User;
  commodity_id: string;
  commodity: Commodity;
  quantity: number;
  quantity_unit: QuantityUnit;
  quality_grade: QualityGrade;
  price_per_unit: number;
  description?: string;
  images: string[];
  location_district: string;
  location_taluka: string;
  status: ListingStatus;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface Offer {
  id: string;
  listing_id: string;
  listing: Listing;
  buyer_id: string;
  buyer: User;
  offered_price: number;
  offered_quantity: number;
  quantity_unit: QuantityUnit;
  message?: string;
  status: OfferStatus;
  counter_price?: number;
  created_at: string;
  updated_at: string;
}

export interface MarketPrice {
  id: string;
  commodity_id: string;
  commodity: Commodity;
  market_name: string;
  district: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  date: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'offer' | 'listing' | 'price_alert' | 'system';
  is_read: boolean;
  data?: Record<string, unknown>;
  created_at: string;
}

// ─── API Types ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
  errors?: Record<string, string[]>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  phone: string;
  otp: string;
}

export interface RegisterRequest {
  full_name: string;
  phone: string;
  role: UserRole;
  district: string;
  taluka: string;
  village: string;
  preferred_language: string;
}

export interface CreateListingRequest {
  commodity_id: string;
  quantity: number;
  quantity_unit: QuantityUnit;
  quality_grade: QualityGrade;
  price_per_unit: number;
  description?: string;
  images?: File[];
}

export interface CreateOfferRequest {
  listing_id: string;
  offered_price: number;
  offered_quantity: number;
  quantity_unit: QuantityUnit;
  message?: string;
}

export interface ListingFilters {
  commodity_id?: string;
  district?: string;
  taluka?: string;
  quality_grade?: QualityGrade;
  min_price?: number;
  max_price?: number;
  status?: ListingStatus;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
