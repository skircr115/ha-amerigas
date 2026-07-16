# Mock out homeassistant const before importing from custom_components
import homeassistant.const
if not hasattr(homeassistant.const.UnitOfVolumeFlowRate, 'GALLONS_PER_DAY'):
    homeassistant.const.UnitOfVolumeFlowRate.GALLONS_PER_DAY = "gal/d"

from unittest.mock import MagicMock
from custom_components.amerigas.sensor import AmeriGasSensorBase

def test_calculate_gallons_remaining_bounds():
    """Test boundary conditions for _calculate_gallons_remaining."""
    coordinator = MagicMock()
    sensor = AmeriGasSensorBase(coordinator, "test_entry")

    # 1. Test percent exactly 0 (boundary)
    coordinator.data = {"tank_size": 100, "tank_level": 0}
    assert sensor._calculate_gallons_remaining() == 0.0

    # 2. Test percent < 0 (should treat as 0)
    coordinator.data = {"tank_size": 100, "tank_level": -5}
    assert sensor._calculate_gallons_remaining() == 0.0

    # 3. Test percent exactly 100 (boundary)
    coordinator.data = {"tank_size": 100, "tank_level": 100}
    assert sensor._calculate_gallons_remaining() == 100.0

    # 4. Test percent > 100 (should treat as 100)
    coordinator.data = {"tank_size": 100, "tank_level": 105}
    assert sensor._calculate_gallons_remaining() == 100.0

    # 5. Test normal bounds check for missing percent defaults to 0
    coordinator.data = {"tank_size": 100, "tank_level": None}
    assert sensor._calculate_gallons_remaining() == 0.0

    # 6. Test normal bounds check for missing tank_size defaults to 500 (from const DEFAULT_TANK_SIZE)
    # The default is 500, but we test the general logic that it falls back to something valid
    coordinator.data = {"tank_size": None, "tank_level": 50}
    result = sensor._calculate_gallons_remaining()
    assert result == 250.0  # 50% of 500 (DEFAULT_TANK_SIZE)

    # 7. Test normal operation
    coordinator.data = {"tank_size": 120, "tank_level": 50}
    assert sensor._calculate_gallons_remaining() == 60.0

    # 8. Test tank_size <= 0
    # Because of `tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE`
    # if tank_size is explicitly 0, `0 or 500` evaluates to 500!
    # Let's verify what actually happens in the code.
    coordinator.data = {"tank_size": 0, "tank_level": 50}
    # When tank_size=0, `0 or 500` = 500. So it uses DEFAULT_TANK_SIZE!
    assert sensor._calculate_gallons_remaining() == 250.0

    # If tank_size is negative, it won't evaluate to false in `or DEFAULT_TANK_SIZE`
    coordinator.data = {"tank_size": -10, "tank_level": 50}
    # It will use -10, but the code checks `if tank_size <= 0: return None`
    assert sensor._calculate_gallons_remaining() is None

def test_calculate_used_since_delivery():
    """Test priority order and edge cases for _calculate_used_since_delivery."""
    coordinator = MagicMock()
    sensor = AmeriGasSensorBase(coordinator, "test_entry")

    # 1. No data
    coordinator.data = {}
    assert sensor._calculate_used_since_delivery() == (None, "unknown")

    # Mock the priority getters for the rest of the tests
    sensor._get_post_fill_gallons = MagicMock(return_value=None)
    sensor._get_pre_delivery_level = MagicMock(return_value=None)

    # 2. Priority 1: post_fill_gallons (tank monitor)
    coordinator.data = {"tank_size": 100, "tank_level": 40}  # current = 40
    sensor._get_post_fill_gallons.return_value = 85.0
    # used = 85.0 - 40.0 = 45.0
    assert sensor._calculate_used_since_delivery() == (45.0, "tank_monitor")
    sensor._get_post_fill_gallons.return_value = None  # Reset for next tests

    # 3. Priority 2: pre_delivery_level + last_delivery
    coordinator.data = {"tank_size": 100, "tank_level": 40, "last_delivery_gallons": 50}
    sensor._get_pre_delivery_level.return_value = 30.0
    # starting_level = 30 + 50 = 80. used = 80 - 40 = 40.0
    assert sensor._calculate_used_since_delivery() == (40.0, "auto_captured")

    # 3b. Priority 2 with cap at tank_size
    sensor._get_pre_delivery_level.return_value = 60.0
    # starting_level = 60 + 50 = 110. Capped at 100. used = 100 - 40 = 60.0
    assert sensor._calculate_used_since_delivery() == (60.0, "auto_captured")
    sensor._get_pre_delivery_level.return_value = None  # Reset

    # 4. Priority 3: Heuristic based on small delivery (< 50)
    coordinator.data = {"tank_size": 100, "tank_level": 40, "last_delivery_gallons": 30}
    # last_delivery < 50 => estimated_before = 100 * 0.65 = 65
    # starting_level = min(65 + 30, 100) = 95. used = 95 - 40 = 55.0
    assert sensor._calculate_used_since_delivery() == (55.0, "small_delivery_estimate")

    # 5. Priority 3: Heuristic based on large delivery (>= 50)
    coordinator.data = {"tank_size": 100, "tank_level": 40, "last_delivery_gallons": 60}
    # last_delivery >= 50 => estimated_before = 100 * 0.20 = 20
    # starting_level = min(20 + 60, 100) = 80. used = 80 - 40 = 40.0
    assert sensor._calculate_used_since_delivery() == (40.0, "large_delivery_estimate")

    # 5b. Priority 3 with cap
    coordinator.data = {"tank_size": 100, "tank_level": 40, "last_delivery_gallons": 90}
    # starting_level = min(20 + 90, 100) = 100. used = 100 - 40 = 60.0
    assert sensor._calculate_used_since_delivery() == (60.0, "large_delivery_estimate")

    # 6. Fallback: Assumed 80% fill
    coordinator.data = {"tank_size": 100, "tank_level": 40}  # No last_delivery_gallons
    # starting_level = 100 * 0.8 = 80. used = 80 - 40 = 40.0
    assert sensor._calculate_used_since_delivery() == (40.0, "assumed_80_percent")

    # 7. Max 0 bound check
    coordinator.data = {"tank_size": 100, "tank_level": 90}
    # starting_level = 80. used = 80 - 90 = -10 => Max(0, -10) = 0.0
    assert sensor._calculate_used_since_delivery() == (0.0, "assumed_80_percent")
