import pytest
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import REFUND_RULES, calculate_refund, parse_departure_time

NOW = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
BASE_PRICE = 1000


def _departure(delta: timedelta) -> str:
    """Return the departure string for a flight leaving `delta` after NOW."""
    return (NOW + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


class TestParseDepartureTime:
    """Test schemas.parse_departure_time."""

    def test_z_suffix_parsed_as_utc(self):
        """Test a Z suffix gives an aware UTC datetime."""
        result = parse_departure_time("2099-01-01T09:00:00Z")
        assert result == datetime(2099, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        assert result.utcoffset() == timedelta(0)

    def test_naive_string_assumed_utc(self):
        """Test a string without an offset is treated as UTC."""
        result = parse_departure_time("2099-01-01T09:00:00")
        assert result == datetime(2099, 1, 1, 9, 0, 0, tzinfo=timezone.utc)

    def test_offset_converted_to_utc(self):
        """Test an explicit offset is converted to UTC."""
        result = parse_departure_time("2099-01-01T09:00:00+02:00")
        assert result == datetime(2099, 1, 1, 7, 0, 0, tzinfo=timezone.utc)
        assert result.utcoffset() == timedelta(0)


class TestCalculateRefund:
    """Test schemas.calculate_refund with a fixed aware now."""

    def test_economy_just_over_72h_refunds_80_percent(self):
        """Test Economy one second over 72h refunds 80%."""
        dep = _departure(timedelta(hours=72, seconds=1))
        assert calculate_refund("economy", BASE_PRICE, dep, NOW) == 800

    def test_economy_exactly_72h_refunds_zero(self):
        """Test Economy at exactly 72h refunds 0."""
        dep = _departure(timedelta(hours=72))
        assert calculate_refund("economy", BASE_PRICE, dep, NOW) == 0

    def test_economy_inside_72h_refunds_zero(self):
        """Test Economy one second inside 72h refunds 0."""
        dep = _departure(timedelta(hours=72) - timedelta(seconds=1))
        assert calculate_refund("economy", BASE_PRICE, dep, NOW) == 0

    def test_flexi_just_over_24h_refunds_100_percent(self):
        """Test Flexi one second over 24h refunds 100% of the Flexi price."""
        dep = _departure(timedelta(hours=24, seconds=1))
        assert calculate_refund("flexi", BASE_PRICE, dep, NOW) == 1500

    def test_flexi_exactly_24h_refunds_zero(self):
        """Test Flexi at exactly 24h refunds 0."""
        dep = _departure(timedelta(hours=24))
        assert calculate_refund("flexi", BASE_PRICE, dep, NOW) == 0

    def test_flexi_inside_24h_refunds_zero(self):
        """Test Flexi one second inside 24h refunds 0."""
        dep = _departure(timedelta(hours=24) - timedelta(seconds=1))
        assert calculate_refund("flexi", BASE_PRICE, dep, NOW) == 0

    @pytest.mark.parametrize("delta", [
        timedelta(days=30),
        timedelta(hours=24),
        timedelta(minutes=1),
        timedelta(seconds=1),
    ])
    def test_business_refunds_75_percent_at_any_notice(self, delta):
        """Test Business refunds 75% at any time before departure."""
        assert calculate_refund("business", BASE_PRICE, _departure(delta), NOW) == 2250

    @pytest.mark.parametrize("delta", [
        timedelta(days=30),
        timedelta(hours=24),
        timedelta(minutes=1),
        timedelta(seconds=1),
    ])
    def test_galaxium_refunds_100_percent_at_any_notice(self, delta):
        """Test Galaxium refunds 100% at any time before departure."""
        assert calculate_refund("galaxium", BASE_PRICE, _departure(delta), NOW) == 6000

    @pytest.mark.parametrize("seat_class", list(REFUND_RULES))
    @pytest.mark.parametrize("delta", [
        timedelta(0),
        timedelta(seconds=-1),
        timedelta(days=-10),
    ])
    def test_at_or_after_departure_refunds_zero(self, seat_class, delta):
        """Test every class refunds 0 at or after departure."""
        assert calculate_refund(seat_class, BASE_PRICE, _departure(delta), NOW) == 0

    def test_z_suffix_departure_is_used_as_utc(self):
        """Test a Z-suffixed departure string is compared as UTC."""
        assert calculate_refund("galaxium", BASE_PRICE, "2030-01-01T12:00:01Z", NOW) == 6000
        assert calculate_refund("galaxium", BASE_PRICE, "2030-01-01T11:59:59Z", NOW) == 0

    def test_refund_is_rounded_to_integer(self):
        """Test the refund is a rounded integer (333 * 80% = 266.4 -> 266; 101 * 3 * 75% = 227.25 -> 227)."""
        dep = _departure(timedelta(days=30))
        assert calculate_refund("economy", 333, dep, NOW) == 266
        assert calculate_refund("business", 101, dep, NOW) == 227

    def test_naive_now_raises_type_error(self):
        """Test a naive now is rejected."""
        with pytest.raises(TypeError):
            calculate_refund("economy", BASE_PRICE, _departure(timedelta(days=30)), datetime(2030, 1, 1))

    def test_unknown_seat_class_raises_key_error(self):
        """Test an unknown seat class raises KeyError."""
        with pytest.raises(KeyError):
            calculate_refund("first", BASE_PRICE, _departure(timedelta(days=30)), NOW)
