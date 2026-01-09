"""
EV Multi-Book Arbitrage Strategy.

Compares Kalshi prices against individual sportsbook odds to find
positive expected value opportunities across multiple books.

Strategy Logic:
1. For each market, check Kalshi price vs each sportsbook
2. Calculate EV against each book individually
3. If multiple books agree on +EV, generate signal
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState, MarketState, OddsState
from backend.models.order import TradeSignal, OrderSide
from backend.utils.odds_calculator import (
    american_to_implied_probability,
    calculate_ev
)

logger = logging.getLogger(__name__)


class EVMultiBookStrategy(BaseStrategy):
    """
    EV Multi-Book Arbitrage Strategy.
    
    Finds opportunities where Kalshi prices offer positive expected value
    compared to multiple sportsbook odds.
    """
    
    STRATEGY_NAME = "EV Multi-Book Arbitrage"
    STRATEGY_TYPE = "ev_multibook"
    STRATEGY_DESCRIPTION = "Find +EV opportunities by comparing Kalshi to individual sportsbooks"
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "min_ev_percent": 3.0,           # Minimum EV percentage to consider
            "min_sportsbooks_agreeing": 2,   # Minimum books showing +EV
            "position_size": 10,             # Contracts per trade
            "cooldown_minutes": 5,           # Cooldown between trades
            "preferred_books": [],           # Empty = use all books
            "market_types": ["moneyline"],   # Market types to evaluate
            "exclude_books": []              # Books to ignore
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """Evaluate game state and generate EV-based signals."""
        if not self.is_enabled:
            return []
        
        signals = []
        
        # Need odds data to compare
        if not game_state.odds:
            return []
        
        for ticker, market in game_state.markets.items():
            signal = self._evaluate_market(game_state, market)
            if signal:
                signals.append(signal)
                self.record_signal(signal)
        
        return signals
    
    def _evaluate_market(
        self, 
        game_state: GameState, 
        market: MarketState
    ) -> Optional[TradeSignal]:
        """Evaluate a single market for multi-book EV opportunity."""
        
        # Check market type
        if market.market_type not in self.config["market_types"]:
            return None
        
        # Check cooldown
        if not self.check_cooldown(market.ticker):
            return None
        
        # Get orderbook
        if not market.orderbook:
            return None
        
        # Get Kalshi prices (already in cents)
        yes_ask = market.orderbook.yes_ask
        no_ask = market.orderbook.no_ask
        
        if not yes_ask or not no_ask:
            return None
        
        # Determine if this is home or away market
        ticker_parts = market.ticker.split("-")
        team_suffix = ticker_parts[-1] if ticker_parts else ""
        is_home_market = team_suffix.upper() == game_state.home_team.upper()
        
        # Calculate EV against each sportsbook
        yes_ev_books = []  # List of (book_name, ev, implied_prob)
        no_ev_books = []
        
        for book_name, odds_state in game_state.odds.items():
            # Skip excluded books
            if book_name in self.config.get("exclude_books", []):
                continue
            
            # Skip if preferred_books is set and this isn't in it
            preferred = self.config.get("preferred_books", [])
            if preferred and book_name not in preferred:
                continue
            
            # Get the relevant odds for this market
            book_prob = self._get_book_probability(odds_state, market, is_home_market)
            
            if book_prob is None:
                continue
            
            # Kalshi prices are already in cents (0-100)
            kalshi_yes_cents = Decimal(str(float(yes_ask)))
            kalshi_no_cents = Decimal(str(float(no_ask)))
            
            # Calculate EV for YES side (buying at yes_ask)
            ev_yes = calculate_ev(
                kalshi_price=kalshi_yes_cents,
                true_probability=book_prob,
                side="yes"
            )
            
            # Calculate EV for NO side
            ev_no = calculate_ev(
                kalshi_price=kalshi_no_cents,
                true_probability=Decimal("1") - book_prob,
                side="yes"  # NO side is like YES on the opposite
            )
            
            min_ev = Decimal(str(self.config["min_ev_percent"])) / 100
            
            if ev_yes >= min_ev:
                yes_ev_books.append((book_name, float(ev_yes), float(book_prob)))
            
            if ev_no >= min_ev:
                no_ev_books.append((book_name, float(ev_no), float(Decimal("1") - book_prob)))
        
        # Check if enough books agree
        min_books = self.config["min_sportsbooks_agreeing"]
        
        # Prefer the side with more agreeing books, or higher EV
        if len(yes_ev_books) >= min_books and len(yes_ev_books) >= len(no_ev_books):
            side = OrderSide.YES
            ev_books = yes_ev_books
            entry_price = yes_ask
        elif len(no_ev_books) >= min_books:
            side = OrderSide.NO
            ev_books = no_ev_books
            entry_price = no_ask
        else:
            return None
        
        # Sort by EV and get best
        ev_books.sort(key=lambda x: x[1], reverse=True)
        best_book, best_ev, best_prob = ev_books[0]
        
        # Record trade for cooldown
        self.record_trade(market.ticker)
        
        # Create signal
        signal = TradeSignal(
            strategy_id=self.strategy_id,
            strategy_name=self.STRATEGY_NAME,
            market_ticker=market.ticker,
            side=side,
            quantity=self.config["position_size"],
            confidence=min(len(ev_books) / 5, 1.0),  # More books = higher confidence
            reason=self._format_reason(side, best_book, best_ev, len(ev_books)),
            metadata={
                "best_book": best_book,
                "best_ev_percent": best_ev * 100,
                "best_implied_prob": best_prob,
                "agreeing_books": len(ev_books),
                "all_ev_books": [(b, ev * 100, prob) for b, ev, prob in ev_books],
                "entry_price": float(entry_price),
                "is_home_market": is_home_market
            }
        )
        
        logger.info(
            f"EV Multi-Book signal: {side.value.upper()} {self.config['position_size']} "
            f"{market.ticker} (best EV: {best_ev*100:.1f}% from {best_book}, "
            f"{len(ev_books)} books agree)"
        )
        
        return signal
    
    def _get_book_probability(
        self, 
        odds_state: OddsState, 
        market: MarketState,
        is_home_market: bool
    ) -> Optional[Decimal]:
        """
        Get implied probability from a sportsbook for this market.
        
        Handles mapping between market type and odds fields.
        """
        if market.market_type == "moneyline":
            if is_home_market:
                odds = odds_state.moneyline_home
            else:
                odds = odds_state.moneyline_away
            
            if odds is None:
                return None
            
            return american_to_implied_probability(odds)
        
        elif market.market_type == "spread":
            # For spreads, use spread odds
            if is_home_market:
                odds = odds_state.spread_home_odds
            else:
                odds = odds_state.spread_away_odds
            
            if odds is None:
                return None
            
            return american_to_implied_probability(odds)
        
        elif market.market_type == "total":
            # For totals, determine over/under from ticker
            # Tickers like KXNBATOTAL-26JAN08DALUTA-240 
            # YES = over, NO = under
            odds = odds_state.total_over_odds
            
            if odds is None:
                return None
            
            return american_to_implied_probability(odds)
        
        return None
    
    def _format_reason(
        self, 
        side: OrderSide, 
        best_book: str, 
        best_ev: float,
        num_books: int
    ) -> str:
        """Format human-readable reason for the signal."""
        return (
            f"{num_books} sportsbooks show +EV for {side.value.upper()}. "
            f"Best: {best_book} at +{best_ev*100:.1f}% EV."
        )
