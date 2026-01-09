"""
Sharp Line Detection Strategy.

Compares Kalshi market prices to professional sportsbook odds consensus.
Generates trade signals when significant divergences are detected.

Strategy Logic:
1. Get Kalshi price for a market (implied probability)
2. Get consensus probability from multiple sportsbooks
3. If divergence > threshold:
   - Kalshi undervalued (prob < consensus) → BUY YES
   - Kalshi overvalued (prob > consensus) → BUY NO
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import logging

from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState, MarketState, ConsensusOdds
from backend.models.order import TradeSignal, OrderSide
from backend.utils.odds_calculator import (
    kalshi_price_to_probability,
    calculate_ev,
    calculate_kelly_fraction
)

logger = logging.getLogger(__name__)


class SharpLineStrategy(BaseStrategy):
    """
    Sharp Line Detection Strategy.
    
    Detects when Kalshi prices diverge significantly from sportsbook consensus
    and generates trade signals to exploit the mispricing.
    """
    
    STRATEGY_NAME = "Sharp Line Detection"
    STRATEGY_TYPE = "sharp_line"
    STRATEGY_DESCRIPTION = "Compare Kalshi prices to sportsbook consensus and trade on divergences"
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "threshold_percent": 5.0,       # Min % divergence to trigger signal
            "min_sample_sportsbooks": 3,    # Min sportsbooks for valid consensus
            "position_size": 10,            # Contracts per trade
            "cooldown_minutes": 5,          # Minutes between trades on same market
            "min_ev_percent": 2.0,          # Minimum expected value to trade
            "market_types": ["moneyline"],  # Which market types to trade
            "use_kelly_sizing": False,      # Use Kelly criterion for position sizing
            "kelly_fraction": 0.25          # Fraction of Kelly to use (quarter Kelly)
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """
        Evaluate game state and generate trade signals.
        
        Args:
            game_state: Current unified game state
        
        Returns:
            List of TradeSignal objects
        """
        if not self.is_enabled:
            return []
        
        signals = []
        
        # Check if we have consensus odds
        if not game_state.consensus:
            logger.debug(f"No consensus odds available for {game_state.game_id}")
            return []
        
        # Check minimum sportsbook sources
        if game_state.consensus.num_sportsbooks < self.config["min_sample_sportsbooks"]:
            logger.debug(
                f"Insufficient sportsbook sources: {game_state.consensus.num_sportsbooks} < "
                f"{self.config['min_sample_sportsbooks']}"
            )
            return []
        
        # Evaluate each market
        for ticker, market in game_state.markets.items():
            signal = await self._evaluate_market(game_state, market)
            if signal:
                signals.append(signal)
                self.record_signal(signal)
        
        return signals
    
    async def _evaluate_market(
        self, 
        game_state: GameState, 
        market: MarketState
    ) -> Optional[TradeSignal]:
        """
        Evaluate a single market for trading opportunity.
        
        Args:
            game_state: Current game state
            market: Market to evaluate
        
        Returns:
            TradeSignal if opportunity exists, None otherwise
        """
        # Check if market type is enabled
        if market.market_type not in self.config["market_types"]:
            return None
        
        # Check cooldown
        if not self.check_cooldown(market.ticker):
            return None
        
        # Get orderbook
        if not market.orderbook:
            return None
        
        # Get Kalshi implied probability (use mid price)
        kalshi_price = market.orderbook.mid_price
        if not kalshi_price or kalshi_price <= 0:
            return None
        
        # Kalshi prices are in cents (0-100), convert to probability (0-1)
        kalshi_prob = kalshi_price / Decimal("100")
        
        # Get consensus probability for this market type
        consensus_prob = self._get_consensus_for_market(game_state, market)
        if not consensus_prob:
            return None
        
        # Calculate divergence
        divergence = float(consensus_prob - kalshi_prob)
        divergence_percent = abs(divergence) * 100
        
        # Check threshold
        if divergence_percent < self.config["threshold_percent"]:
            return None
        
        # Determine trade direction
        if divergence > 0:
            # Kalshi undervalued (prob < consensus) → BUY YES
            side = OrderSide.YES
            # Use ask price for buying
            entry_price = market.orderbook.yes_ask
        else:
            # Kalshi overvalued (prob > consensus) → BUY NO
            side = OrderSide.NO
            entry_price = market.orderbook.no_ask
        
        if not entry_price or entry_price <= 0:
            return None
        
        # Calculate expected value
        # entry_price is already in cents (0-100 range) from Kalshi
        ev = calculate_ev(
            kalshi_price=entry_price,
            true_probability=consensus_prob,
            side=side.value
        )
        
        # Check minimum EV
        min_ev = Decimal(str(self.config["min_ev_percent"])) / 100
        if ev < min_ev:
            logger.debug(f"EV {ev} below minimum {min_ev} for {market.ticker}")
            return None
        
        # Calculate position size
        if self.config["use_kelly_sizing"]:
            kelly = calculate_kelly_fraction(
                kalshi_price=entry_price,
                true_probability=consensus_prob,
                side=side.value,
                fractional_kelly=Decimal(str(self.config["kelly_fraction"]))
            )
            # Scale position size by Kelly fraction (assuming base size is max)
            position_size = max(1, int(self.config["position_size"] * float(kelly) * 4))
        else:
            position_size = self.config["position_size"]
        
        # Create trade signal
        signal = TradeSignal(
            strategy_id=self.strategy_id,
            strategy_name=self.STRATEGY_NAME,
            market_ticker=market.ticker,
            side=side,
            quantity=position_size,
            confidence=min(divergence_percent / 10, 1.0),  # Scale confidence 0-1
            reason=self._format_reason(
                market, side, kalshi_prob, consensus_prob, divergence_percent, ev
            ),
            metadata={
                "kalshi_prob": float(kalshi_prob),
                "consensus_prob": float(consensus_prob),
                "divergence_percent": divergence_percent,
                "expected_value": float(ev),
                "entry_price_cents": float(entry_price),
                "market_type": market.market_type,
                "sources_count": game_state.consensus.num_sportsbooks
            }
        )
        
        logger.info(
            f"Sharp Line signal: {side.value.upper()} {position_size} {market.ticker} "
            f"(divergence: {divergence_percent:.1f}%, EV: {float(ev)*100:.2f}%)"
        )
        
        # Record trade for cooldown tracking
        self.record_trade(market.ticker)
        
        return signal
    
    def _get_consensus_for_market(
        self, 
        game_state: GameState, 
        market: MarketState
    ) -> Optional[Decimal]:
        """
        Get consensus probability for a specific market.
        
        Maps market type to the appropriate consensus odds field.
        """
        if not game_state.consensus:
            return None
        
        consensus = game_state.consensus
        prob = None
        
        if market.market_type == "moneyline":
            # The team suffix is the last part after the final hyphen
            # e.g., KXNBAGAME-26JAN08DALUTA-DAL -> DAL
            ticker_parts = market.ticker.split("-")
            team_suffix = ticker_parts[-1] if ticker_parts else ""
            
            # Check if this market is for the home team
            if team_suffix.upper() == game_state.home_team.upper():
                prob = consensus.home_win_probability
            else:
                prob = consensus.away_win_probability
        
        elif market.market_type == "spread":
            prob = consensus.spread_home_probability
        
        elif market.market_type == "total":
            prob = consensus.over_probability
        
        # Ensure we return a Decimal if value exists
        if prob is not None:
            return Decimal(str(prob)) if not isinstance(prob, Decimal) else prob
        
        return None
    
    def _format_reason(
        self,
        market: MarketState,
        side: OrderSide,
        kalshi_prob: Decimal,
        consensus_prob: Decimal,
        divergence_percent: float,
        ev: Decimal
    ) -> str:
        """Format human-readable reason for the signal."""
        direction = "undervalued" if side == OrderSide.YES else "overvalued"
        return (
            f"Kalshi {direction} by {divergence_percent:.1f}%. "
            f"Kalshi: {float(kalshi_prob)*100:.1f}%, Consensus: {float(consensus_prob)*100:.1f}%. "
            f"EV: +{float(ev)*100:.1f}%"
        )
