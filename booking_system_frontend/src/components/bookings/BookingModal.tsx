import { useState } from 'react';
import type { Flight, SeatClass } from '../../types';
import { SEAT_CLASS_LABELS, SEAT_CLASS_COLORS } from '../../types';
import { Modal, Button } from '../common';
import { Plane, Calendar, Clock, DollarSign, Star } from 'lucide-react';
import { formatCurrency, formatDate, calculateDuration } from '../../utils/formatters';
import { bookFlight, isErrorResponse } from '../../services/api';
import { useUser } from '../../hooks/useUser';
import toast from 'react-hot-toast';

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  flight: Flight | null;
  seatClass: SeatClass | null;
  onSuccess: () => void;
}

export const BookingModal = ({ isOpen, onClose, flight, seatClass, onSuccess }: BookingModalProps) => {
  const { user } = useUser();
  const [isLoading, setIsLoading] = useState(false);

  if (!flight || !seatClass) return null;

  const classPrice = flight[`${seatClass}_price` as keyof Flight] as number;
  const classLabel = SEAT_CLASS_LABELS[seatClass];
  const classColorClass = SEAT_CLASS_COLORS[seatClass];

  const handleConfirmBooking = async () => {
    if (!user) {
      toast.error('Please sign in to book a flight');
      return;
    }

    setIsLoading(true);

    try {
      const result = await bookFlight({
        user_id: user.user_id,
        name: user.name,
        flight_id: flight.flight_id,
        seat_class: seatClass,
      });

      if (isErrorResponse(result)) {
        toast.error(result.details || result.error);
        return;
      }

      toast.success(`${classLabel} seat booked successfully!`);
      onSuccess();
      onClose();
    } catch (error: any) {
      toast.error(error.details || error.error || 'Failed to book flight');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm Your Booking"
      size="md"
    >
      <div className="space-y-6">
        {/* Flight Summary */}
        <div className="glass-card p-4 bg-white/5">
          <div className="flex items-center gap-3 mb-4">
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

          <div className="space-y-3">
            {/* Seat Class */}
            <div className="flex items-start gap-3">
              <Star className="mt-1 shrink-0" size={20} style={{ color: 'currentColor' }} />
              <div>
                <p className="text-xs text-star-white/60">Seat Class</p>
                <span className={`text-sm font-bold ${classColorClass.split(' ')[0]}`}>
                  {classLabel}
                </span>
              </div>
            </div>

            {/* Departure */}
            <div className="flex items-start gap-3">
              <Calendar className="text-cosmic-purple mt-1 shrink-0" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Departure</p>
                <p className="text-star-white font-medium">
                  {formatDate(flight.departure_time)}
                </p>
              </div>
            </div>

            {/* Arrival */}
            <div className="flex items-start gap-3">
              <Calendar className="text-cosmic-purple mt-1 shrink-0" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Arrival</p>
                <p className="text-star-white font-medium">
                  {formatDate(flight.arrival_time)}
                </p>
              </div>
            </div>

            {/* Duration */}
            <div className="flex items-start gap-3">
              <Clock className="text-cosmic-purple mt-1 shrink-0" size={20} />
              <div>
                <p className="text-xs text-star-white/60">Duration</p>
                <p className="text-star-white font-medium">
                  {calculateDuration(flight.departure_time, flight.arrival_time)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Passenger Info */}
        {user && (
          <div className="glass-card p-4 bg-white/5">
            <h4 className="text-sm font-semibold text-star-white mb-2">
              Passenger Information
            </h4>
            <p className="text-star-white">{user.name}</p>
            <p className="text-star-white/60 text-sm">{user.email}</p>
          </div>
        )}

        {/* Price — uses per-class price */}
        <div className="flex items-center justify-between p-4 glass-card bg-cosmic-gradient">
          <div className="flex items-center gap-2">
            <DollarSign className="text-white" size={24} />
            <span className="text-white font-semibold">Total Price</span>
          </div>
          <span className="text-2xl font-bold text-white">
            {formatCurrency(classPrice)}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmBooking}
            isLoading={isLoading}
            className="flex-1"
          >
            Confirm Booking
          </Button>
        </div>

        <p className="text-xs text-star-white/60 text-center">
          By confirming, you agree to our terms and conditions
        </p>
      </div>
    </Modal>
  );
};

// Made with Bob
