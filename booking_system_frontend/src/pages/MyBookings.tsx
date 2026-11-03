import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Booking, Flight, RefundPreview } from '../types';
import { SEAT_CLASS_REFUND_POLICY } from '../types';
import { LoadingSpinner, Modal, Button } from '../components/common';
import { BookingCard } from '../components/bookings/BookingCard';
import {
  getUserBookings,
  getFlights,
  cancelBooking,
  getRefundPreview,
  isErrorResponse,
} from '../services/api';
import { formatCurrency } from '../utils/formatters';
import { useUser } from '../hooks/useUser';
import { AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';

export const MyBookings = () => {
  const { user } = useUser();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [bookingToCancel, setBookingToCancel] = useState<number | null>(null);
  const [refundPreview, setRefundPreview] = useState<RefundPreview | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewFailed, setPreviewFailed] = useState(false);
  const previewRequestId = useRef(0);

  useEffect(() => {
    if (!user) {
      navigate('/flights');
      return;
    }
    loadData();
  }, [user, navigate]);

  const loadData = async () => {
    if (!user) return;

    setIsLoading(true);
    try {
      const [bookingsData, flightsData] = await Promise.all([
        getUserBookings(user.user_id),
        getFlights(),
      ]);
      setBookings(bookingsData);
      setFlights(flightsData);
    } catch (error: any) {
      toast.error('Failed to load bookings');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  /** Close the cancel modal and discard any in-flight refund preview. */
  const handleCloseCancelModal = () => {
    previewRequestId.current += 1;
    setShowCancelModal(false);
    setRefundPreview(null);
    setIsPreviewLoading(false);
    setPreviewFailed(false);
  };

  /** Open the cancel modal and fetch the refund preview for the booking. */
  const handleCancelClick = async (bookingId: number) => {
    const requestId = ++previewRequestId.current;
    setBookingToCancel(bookingId);
    setRefundPreview(null);
    setPreviewFailed(false);
    setIsPreviewLoading(true);
    setShowCancelModal(true);

    try {
      const preview = await getRefundPreview(bookingId);
      if (requestId !== previewRequestId.current) return;

      if (isErrorResponse(preview)) {
        setPreviewFailed(true);
        toast.error(preview.details || preview.error);
        return;
      }
      setRefundPreview(preview);
    } catch {
      if (requestId !== previewRequestId.current) return;
      setPreviewFailed(true);
      toast.error('Failed to load refund preview');
    } finally {
      if (requestId === previewRequestId.current) {
        setIsPreviewLoading(false);
      }
    }
  };

  const handleConfirmCancel = async () => {
    if (!bookingToCancel) return;

    setCancellingId(bookingToCancel);
    handleCloseCancelModal();

    try {
      const result = await cancelBooking(bookingToCancel);

      if (isErrorResponse(result)) {
        toast.error(result.details || result.error);
        return;
      }

      toast.success(
        result.refund_amount && result.refund_amount > 0
          ? `Booking cancelled. ${formatCurrency(result.refund_amount)} refunded.`
          : 'Booking cancelled. No refund applied.'
      );
      loadData(); // Reload bookings
    } catch (error: any) {
      toast.error(error.details || error.error || 'Failed to cancel booking');
    } finally {
      setCancellingId(null);
      setBookingToCancel(null);
    }
  };

  const getFlightForBooking = (booking: Booking): Flight | undefined => {
    return flights.find((f) => f.flight_id === booking.flight_id);
  };

  const activeBookings = bookings.filter((b) => b.status === 'booked');
  const pastBookings = bookings.filter((b) => b.status !== 'booked');

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl md:text-5xl font-bold text-star-white mb-4">
          My <span className="bg-cosmic-gradient bg-clip-text text-transparent">Bookings</span>
        </h1>
        <p className="text-star-white/70 text-lg">
          Manage your space travel reservations
        </p>
      </motion.div>

      {isLoading ? (
        <LoadingSpinner size="lg" text="Loading your bookings..." />
      ) : bookings.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <AlertCircle className="mx-auto mb-4 text-star-white/50" size={48} />
          <h3 className="text-xl font-semibold text-star-white mb-2">
            No bookings yet
          </h3>
          <p className="text-star-white/70 mb-6">
            Start your space adventure by booking your first flight!
          </p>
          <Button onClick={() => navigate('/flights')}>
            Browse Flights
          </Button>
        </motion.div>
      ) : (
        <div className="space-y-8">
          {/* Active Bookings */}
          {activeBookings.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <h2 className="text-2xl font-bold text-star-white mb-4">
                Active Bookings ({activeBookings.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {activeBookings.map((booking) => (
                  <BookingCard
                    key={booking.booking_id}
                    booking={booking}
                    flight={getFlightForBooking(booking)}
                    onCancel={handleCancelClick}
                    isCancelling={cancellingId === booking.booking_id}
                  />
                ))}
              </div>
            </motion.div>
          )}

          {/* Past Bookings */}
          {pastBookings.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className="text-2xl font-bold text-star-white mb-4">
                Past Bookings ({pastBookings.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {pastBookings.map((booking) => (
                  <BookingCard
                    key={booking.booking_id}
                    booking={booking}
                    flight={getFlightForBooking(booking)}
                    onCancel={handleCancelClick}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={handleCloseCancelModal}
        title="Cancel Booking"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-star-white/70">
            Are you sure you want to cancel this booking? This action cannot be undone.
          </p>
          {isPreviewLoading && (
            <LoadingSpinner size="sm" text="Checking your refund..." />
          )}
          {!isPreviewLoading && previewFailed && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-solar-orange text-sm"
            >
              Could not load the refund amount. You can still cancel.
            </motion.p>
          )}
          {!isPreviewLoading && refundPreview && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-1"
            >
              {refundPreview.refund_amount > 0 ? (
                <p className="text-alien-green font-semibold">
                  You'll get {formatCurrency(refundPreview.refund_amount)} back
                </p>
              ) : (
                <p className="text-solar-orange font-semibold">
                  No refund applies if you cancel now
                </p>
              )}
              <p className="text-star-white/60 text-sm">
                {SEAT_CLASS_REFUND_POLICY[refundPreview.seat_class]}
              </p>
            </motion.div>
          )}
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={handleCloseCancelModal}
              className="flex-1"
            >
              Keep Booking
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmCancel}
              className="flex-1"
            >
              Cancel Booking
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// Made with Bob
