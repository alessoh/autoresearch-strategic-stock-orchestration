"""Trading strategy signal functions used by the harness."""

from .buy_hold import compute_signal as buy_hold_signal
from .mean_reversion import compute_signal as mean_reversion_signal
from .momentum import compute_signal as momentum_signal

__all__ = ["momentum_signal", "mean_reversion_signal", "buy_hold_signal"]
