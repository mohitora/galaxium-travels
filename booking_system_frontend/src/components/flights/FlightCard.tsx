import type { Flight, SeatClass } from '../../types';
import { SEAT_CLASSES, SEAT_CLASS_LABELS } from '../../types';
import { Card } from '../common';
import { Plane, Clock, Users } from 'lucide-react';
import { formatCurrency, formatDate, formatTime, calculateDuration } from '../../utils/formatters';
import { motion } from 'framer-motion';

interface FlightCardProps {
  flight: Flight;
  onBook: (flight: Flight, seatClass: SeatClass) => void;
}

// Per-class visual accent (bg gradient for button, border colour for row)
const CLASS_STYLES: Record<SeatClass, { row: string; badge: string; btn: string }> = {
  economy: {
    row: 'border-white/10',
    badge: 'bg-white/10 text-star-white',
    btn: 'bg-white/10 hover:bg-white/20 text-star-white',
  },
  flexi: {
    row: 'border-blue-400/20',
    badge: 'bg-blue-500/15 text-blue-300',
    btn: 'bg-blue-500/20 hover:bg-blue-500/35 text-blue-200',
  },
  business: {
    row: 'border-cosmic-purple/30',
    badge: 'bg-cosmic-purple/20 text-cosmic-purple',
    btn: 'bg-cosmic-purple/25 hover:bg-cosmic-purple/40 text-purple-200',
  },
  galaxium: {
    row: 'border-solar-orange/30',
    badge: 'bg-solar-orange/15 text-solar-orange',
    btn: 'bg-solar-orange/20 hover:bg-solar-orange/35 text-orange-200',
  },
};

const seatCount = (flight: Flight, sc: SeatClass): number =>
  flight[`${sc}_seats` as keyof Flight] as number;

const seatPrice = (flight: Flight, sc: SeatClass): number =>
  flight[`${sc}_price` as keyof Flight] as number;

export const FlightCard = ({ flight, onBook }: FlightCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="h-full flex flex-col">
        {/* Route Header */}
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cosmic-gradient">
              <Plane className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-star-white">
                {flight.origin} → {flight.destination}
              </h3>
              <p className="text-sm text-star-white/60">
                Flight #{flight.flight_id}
              </p>
            </div>
          </div>
        </div>

        {/* Departure / Arrival / Duration */}
        <div className="space-y-3 mb-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-star-white/60 mb-1">Departure</p>
              <p className="text-sm font-medium text-star-white">
                {formatDate(flight.departure_time, 'MMM dd, yyyy')}
              </p>
              <p className="text-lg font-bold text-cosmic-purple">
                {formatTime(flight.departure_time)}
              </p>
            </div>
            <div>
              <p className="text-xs text-star-white/60 mb-1">Arrival</p>
              <p className="text-sm font-medium text-star-white">
                {formatDate(flight.arrival_time, 'MMM dd, yyyy')}
              </p>
              <p className="text-lg font-bold text-cosmic-purple">
                {formatTime(flight.arrival_time)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-star-white/70">
            <Clock size={16} />
            <span className="text-sm">
              Duration: {calculateDuration(flight.departure_time, flight.arrival_time)}
            </span>
          </div>
        </div>

        {/* Seat Class Selector */}
        <div className="flex-1 space-y-2">
          {SEAT_CLASSES.map((sc) => {
            const seats = seatCount(flight, sc);
            const price = seatPrice(flight, sc);
            const soldOut = seats === 0;
            const lowSeats = !soldOut && seats <= 2;
            const styles = CLASS_STYLES[sc];

            return (
              <div
                key={sc}
                className={`flex items-center justify-between rounded-lg border px-3 py-2 ${styles.row}`}
              >
                {/* Class label + seats */}
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${styles.badge}`}>
                    {SEAT_CLASS_LABELS[sc]}
                  </span>
                  <span className={`text-xs flex items-center gap-1 ${
                    soldOut ? 'text-red-400' : lowSeats ? 'text-solar-orange' : 'text-star-white/50'
                  }`}>
                    <Users size={12} />
                    {soldOut ? 'Sold out' : `${seats} left`}
                  </span>
                </div>

                {/* Price + Book button */}
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm font-bold text-star-white">
                    {formatCurrency(price)}
                  </span>
                  <button
                    onClick={() => onBook(flight, sc)}
                    disabled={soldOut}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${styles.btn}`}
                  >
                    {soldOut ? 'Full' : 'Book'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </motion.div>
  );
};

// Made with Bob
