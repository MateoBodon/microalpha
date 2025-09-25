# microalpha/slippage.py


class SlippageModel:
    """
    Base class for slippage models.
    """

    def calculate_slippage(self, quantity: int, price: float) -> float:
        raise NotImplementedError


class VolumeSlippageModel(SlippageModel):
    """
    A simple slippage model that simulates price impact based on
    the trade quantity. The idea is that larger orders move the price
    against you.

    Slippage is calculated as: price_impact * (quantity^2)
    """

    def __init__(self, price_impact: float = 0.0001):
        # A small constant to model the market impact of our trades.
        self.price_impact = price_impact

    def calculate_slippage(self, quantity: int, price: float) -> float:
        """
        Calculates the per-share slippage for a given quantity.
        Returns the amount of price impact per share.
        """
        # The slippage impact grows with the square of the quantity
        return self.price_impact * (quantity**2)
