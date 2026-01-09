"""
Order Execution Engine.

Handles the conversion of trading signals to orders, simulates execution,
and manages order lifecycle for paper trading.
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from decimal import Decimal
import uuid

from backend.models.order import (
    TradeSignal, SimulatedOrder, ExecutionPosition, ExecutionResult,
    OrderSide, OrderStatus, OrderType
)
from backend.models.game_state import GameState
from backend.engine.aggregator import get_aggregator
from backend.engine.risk_manager import get_risk_manager, RiskCheckResult
from backend.database import helpers as db
from backend.config.settings import settings
from backend.utils.pnl_calculator import PnLCalculator, PortfolioPnL

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Simulated Order Execution Engine.
    
    Responsibilities:
    - Convert signals to orders
    - Validate orders against risk limits
    - Simulate execution at market prices
    - Update positions
    - Store results in database
    """
    
    def __init__(self):
        """Initialize the execution engine."""
        # Track active orders
        self._pending_orders: Dict[str, SimulatedOrder] = {}
        
        # Track positions in memory (synced with DB)
        self._positions: Dict[str, ExecutionPosition] = {}  # market_ticker -> Position
        
        # Execution callbacks
        self._execution_callbacks: List[Callable] = []
        
        # Running state
        self._running = False
        
        # Configuration
        self._max_position_size = 100  # Max contracts per market
        self._max_daily_orders = 50    # Max orders per day
        self._daily_order_count = 0
        self._last_order_reset = datetime.utcnow().date()
        
        logger.info("ExecutionEngine initialized")
    
    async def start(self) -> None:
        """Start the execution engine."""
        if self._running:
            return
        
        self._running = True
        
        # Load existing open positions from database
        await self._load_positions()
        
        logger.info("ExecutionEngine started")
    
    async def stop(self) -> None:
        """Stop the execution engine."""
        self._running = False
        logger.info("ExecutionEngine stopped")
    
    # =========================================================================
    # Order Execution
    # =========================================================================
    
    async def execute_signal(
        self, 
        signal: TradeSignal,
        game_id: str
    ) -> ExecutionResult:
        """
        Execute a trading signal.
        
        Args:
            signal: The trade signal to execute
            game_id: The game ID for this trade
        
        Returns:
            ExecutionResult with order details
        """
        logger.info(
            f"Executing signal: {signal.side.value.upper()} {signal.quantity} "
            f"{signal.market_ticker} from {signal.strategy_name}"
        )
        
        # Reset daily counter if new day
        self._check_daily_reset()
        
        # Create order from signal
        order = SimulatedOrder(
            id=str(uuid.uuid4()),
            strategy_id=signal.strategy_id,
            game_id=game_id,
            market_id=None,
            market_ticker=signal.market_ticker,
            order_type=OrderType.MARKET,
            side=signal.side,
            quantity=signal.quantity,
            limit_price=None,
            filled_price=None,
            status=OrderStatus.PENDING,
            placed_at=datetime.utcnow(),
            filled_at=None,
            signal_data={
                "strategy_name": signal.strategy_name,
                "reason": signal.reason,
                "confidence": signal.confidence,
                "metadata": signal.metadata
            },
            created_at=datetime.utcnow()
        )
        
        # === RISK CHECK ===
        risk_manager = get_risk_manager()
        risk_result = risk_manager.check_order(order, self._positions)
        
        if not risk_result.approved:
            order.status = OrderStatus.CANCELLED
            
            await self._store_order(order, rejection_reason=f"Risk check failed: {risk_result.reason}")
            
            logger.warning(f"Order rejected by risk manager: {risk_result.reason}")
            return ExecutionResult(
                success=False, 
                order=order, 
                error=risk_result.reason
            )
        
        # Validate order
        validation_error = await self._validate_order(order)
        if validation_error:
            order.status = OrderStatus.CANCELLED
            
            # Store rejected order
            await self._store_order(order, rejection_reason=validation_error)
            
            logger.warning(f"Order rejected: {validation_error}")
            return ExecutionResult(success=False, order=order, error=validation_error)
        
        # Get current market price
        fill_price = await self._get_fill_price(order, game_id)
        
        if fill_price is None:
            order.status = OrderStatus.CANCELLED
            
            await self._store_order(order, rejection_reason="Could not get market price")
            
            logger.warning(f"Order rejected: Could not get market price for {order.market_ticker}")
            return ExecutionResult(success=False, order=order, error="No market price available")
        
        # Execute the order (simulate immediate fill)
        order.status = OrderStatus.FILLED
        order.filled_price = fill_price
        order.filled_at = datetime.utcnow()
        
        # Record with risk manager
        risk_manager.record_order(order, fill_price)
        
        # Update position
        position = await self._update_position(order, game_id)
        
        # Store order in database
        await self._store_order(order)
        
        # Increment daily counter
        self._daily_order_count += 1
        
        # Notify callbacks
        await self._notify_execution(order, position)
        
        logger.info(
            f"Order filled: {order.side.value.upper()} {order.quantity} "
            f"{order.market_ticker} @ {order.filled_price}¢"
        )
        
        return ExecutionResult(
            success=True,
            order=order,
            position_updated=True,
            new_position=position
        )
    
    async def execute_signals(
        self,
        signals: List[TradeSignal],
        game_id: str
    ) -> List[ExecutionResult]:
        """Execute multiple signals."""
        results = []
        for signal in signals:
            result = await self.execute_signal(signal, game_id)
            results.append(result)
        return results
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    async def _validate_order(self, order: SimulatedOrder) -> Optional[str]:
        """
        Validate an order before execution.
        
        Returns error message if invalid, None if valid.
        """
        # Check daily order limit
        if self._daily_order_count >= self._max_daily_orders:
            return f"Daily order limit reached ({self._max_daily_orders})"
        
        # Check position size limit
        current_position = self._positions.get(order.market_ticker)
        if current_position:
            new_size = current_position.quantity + order.quantity
            if new_size > self._max_position_size:
                return f"Position size limit exceeded ({new_size} > {self._max_position_size})"
        elif order.quantity > self._max_position_size:
            return f"Order quantity exceeds position limit ({order.quantity} > {self._max_position_size})"
        
        # Check if market exists in aggregator
        aggregator = get_aggregator()
        game_id = str(order.game_id)
        game_state = aggregator.get_game_state(game_id)
        if not game_state:
            return f"Game not loaded in aggregator: {game_id}"
        
        if order.market_ticker not in game_state.markets:
            return f"Market not found: {order.market_ticker}"
        
        return None
    
    # =========================================================================
    # Price and Position Management
    # =========================================================================
    
    async def _get_fill_price(self, order: SimulatedOrder, game_id: str) -> Optional[Decimal]:
        """Get the fill price for an order (simulated execution at ask)."""
        aggregator = get_aggregator()
        game_state = aggregator.get_game_state(game_id)
        
        if not game_state:
            return None
        
        market = game_state.markets.get(order.market_ticker)
        if not market or not market.orderbook:
            return None
        
        # For buys, use ask price
        if order.side == OrderSide.YES:
            price = market.orderbook.yes_ask
        else:
            price = market.orderbook.no_ask
        
        if price is None:
            return None
        
        # Ensure Decimal type
        return Decimal(str(price))
    
    async def _update_position(self, order: SimulatedOrder, game_id: str) -> ExecutionPosition:
        """Update position after order fill."""
        ticker = order.market_ticker
        
        # Get or create position
        if ticker in self._positions:
            position = self._positions[ticker]
        else:
            position = ExecutionPosition(
                game_id=game_id,
                market_ticker=ticker,
                side=order.side
            )
            self._positions[ticker] = position
        
        # Update position
        if position.side == order.side:
            # Adding to position
            old_cost = position.total_cost
            new_cost = order.filled_price * order.quantity
            position.total_cost = old_cost + new_cost
            position.quantity += order.quantity
            position.avg_entry_price = position.total_cost / position.quantity if position.quantity > 0 else Decimal("0")
        else:
            # Closing/reducing position (opposite side)
            # For simplicity, we'll handle this as a separate close
            # In full implementation, you'd net positions
            pass
        
        position.updated_at = datetime.utcnow()
        
        # Store in database
        await self._store_position(position)
        
        return position
    
    async def _load_positions(self) -> None:
        """Load open positions from database."""
        try:
            # Query open positions from database
            # For now, start fresh each session
            self._positions = {}
            logger.info("Positions loaded (starting fresh)")
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
    
    # =========================================================================
    # Database Operations
    # =========================================================================
    
    async def _store_order(self, order: SimulatedOrder, rejection_reason: str = None) -> None:
        """Store order in database."""
        try:
            # Check if strategy exists in database, set to None if not (manual orders)
            # This avoids foreign key constraint violations
            strategy_id = None
            if order.strategy_id:
                strategy_exists = await db.get_strategy_by_id(str(order.strategy_id))
                if strategy_exists:
                    strategy_id = str(order.strategy_id)
            
            order_data = {
                "id": str(order.id),
                "strategy_id": strategy_id,  # None for manual orders
                "game_id": str(order.game_id),
                "market_id": str(order.market_id) if order.market_id else None,
                "market_ticker": order.market_ticker,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": order.quantity,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "status": order.status.value,
                "filled_price": float(order.filled_price) if order.filled_price else None,
                "placed_at": order.placed_at.isoformat() if order.placed_at else None,
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "signal_data": order.signal_data
            }
            
            await db.create_simulated_order(order_data)
            logger.info(f"Order stored in database: {order.id}")
            
        except Exception as e:
            logger.warning(f"Could not store order in database: {e}")
    
    async def _store_position(self, position: ExecutionPosition) -> None:
        """Store/update position in database."""
        try:
            position_data = {
                "id": position.id,
                "game_id": position.game_id,
                "market_ticker": position.market_ticker,
                "side": position.side.value,
                "quantity": position.quantity,
                "avg_price": float(position.avg_entry_price),  # DB uses avg_price
                "unrealized_pnl": float(position.unrealized_pnl),
                "realized_pnl": float(position.realized_pnl),
                "opened_at": position.opened_at.isoformat(),
                "closed_at": position.closed_at.isoformat() if position.closed_at else None,
                "is_open": position.is_open
            }
            
            await db.upsert_position(position_data)
            logger.debug(f"Position stored: {position.market_ticker}")
            
        except Exception as e:
            logger.error(f"Error storing position: {e}")
    
    # =========================================================================
    # Callbacks and Utilities
    # =========================================================================
    
    def add_execution_callback(self, callback: Callable) -> None:
        """Add callback for execution notifications."""
        self._execution_callbacks.append(callback)
    
    def remove_execution_callback(self, callback: Callable) -> None:
        """Remove execution callback."""
        if callback in self._execution_callbacks:
            self._execution_callbacks.remove(callback)
    
    async def _notify_execution(self, order: SimulatedOrder, position: ExecutionPosition) -> None:
        """Notify callbacks of execution."""
        for callback in self._execution_callbacks:
            try:
                result = callback(order, position)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in execution callback: {e}")
    
    def _check_daily_reset(self) -> None:
        """Reset daily counters if new day."""
        today = datetime.utcnow().date()
        if today > self._last_order_reset:
            self._daily_order_count = 0
            self._last_order_reset = today
            logger.info("Daily order counter reset")
    
    # =========================================================================
    # Getters
    # =========================================================================
    
    def get_position(self, market_ticker: str) -> Optional[ExecutionPosition]:
        """Get current position for a market."""
        return self._positions.get(market_ticker)
    
    def get_all_positions(self) -> Dict[str, ExecutionPosition]:
        """Get all current positions."""
        return self._positions.copy()
    
    def get_open_positions(self) -> List[ExecutionPosition]:
        """Get all open positions."""
        return [p for p in self._positions.values() if p.is_open and p.quantity > 0]
    
    def get_daily_order_count(self) -> int:
        """Get today's order count."""
        return self._daily_order_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution engine statistics."""
        open_positions = self.get_open_positions()
        return {
            "running": self._running,
            "daily_order_count": self._daily_order_count,
            "max_daily_orders": self._max_daily_orders,
            "open_positions_count": len(open_positions),
            "total_positions_tracked": len(self._positions),
            "max_position_size": self._max_position_size
        }
    
    # =========================================================================
    # P&L Management
    # =========================================================================
    
    async def update_unrealized_pnl(self) -> Dict[str, Any]:
        """
        Update unrealized P&L for all open positions based on current market prices.
        
        Returns:
            Portfolio P&L summary
        """
        aggregator = get_aggregator()
        current_prices: Dict[str, Decimal] = {}
        
        # Get current prices for all positions
        for ticker, position in self._positions.items():
            if position.quantity <= 0:
                continue
            
            # Find the game and market for this position
            for game_id, game_state in aggregator.get_all_game_states().items():
                if ticker in game_state.markets:
                    market = game_state.markets[ticker]
                    if market.orderbook and market.orderbook.mid_price:
                        current_prices[ticker] = Decimal(str(market.orderbook.mid_price))
                    break
        
        # Calculate P&L for each position
        calc = PnLCalculator()
        for ticker, position in self._positions.items():
            if ticker in current_prices:
                position.unrealized_pnl = calc.calculate_unrealized_pnl(
                    position, current_prices[ticker]
                )
                position.updated_at = datetime.utcnow()
                
                # Update in database
                await self._store_position(position)
        
        # Calculate portfolio totals
        open_positions = self.get_open_positions()
        portfolio = PortfolioPnL.calculate_total_unrealized(open_positions, current_prices)
        
        logger.info(
            f"P&L updated: {portfolio['position_count']} positions, "
            f"unrealized P&L: {portfolio['total_unrealized_pnl']:.1f}¢"
        )
        
        return portfolio
    
    async def close_position(
        self,
        market_ticker: str,
        exit_price: Optional[Decimal] = None,
        reason: str = "manual_close"
    ) -> Optional[ExecutionPosition]:
        """
        Close a position and calculate realized P&L.
        
        Args:
            market_ticker: The market to close
            exit_price: Price to close at (uses current market if None)
            reason: Reason for closing
        
        Returns:
            The closed position with realized P&L
        """
        position = self._positions.get(market_ticker)
        if not position or position.quantity <= 0:
            logger.warning(f"No open position to close: {market_ticker}")
            return None
        
        # Get exit price if not provided
        if exit_price is None:
            aggregator = get_aggregator()
            for game_id, game_state in aggregator.get_all_game_states().items():
                if market_ticker in game_state.markets:
                    market = game_state.markets[market_ticker]
                    if market.orderbook:
                        # Use bid price for selling
                        if position.side == OrderSide.YES:
                            exit_price = Decimal(str(market.orderbook.yes_bid or 0))
                        else:
                            exit_price = Decimal(str(market.orderbook.no_bid or 0))
                    break
        
        if exit_price is None:
            logger.error(f"Could not get exit price for {market_ticker}")
            return None
        
        # Calculate realized P&L
        calc = PnLCalculator()
        realized_pnl = calc.calculate_realized_pnl(
            entry_price=position.avg_entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            side=position.side
        )
        
        # Record P&L with risk manager
        risk_manager = get_risk_manager()
        risk_manager.record_pnl(realized_pnl)
        risk_manager.record_position_close(
            market_ticker, 
            position.game_id, 
            position.quantity
        )
        
        # Update position
        position.realized_pnl += realized_pnl
        position.quantity = 0
        position.is_open = False
        position.closed_at = datetime.utcnow()
        position.updated_at = datetime.utcnow()
        
        # Store in database
        await self._store_position(position)
        
        logger.info(
            f"Position closed: {market_ticker}, realized P&L: {realized_pnl:.1f}¢ "
            f"(entry: {position.avg_entry_price:.1f}¢, exit: {exit_price:.1f}¢)"
        )
        
        return position
    
    async def settle_position(
        self,
        market_ticker: str,
        outcome: bool  # True = YES won, False = NO won
    ) -> Optional[ExecutionPosition]:
        """
        Settle a position at contract expiry.
        
        Args:
            market_ticker: The market to settle
            outcome: True if YES outcome, False if NO outcome
        
        Returns:
            The settled position with realized P&L
        """
        position = self._positions.get(market_ticker)
        if not position or position.quantity <= 0:
            logger.warning(f"No open position to settle: {market_ticker}")
            return None
        
        # Calculate settlement P&L
        calc = PnLCalculator()
        settlement_pnl = calc.calculate_settlement_pnl(position, outcome)
        
        # Update position
        position.realized_pnl += settlement_pnl
        position.unrealized_pnl = Decimal("0")
        position.quantity = 0
        position.is_open = False
        position.closed_at = datetime.utcnow()
        position.updated_at = datetime.utcnow()
        
        # Store in database
        await self._store_position(position)
        
        outcome_str = "YES" if outcome else "NO"
        logger.info(
            f"Position settled: {market_ticker}, outcome: {outcome_str}, "
            f"P&L: {settlement_pnl:.1f}¢"
        )
        
        return position
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of all positions and P&L."""
        open_positions = self.get_open_positions()
        
        total_cost = sum(float(p.total_cost) for p in open_positions)
        total_unrealized = sum(float(p.unrealized_pnl) for p in open_positions)
        total_realized = sum(float(p.realized_pnl) for p in self._positions.values())
        
        return {
            "open_positions": len(open_positions),
            "total_cost": total_cost,
            "total_unrealized_pnl": total_unrealized,
            "total_realized_pnl": total_realized,
            "total_pnl": total_unrealized + total_realized,
            "positions": [
                {
                    "ticker": p.market_ticker,
                    "side": p.side.value,
                    "quantity": p.quantity,
                    "avg_entry": float(p.avg_entry_price),
                    "cost": float(p.total_cost),
                    "unrealized_pnl": float(p.unrealized_pnl)
                }
                for p in open_positions
            ]
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_execution_engine: Optional[ExecutionEngine] = None


def get_execution_engine() -> ExecutionEngine:
    """Get or create the global ExecutionEngine instance."""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine()
    return _execution_engine
