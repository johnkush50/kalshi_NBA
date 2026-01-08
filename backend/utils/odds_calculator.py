"""
Odds calculation utilities for the Data Aggregation Layer.

All calculations use Decimal to avoid floating point errors.
Handles conversion between American odds, implied probabilities,
and Kalshi prices (in cents).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Constants
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")
DECIMAL_HUNDRED = Decimal("100")


def american_to_implied_probability(american_odds: int) -> Decimal:
    """
    Convert American odds to implied probability.
    
    Args:
        american_odds: American odds (e.g., -150, +200)
        
    Returns:
        Implied probability as Decimal (0-1)
        
    Examples:
        american_to_implied_probability(-150) -> Decimal("0.6")
        american_to_implied_probability(+200) -> Decimal("0.333...")
    """
    if american_odds == 0:
        return Decimal("0.5")
    
    odds = Decimal(str(american_odds))
    
    if american_odds < 0:
        # Favorite: probability = |odds| / (|odds| + 100)
        abs_odds = abs(odds)
        return abs_odds / (abs_odds + DECIMAL_HUNDRED)
    else:
        # Underdog: probability = 100 / (odds + 100)
        return DECIMAL_HUNDRED / (odds + DECIMAL_HUNDRED)


def implied_probability_to_american(prob: Decimal) -> int:
    """
    Convert implied probability to American odds.
    
    Args:
        prob: Implied probability as Decimal (0-1)
        
    Returns:
        American odds as integer (e.g., -150, +200)
        
    Examples:
        implied_probability_to_american(Decimal("0.6")) -> -150
        implied_probability_to_american(Decimal("0.333")) -> +200
    """
    if prob <= DECIMAL_ZERO or prob >= DECIMAL_ONE:
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")
    
    if prob == Decimal("0.5"):
        return 100  # Even odds
    
    if prob > Decimal("0.5"):
        # Favorite: odds = -100 * prob / (1 - prob)
        american = -DECIMAL_HUNDRED * prob / (DECIMAL_ONE - prob)
    else:
        # Underdog: odds = 100 * (1 - prob) / prob
        american = DECIMAL_HUNDRED * (DECIMAL_ONE - prob) / prob
    
    return int(american.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def kalshi_price_to_probability(price_cents: Decimal) -> Decimal:
    """
    Convert Kalshi price (in cents) to implied probability.
    
    Args:
        price_cents: Price in cents (0-100)
        
    Returns:
        Implied probability as Decimal (0-1)
        
    Example:
        kalshi_price_to_probability(Decimal("45")) -> Decimal("0.45")
    """
    if price_cents < DECIMAL_ZERO or price_cents > DECIMAL_HUNDRED:
        logger.warning(f"Kalshi price out of range: {price_cents}")
        price_cents = max(DECIMAL_ZERO, min(DECIMAL_HUNDRED, price_cents))
    
    return price_cents / DECIMAL_HUNDRED


def probability_to_kalshi_price(prob: Decimal) -> Decimal:
    """
    Convert probability to Kalshi price (in cents).
    
    Args:
        prob: Probability as Decimal (0-1)
        
    Returns:
        Price in cents as Decimal (0-100)
        
    Example:
        probability_to_kalshi_price(Decimal("0.45")) -> Decimal("45")
    """
    if prob < DECIMAL_ZERO or prob > DECIMAL_ONE:
        logger.warning(f"Probability out of range: {prob}")
        prob = max(DECIMAL_ZERO, min(DECIMAL_ONE, prob))
    
    return (prob * DECIMAL_HUNDRED).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_consensus_probability(
    odds_list: List[int],
    method: str = "median"
) -> Optional[Decimal]:
    """
    Calculate consensus implied probability from multiple American odds.
    
    Args:
        odds_list: List of American odds from different sportsbooks
        method: Aggregation method - "mean", "median", or "weighted"
        
    Returns:
        Consensus probability as Decimal (0-1), or None if list is empty
        
    Example:
        calculate_consensus_probability([-150, -140, -160], "median") -> ~Decimal("0.58")
    """
    if not odds_list:
        return None
    
    # Convert all odds to probabilities
    probabilities = [american_to_implied_probability(odds) for odds in odds_list]
    
    if method == "mean":
        total = sum(probabilities)
        return total / Decimal(str(len(probabilities)))
    
    elif method == "median":
        sorted_probs = sorted(probabilities)
        n = len(sorted_probs)
        mid = n // 2
        
        if n % 2 == 0:
            return (sorted_probs[mid - 1] + sorted_probs[mid]) / Decimal("2")
        else:
            return sorted_probs[mid]
    
    elif method == "weighted":
        # Weight by distance from 50% (sharper lines get more weight)
        weights = []
        for prob in probabilities:
            distance = abs(prob - Decimal("0.5"))
            weight = Decimal("1") + distance  # 1.0 to 1.5 weight
            weights.append(weight)
        
        total_weight = sum(weights)
        weighted_sum = sum(p * w for p, w in zip(probabilities, weights))
        return weighted_sum / total_weight
    
    else:
        logger.warning(f"Unknown consensus method: {method}, using median")
        return calculate_consensus_probability(odds_list, "median")


def calculate_ev(
    kalshi_price: Decimal,
    true_probability: Decimal,
    side: str = "yes"
) -> Decimal:
    """
    Calculate expected value of a trade.
    
    Args:
        kalshi_price: Kalshi price in cents (0-100)
        true_probability: Estimated true probability (0-1)
        side: "yes" or "no"
        
    Returns:
        Expected value as Decimal (can be negative)
        Positive EV means profitable bet in the long run.
        
    Formula for YES side:
        EV = (payout * true_prob) - cost
        EV = ((100 - price) * true_prob) - price * (1 - true_prob)
        Simplified: EV = true_prob * 100 - price
        
    Example:
        If Kalshi price is 45¢ and true probability is 55%:
        EV = 0.55 * 100 - 45 = 55 - 45 = +10¢ (positive EV)
    """
    if kalshi_price < DECIMAL_ZERO or kalshi_price > DECIMAL_HUNDRED:
        raise ValueError(f"Kalshi price must be 0-100, got {kalshi_price}")
    
    if true_probability < DECIMAL_ZERO or true_probability > DECIMAL_ONE:
        raise ValueError(f"Probability must be 0-1, got {true_probability}")
    
    if side.lower() == "yes":
        # Buying YES: profit if event happens
        # Cost = price, Payout if win = 100 - price, Prob of win = true_prob
        ev = (true_probability * DECIMAL_HUNDRED) - kalshi_price
    elif side.lower() == "no":
        # Buying NO: profit if event doesn't happen
        # Cost = 100 - price, Payout if win = price, Prob of win = 1 - true_prob
        no_probability = DECIMAL_ONE - true_probability
        ev = (no_probability * DECIMAL_HUNDRED) - (DECIMAL_HUNDRED - kalshi_price)
    else:
        raise ValueError(f"Side must be 'yes' or 'no', got {side}")
    
    return ev.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_kelly_fraction(
    kalshi_price: Decimal,
    true_probability: Decimal,
    side: str = "yes",
    fractional_kelly: Decimal = Decimal("0.25")
) -> Decimal:
    """
    Calculate Kelly criterion bet sizing fraction.
    
    Args:
        kalshi_price: Kalshi price in cents (0-100)
        true_probability: Estimated true probability (0-1)
        side: "yes" or "no"
        fractional_kelly: Fraction of full Kelly to use (default 0.25 = quarter Kelly)
        
    Returns:
        Fraction of bankroll to bet as Decimal (0-1)
        Returns 0 if EV is negative.
        
    Formula:
        Kelly % = (p * b - q) / b
        where p = win probability, q = loss probability, b = odds received
        
    Example:
        If price is 40¢, true prob is 50%, buying YES:
        - Win probability = 50%
        - Payout on win = 60¢ (100 - 40)
        - b = 60/40 = 1.5
        - Kelly = (0.5 * 1.5 - 0.5) / 1.5 = 0.25 / 1.5 = 0.167
        - Quarter Kelly = 0.167 * 0.25 = 0.042 (4.2% of bankroll)
    """
    if kalshi_price <= DECIMAL_ZERO or kalshi_price >= DECIMAL_HUNDRED:
        return DECIMAL_ZERO
    
    if true_probability <= DECIMAL_ZERO or true_probability >= DECIMAL_ONE:
        return DECIMAL_ZERO
    
    if side.lower() == "yes":
        p = true_probability  # Probability of winning
        cost = kalshi_price
        payout = DECIMAL_HUNDRED - kalshi_price
    elif side.lower() == "no":
        p = DECIMAL_ONE - true_probability  # Probability of winning (event doesn't happen)
        cost = DECIMAL_HUNDRED - kalshi_price
        payout = kalshi_price
    else:
        raise ValueError(f"Side must be 'yes' or 'no', got {side}")
    
    q = DECIMAL_ONE - p  # Probability of losing
    
    if payout <= DECIMAL_ZERO:
        return DECIMAL_ZERO
    
    b = payout / cost  # Odds received (payout / cost)
    
    # Kelly formula: f = (p * b - q) / b
    kelly = (p * b - q) / b
    
    # If Kelly is negative, don't bet
    if kelly <= DECIMAL_ZERO:
        return DECIMAL_ZERO
    
    # Apply fractional Kelly
    fraction = kelly * fractional_kelly
    
    # Cap at 100% of bankroll
    return min(fraction, DECIMAL_ONE).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_edge(
    kalshi_price: Decimal,
    true_probability: Decimal,
    side: str = "yes"
) -> Decimal:
    """
    Calculate the edge (advantage) as a percentage.
    
    Args:
        kalshi_price: Kalshi price in cents (0-100)
        true_probability: Estimated true probability (0-1)
        side: "yes" or "no"
        
    Returns:
        Edge as a percentage (e.g., 10 means 10% edge)
        
    Example:
        If Kalshi price is 45¢ (45% implied) and true prob is 55%:
        Edge = 55% - 45% = 10%
    """
    kalshi_implied = kalshi_price_to_probability(kalshi_price)
    
    if side.lower() == "yes":
        edge = true_probability - kalshi_implied
    elif side.lower() == "no":
        edge = (DECIMAL_ONE - true_probability) - (DECIMAL_ONE - kalshi_implied)
    else:
        raise ValueError(f"Side must be 'yes' or 'no', got {side}")
    
    return (edge * DECIMAL_HUNDRED).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def remove_vig(home_odds: int, away_odds: int) -> tuple[Decimal, Decimal]:
    """
    Remove the vig (vigorish) from a two-way market to get true probabilities.
    
    Args:
        home_odds: American odds for home team
        away_odds: American odds for away team
        
    Returns:
        Tuple of (home_true_prob, away_true_prob) that sum to 1
        
    Example:
        remove_vig(-110, -110) -> (Decimal("0.5"), Decimal("0.5"))
        remove_vig(-150, +130) -> (Decimal("0.536"), Decimal("0.464"))
    """
    home_implied = american_to_implied_probability(home_odds)
    away_implied = american_to_implied_probability(away_odds)
    
    total_implied = home_implied + away_implied
    
    if total_implied == DECIMAL_ZERO:
        return Decimal("0.5"), Decimal("0.5")
    
    home_true = home_implied / total_implied
    away_true = away_implied / total_implied
    
    return (
        home_true.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        away_true.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    )
