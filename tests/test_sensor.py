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

    # 1. Test percent < 0 (should treat as 0)
    coordinator.data = {"tank_size": 100, "tank_level": -5}
    assert sensor._calculate_gallons_remaining() == 0.0

    # 2. Test percent > 100 (should treat as 100)
    coordinator.data = {"tank_size": 100, "tank_level": 105}
    assert sensor._calculate_gallons_remaining() == 100.0

    # 3. Test normal bounds check for missing percent defaults to 0
    coordinator.data = {"tank_size": 100, "tank_level": None}
    assert sensor._calculate_gallons_remaining() == 0.0

    # 4. Test normal bounds check for missing tank_size defaults to 500 (from const DEFAULT_TANK_SIZE)
    # The default is 500, but we test the general logic that it falls back to something valid
    coordinator.data = {"tank_size": None, "tank_level": 50}
    result = sensor._calculate_gallons_remaining()
    assert result == 250.0  # 50% of 500 (DEFAULT_TANK_SIZE)

    # 5. Test normal operation
    coordinator.data = {"tank_size": 120, "tank_level": 50}
    assert sensor._calculate_gallons_remaining() == 60.0

    # 6. Test tank_size <= 0
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
