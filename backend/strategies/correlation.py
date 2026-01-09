"""
Cross-Market Correlation Strategy.

Exploits pricing inefficiencies between related markets for the same game.
Detects when moneyline, spread, and total markets are inconsistently priced.

Strategy Logic:
1. Check if complementary markets (home/away) sum correctly
2. Check if moneyline and spread imply consistent probabilities
3. Trade when discrepancies exceed threshold
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState, MarketState
from backend.models.order import TradeSignal, OrderSide

logger = logging.getLogger(__name__)


class CorrelationStrategy(BaseStrategy):
    """
    Cross-Market Correlation Strategy.
    
    Finds arbitrage opportunities between related markets
    that should be mathematically consistent.
    """
    
    STRATEGY_NAME = "Cross-Market Correlation"
    STRATEGY_TYPE = "correlation"
    STRATEGY_DESCRIPTION = "Exploit pricing inefficiencies between correlated markets"
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "min_discrepancy_percent": 5.0,      # Min discrepancy to trigger
            "complementary_max_sum": 105.0,      # Max sum before overvalued
            "complementary_min_sum": 95.0,       # Min sum before undervalued
            "position_size": 10,
            "cooldown_minutes": 5,
            "check_complementary": True,          # Check home+away sum
            "check_moneyline_spread": True,       # Check ML vs spread
            "prefer_no_on_overvalued": True       # Buy NO when sum > max
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """Evaluate game state for correlation opportunities."""
        if not self.is_enabled:
            return []
        
        signals = []
        
        # Group markets by type
        moneyline_markets = {}
        spread_markets = {}
        total_markets = {}
        
        for ticker, market in game_state.markets.items():
            if market.market_type == "moneyline":
                # Extract team from ticker (last part after final hyphen)
                team = ticker.split("-")[-1]
                moneyline_markets[team] = market
            elif market.market_type == "spread":
                spread_markets[ticker] = market
            elif market.market_type == "total":
                total_markets[ticker] = market
        
        logger.info(
            f"DEBUG {game_state.game_id}: Found {len(moneyline_markets)} moneyline, "
            f"{len(spread_markets)} spread, {len(total_markets)} total markets"
        )
        
        # Check 1: Complementary moneyline markets
        if self.config["check_complementary"] and len(moneyline_markets) >= 2:
            complementary_signals = self._check_complementary_moneyline(
                game_state, moneyline_markets
            )
            signals.extend(complementary_signals)
        
        # Check 2: Moneyline vs Spread correlation
        if self.config["check_moneyline_spread"] and moneyline_markets and spread_markets:
            correlation_signals = self._check_moneyline_spread_correlation(
                game_state, moneyline_markets, spread_markets
            )
            signals.extend(correlation_signals)
        
        # Record signals
        for signal in signals:
            self.record_signal(signal)
        
        return signals
    
    def _check_complementary_moneyline(
        self,
        game_state: GameState,
        moneyline_markets: Dict[str, MarketState]
    ) -> List[TradeSignal]:
        """
        Check if home + away moneyline YES prices sum to ~100%.
        
        If sum > 105%: Both sides overvalued (vig too high or mispricing)
        If sum < 95%: Both sides undervalued (unusual)
        """
        signals = []
        
        home_team = game_state.home_team.upper()
        away_team = game_state.away_team.upper()
        
        home_market = moneyline_markets.get(home_team)
        away_market = moneyline_markets.get(away_team)
        
        if not home_market or not away_market:
            logger.info(f"DEBUG: Missing moneyline market (home={home_market is not None}, away={away_market is not None})")
            return []
        
        if not home_market.orderbook or not away_market.orderbook:
            logger.info(f"DEBUG: Missing orderbook for moneyline markets")
            return []
        
        # Get mid prices (YES probability for each team)
        home_yes = home_market.orderbook.mid_price
        away_yes = away_market.orderbook.mid_price
        
        if not home_yes or not away_yes:
            return []
        
        # Calculate sum (in percentage)
        total_sum = float(home_yes) + float(away_yes)
        
        logger.info(
            f"DEBUG Complementary: {home_team} YES={float(home_yes):.1f}%, "
            f"{away_team} YES={float(away_yes):.1f}%, Sum={total_sum:.1f}%"
        )
        
        max_sum = self.config["complementary_max_sum"]
        min_sum = self.config["complementary_min_sum"]
        
        # Check for overvaluation (sum too high)
        if total_sum > max_sum:
            excess = total_sum - 100
            logger.info(f"DEBUG: Complementary sum {total_sum:.1f}% > {max_sum}% (excess: {excess:.1f}%)")
            
            # Determine which side is more overvalued
            # Buy NO on the side that's further from fair value
            # If home is 60% and away is 50%, sum is 110%, but 60% is more "wrong"
            
            if self.config["prefer_no_on_overvalued"]:
                # Buy NO on the higher priced (more overvalued) side
                if float(home_yes) > float(away_yes):
                    target_market = home_market
                    target_team = home_team
                else:
                    target_market = away_market
                    target_team = away_team
                
                # Check cooldown
                if not self.check_cooldown(target_market.ticker):
                    logger.info(f"DEBUG {target_market.ticker}: SKIP in cooldown")
                    return []
                
                self.record_trade(target_market.ticker)
                
                signal = TradeSignal(
                    strategy_id=self.strategy_id,
                    strategy_name=self.STRATEGY_NAME,
                    market_ticker=target_market.ticker,
                    side=OrderSide.NO,
                    quantity=self.config["position_size"],
                    confidence=min(excess / 10, 1.0),
                    reason=self._format_complementary_reason(
                        home_team, away_team, home_yes, away_yes, total_sum
                    ),
                    metadata={
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_yes_price": float(home_yes),
                        "away_yes_price": float(away_yes),
                        "total_sum": total_sum,
                        "excess_percent": excess,
                        "signal_type": "complementary_overvalued"
                    }
                )
                
                logger.info(
                    f"Correlation signal: NO {self.config['position_size']} {target_market.ticker} "
                    f"(complementary sum: {total_sum:.1f}%)"
                )
                
                signals.append(signal)
        
        elif total_sum < min_sum:
            # Both undervalued - less common, could buy YES on either
            shortfall = 100 - total_sum
            logger.info(
                f"DEBUG: Complementary sum {total_sum:.1f}% < {min_sum}% "
                f"(shortfall: {shortfall:.1f}%) - both undervalued"
            )
            # For now, we don't generate signals for undervaluation
            # as it's less reliable
        else:
            logger.info(f"DEBUG: Complementary sum {total_sum:.1f}% within normal range [{min_sum}, {max_sum}]")
        
        return signals
    
    def _check_moneyline_spread_correlation(
        self,
        game_state: GameState,
        moneyline_markets: Dict[str, MarketState],
        spread_markets: Dict[str, MarketState]
    ) -> List[TradeSignal]:
        """
        Check if moneyline and spread markets are consistently priced.
        
        Higher moneyline probability should correlate with covering larger spreads.
        """
        signals = []
        
        home_team = game_state.home_team.upper()
        away_team = game_state.away_team.upper()
        
        # Get moneyline prices
        home_ml = moneyline_markets.get(home_team)
        away_ml = moneyline_markets.get(away_team)
        
        if not home_ml or not away_ml:
            return []
        
        if not home_ml.orderbook or not away_ml.orderbook:
            return []
        
        home_ml_prob = float(home_ml.orderbook.mid_price or 0)
        away_ml_prob = float(away_ml.orderbook.mid_price or 0)
        
        # Determine favorite
        if home_ml_prob > away_ml_prob:
            favorite_team = home_team
            favorite_prob = home_ml_prob
            underdog_team = away_team
        else:
            favorite_team = away_team
            favorite_prob = away_ml_prob
            underdog_team = home_team
        
        logger.info(
            f"DEBUG ML vs Spread: Favorite={favorite_team} at {favorite_prob:.1f}%, "
            f"checking {len(spread_markets)} spread markets"
        )
        
        # Find spread markets for the favorite
        # Spread tickers look like: KXNBASPREAD-26JAN08DALUTA-DAL7
        # The number at the end is the spread value
        
        for ticker, spread_market in spread_markets.items():
            if not spread_market.orderbook:
                continue
            
            # Extract team and spread from ticker
            parts = ticker.split("-")
            if len(parts) < 3:
                continue
            
            team_spread = parts[-1]  # e.g., "DAL7" or "UTA5"
            
            # Parse team and spread value
            team = ""
            spread_value = 0
            for i, char in enumerate(team_spread):
                if char.isdigit():
                    team = team_spread[:i]
                    try:
                        spread_value = int(team_spread[i:])
                    except ValueError:
                        continue
                    break
            
            if not team:
                continue
            
            # Only check spread markets for the favorite
            if team.upper() != favorite_team:
                continue
            
            spread_prob = float(spread_market.orderbook.mid_price or 0)
            
            # Estimate expected spread probability based on moneyline
            # This is a simplified model:
            # - 50% ML ≈ 50% spread coverage (pick'em)
            # - 60% ML ≈ 55% spread coverage (-3 to -5)
            # - 70% ML ≈ 60% spread coverage (-6 to -8)
            # Formula: spread_prob ≈ 50 + (ml_prob - 50) * 0.5
            expected_spread_prob = 50 + (favorite_prob - 50) * 0.5
            
            discrepancy = spread_prob - expected_spread_prob
            
            logger.info(
                f"DEBUG {ticker}: spread_prob={spread_prob:.1f}%, "
                f"expected={expected_spread_prob:.1f}% (from ML {favorite_prob:.1f}%), "
                f"discrepancy={discrepancy:+.1f}%"
            )
            
            min_disc = self.config["min_discrepancy_percent"]
            
            if abs(discrepancy) >= min_disc:
                # Check cooldown
                if not self.check_cooldown(ticker):
                    logger.info(f"DEBUG {ticker}: SKIP in cooldown")
                    continue
                
                # Spread is mispriced relative to moneyline
                if discrepancy > 0:
                    # Spread probability too high → BUY NO
                    side = OrderSide.NO
                    entry_price = spread_market.orderbook.no_ask
                else:
                    # Spread probability too low → BUY YES
                    side = OrderSide.YES
                    entry_price = spread_market.orderbook.yes_ask
                
                if not entry_price:
                    continue
                
                self.record_trade(ticker)
                
                signal = TradeSignal(
                    strategy_id=self.strategy_id,
                    strategy_name=self.STRATEGY_NAME,
                    market_ticker=ticker,
                    side=side,
                    quantity=self.config["position_size"],
                    confidence=min(abs(discrepancy) / 10, 1.0),
                    reason=self._format_correlation_reason(
                        ticker, spread_prob, expected_spread_prob, favorite_prob, favorite_team
                    ),
                    metadata={
                        "spread_ticker": ticker,
                        "spread_value": spread_value,
                        "spread_prob": spread_prob,
                        "expected_spread_prob": expected_spread_prob,
                        "moneyline_prob": favorite_prob,
                        "favorite_team": favorite_team,
                        "discrepancy": discrepancy,
                        "signal_type": "ml_spread_correlation"
                    }
                )
                
                logger.info(
                    f"Correlation signal: {side.value.upper()} {self.config['position_size']} "
                    f"{ticker} (ML-spread discrepancy: {discrepancy:+.1f}%)"
                )
                
                signals.append(signal)
        
        return signals
    
    def _format_complementary_reason(
        self,
        home_team: str,
        away_team: str,
        home_yes: Decimal,
        away_yes: Decimal,
        total_sum: float
    ) -> str:
        """Format reason for complementary market signal."""
        return (
            f"Complementary markets overvalued: {home_team} YES {float(home_yes):.1f}% + "
            f"{away_team} YES {float(away_yes):.1f}% = {total_sum:.1f}% (should be ~100%)"
        )
    
    def _format_correlation_reason(
        self,
        ticker: str,
        spread_prob: float,
        expected_prob: float,
        ml_prob: float,
        favorite: str
    ) -> str:
        """Format reason for ML-spread correlation signal."""
        direction = "overvalued" if spread_prob > expected_prob else "undervalued"
        return (
            f"Spread {direction}: priced at {spread_prob:.1f}% but moneyline "
            f"({favorite} {ml_prob:.1f}%) implies {expected_prob:.1f}%"
        )
