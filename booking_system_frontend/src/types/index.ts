// API Data Models matching backend schemas

export type SeatClass = 'economy' | 'flexi' | 'business' | 'galaxium';

export const SEAT_CLASSES: SeatClass[] = ['economy', 'flexi', 'business', 'galaxium'];

export const SEAT_CLASS_LABELS: Record<SeatClass, string> = {
  economy: 'Economy',
  flexi: 'Flexi-Economy',
  business: 'Business',
  galaxium: 'Galaxium',
};

// One-line refund policy per class. Static text: keep in sync with
// REFUND_RULES in booking_system_backend/schemas.py (drift risk accepted).
export const SEAT_CLASS_REFUND_POLICY: Record<SeatClass, string> = {
  economy: '80% refund more than 72h before departure',
  flexi: '100% refund more than 24h before departure',
  business: '75% refund any time before departure',
  galaxium: '100% refund any time before departure',
};

// Colour tokens per class — used for badges and row styling
export const SEAT_CLASS_COLORS: Record<SeatClass, string> = {
  economy: 'text-star-white border-white/20',
  flexi: 'text-blue-300 border-blue-400/40',
  business: 'text-cosmic-purple border-cosmic-purple/40',
  galaxium: 'text-solar-orange border-solar-orange/40',
};

export interface Flight {
  flight_id: number;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  price: number;
  // Per-class seat inventories
  economy_seats: number;
  flexi_seats: number;
  business_seats: number;
  galaxium_seats: number;
  // Backend-computed per-class prices (base price × multiplier)
  economy_price: number;
  flexi_price: number;
  business_price: number;
  galaxium_price: number;
}

export interface Booking {
  booking_id: number;
  user_id: number;
  flight_id: number;
  status: 'booked' | 'cancelled' | 'completed';
  booking_time: string;
  seat_class: SeatClass;
  // Set on cancellation; null otherwise
  refund_amount: number | null;
}

// Matches backend RefundPreviewOut. refund_percent is always the class rule,
// so use refund_amount (not refund_percent) to decide whether a refund applies.
export interface RefundPreview {
  booking_id: number;
  seat_class: SeatClass;
  class_price: number;
  refund_amount: number;
  refund_percent: number;
  departure_time: string;
}

export interface User {
  user_id: number;
  name: string;
  email: string;
}

// Request/Response types
export interface BookingRequest {
  user_id: number;
  name: string;
  flight_id: number;
  seat_class: SeatClass;
}

export interface UserRegistration {
  name: string;
  email: string;
}

export interface ErrorResponse {
  success: false;
  error: string;
  error_code: string;
  details?: string;
}

// Extended types for UI
export interface BookingWithFlight extends Booking {
  flight?: Flight;
}

export interface FlightFilters {
  origin?: string;
  destination?: string;
  minPrice?: number;
  maxPrice?: number;
  searchTerm?: string;
}

// User context type
export interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
}

// Made with Bob
