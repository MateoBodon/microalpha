# microalpha/risk.py
import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
    """
    Calculates the annualized Sharpe ratio of a returns stream.
    `returns` is a pandas Series.
    `periods` is the number of periods per year (252 for daily).
    """
    if returns.std() == 0:
        return 0.0
    return np.sqrt(periods) * (returns.mean() / returns.std())

def create_drawdowns(equity_curve):
    """
    Calculates the maximum drawdown and the drawdown series.
    `equity_curve` is a pandas Series representing portfolio value over time.
    """
    # Calculate the running maximum
    high_water_mark = equity_curve.cummax()
    # Calculate the drawdown series
    drawdown = high_water_mark - equity_curve
    drawdown_percentage = drawdown / high_water_mark
    max_drawdown = drawdown_percentage.max()
    return drawdown_percentage, max_drawdown