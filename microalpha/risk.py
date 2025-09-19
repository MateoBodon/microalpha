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


def bootstrap_sharpe_ratio(returns, num_simulations=5000, periods=252):
    """
    Performs a bootstrap analysis on a returns stream to determine the
    statistical significance of its Sharpe ratio.
    """
    if returns.std() == 0 or len(returns) < 3: # Not enough data
        return {
            'sharpe_dist': [0.0],
            'p_value': 1.0,
            'confidence_interval': (0.0, 0.0)
        }
        
    sharpe_dist = []
    
    for _ in range(num_simulations):
        # Create a bootstrap sample by sampling with replacement
        bootstrapped_returns = returns.sample(n=len(returns), replace=True)
        
        # Calculate the Sharpe for this random sample
        sim_sharpe = create_sharpe_ratio(bootstrapped_returns, periods)
        sharpe_dist.append(sim_sharpe)
    
    # --- STATISTICAL SIGNIFICANCE ---
    # The p-value is the probability of observing a Sharpe <= 0
    # by random chance, given our returns distribution.
    p_value = sum(1 for s in sharpe_dist if s <= 0.0) / num_simulations
    
    # Calculate the 95% confidence interval
    confidence_interval = (
        np.percentile(sharpe_dist, 2.5),
        np.percentile(sharpe_dist, 97.5)
    )
    
    return {
        'sharpe_dist': sharpe_dist,
        'p_value': p_value,
        'confidence_interval': confidence_interval
    }
