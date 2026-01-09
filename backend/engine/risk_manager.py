"""
Risk Management System.

Enforces trading limits and risk controls to protect the portfolio.
Validates orders before execution and tracks risk metrics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from backend.models.order import SimulatedOrder, OrderSide

logger = logging.getLogger(__name__)


class RiskLimitType(str, Enum):
    """Types of risk limits."""
    # Position limits
    MAX_CONTRACTS_PER_MARKET = "max_contracts_per_market"
    MAX_CONTRACTS_PER_GAME = "max_contracts_per_game"
    MAX_TOTAL_CONTRACTS = "max_total_contracts"
    
    # Loss limits
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_WEEKLY_LOSS = "max_weekly_loss"
    MAX_PER_TRADE_RISK = "max_per_trade_risk"
    
    # Exposure limits
    MAX_TOTAL_EXPOSURE = "max_total_exposure"
    MAX_EXPOSURE_PER_GAME = "max_exposure_per_game"
    MAX_EXPOSURE_PER_STRATEGY = "max_exposure_per_strategy"
    
    # Trading limits
    MAX_ORDERS_PER_DAY = "max_orders_per_day"
    MAX_ORDERS_PER_HOUR = "max_orders_per_hour"
    LOSS_STREAK_COOLDOWN = "loss_streak_cooldown"


class RiskCheckResult:
    """Result of a risk check."""
    
    def __init__(
        self, 
        approved: bool, 
        reason: Optional[str] = None,
        limit_type: Optional[RiskLimitType] = None,
        current_value: Optional[float] = None,
        limit_value: Optional[float] = None
    ):
        self.approved = approved
        self.reason = reason
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value
    
    def __bool__(self):
        return self.approved
    
    def to_dict(self) -> Dict:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "limit_type": self.limit_type.value if self.limit_type else None,
            "current_value": self.current_value,
            "limit_value": self.limit_value
        }


class RiskManager:
    """
    Risk Management System.
    
    Validates trades against risk limits and tracks risk metrics.
    """
    
    # Default risk limits
    DEFAULT_LIMITS = {
        RiskLimitType.MAX_CONTRACTS_PER_MARKET: 100,
        RiskLimitType.MAX_CONTRACTS_PER_GAME: 200,
        RiskLimitType.MAX_TOTAL_CONTRACTS: 500,
        RiskLimitType.MAX_DAILY_LOSS: 1000,        # cents
        RiskLimitType.MAX_WEEKLY_LOSS: 5000,       # cents
        RiskLimitType.MAX_PER_TRADE_RISK: 500,     # cents
        RiskLimitType.MAX_TOTAL_EXPOSURE: 10000,   # cents
        RiskLimitType.MAX_EXPOSURE_PER_GAME: 2000, # cents
        RiskLimitType.MAX_EXPOSURE_PER_STRATEGY: 3000,  # cents
        RiskLimitType.MAX_ORDERS_PER_DAY: 50,
        RiskLimitType.MAX_ORDERS_PER_HOUR: 20,
        RiskLimitType.LOSS_STREAK_COOLDOWN: 3,     # consecutive losses before pause
    }
    
    def __init__(self):
        """Initialize the risk manager."""
        # Current limits (can be customized)
        self._limits: Dict[RiskLimitType, float] = self.DEFAULT_LIMITS.copy()
        
        # Tracking
        self._daily_loss: Decimal = Decimal("0")
        self._weekly_loss: Decimal = Decimal("0")
        self._hourly_orders: List[datetime] = []
        self._daily_orders: List[datetime] = []
        self._consecutive_losses: int = 0
        self._last_loss_time: Optional[datetime] = None
        self._cooldown_until: Optional[datetime] = None
        
        # Track by game/strategy
        self._exposure_by_game: Dict[str, Decimal] = {}
        self._exposure_by_strategy: Dict[str, Decimal] = {}
        self._contracts_by_market: Dict[str, int] = {}
        self._contracts_by_game: Dict[str, int] = {}
        
        # Last reset times
        self._last_daily_reset = datetime.utcnow().date()
        self._last_weekly_reset = datetime.utcnow().date()
        
        # Whether risk management is enabled
        self._enabled = True
        
        logger.info("RiskManager initialized with default limits")
    
    # =========================================================================
    # Risk Checks
    # =========================================================================
    
    def check_order(
        self, 
        order: SimulatedOrder,
        current_positions: Dict[str, Any]
    ) -> RiskCheckResult:
        """
        Perform all risk checks on an order.
        
        Args:
            order: The order to validate
            current_positions: Current open positions
        
        Returns:
            RiskCheckResult indicating if order is approved
        """
        if not self._enabled:
            return RiskCheckResult(approved=True, reason="Risk management disabled")
        
        # Reset counters if needed
        self._check_resets()
        
        # Check cooldown from loss streak
        if self._cooldown_until and datetime.utcnow() < self._cooldown_until:
            remaining = (self._cooldown_until - datetime.utcnow()).seconds
            return RiskCheckResult(
                approved=False,
                reason=f"In cooldown after {self._consecutive_losses} consecutive losses. {remaining}s remaining.",
                limit_type=RiskLimitType.LOSS_STREAK_COOLDOWN
            )
        
        # Run all checks
        checks = [
            self._check_position_limits(order, current_positions),
            self._check_loss_limits(order),
            self._check_exposure_limits(order),
            self._check_trading_limits(),
            self._check_per_trade_risk(order),
        ]
        
        # Return first failure
        for check in checks:
            if not check.approved:
                logger.warning(f"Risk check failed: {check.reason}")
                return check
        
        return RiskCheckResult(approved=True, reason="All risk checks passed")
    
    def _check_position_limits(
        self, 
        order: SimulatedOrder,
        current_positions: Dict[str, Any]
    ) -> RiskCheckResult:
        """Check position size limits."""
        
        # Current contracts in this market
        current_market_contracts = self._contracts_by_market.get(order.market_ticker, 0)
        new_market_total = current_market_contracts + order.quantity
        
        limit = self._limits[RiskLimitType.MAX_CONTRACTS_PER_MARKET]
        if new_market_total > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Would exceed max contracts per market ({new_market_total} > {limit})",
                limit_type=RiskLimitType.MAX_CONTRACTS_PER_MARKET,
                current_value=current_market_contracts,
                limit_value=limit
            )
        
        # Current contracts in this game
        game_id = str(order.game_id)
        current_game_contracts = self._contracts_by_game.get(game_id, 0)
        new_game_total = current_game_contracts + order.quantity
        
        limit = self._limits[RiskLimitType.MAX_CONTRACTS_PER_GAME]
        if new_game_total > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Would exceed max contracts per game ({new_game_total} > {limit})",
                limit_type=RiskLimitType.MAX_CONTRACTS_PER_GAME,
                current_value=current_game_contracts,
                limit_value=limit
            )
        
        # Total contracts across all positions
        total_contracts = sum(self._contracts_by_market.values()) + order.quantity
        
        limit = self._limits[RiskLimitType.MAX_TOTAL_CONTRACTS]
        if total_contracts > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Would exceed max total contracts ({total_contracts} > {limit})",
                limit_type=RiskLimitType.MAX_TOTAL_CONTRACTS,
                current_value=sum(self._contracts_by_market.values()),
                limit_value=limit
            )
        
        return RiskCheckResult(approved=True)
    
    def _check_loss_limits(self, order: SimulatedOrder) -> RiskCheckResult:
        """Check loss limits."""
        
        # Daily loss limit
        limit = self._limits[RiskLimitType.MAX_DAILY_LOSS]
        if float(self._daily_loss) >= limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Daily loss limit reached ({self._daily_loss}¢ >= {limit}¢)",
                limit_type=RiskLimitType.MAX_DAILY_LOSS,
                current_value=float(self._daily_loss),
                limit_value=limit
            )
        
        # Weekly loss limit
        limit = self._limits[RiskLimitType.MAX_WEEKLY_LOSS]
        if float(self._weekly_loss) >= limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Weekly loss limit reached ({self._weekly_loss}¢ >= {limit}¢)",
                limit_type=RiskLimitType.MAX_WEEKLY_LOSS,
                current_value=float(self._weekly_loss),
                limit_value=limit
            )
        
        return RiskCheckResult(approved=True)
    
    def _check_exposure_limits(self, order: SimulatedOrder) -> RiskCheckResult:
        """Check exposure/capital limits."""
        
        # Estimate order cost (price * quantity)
        # For now, assume worst case of 100¢ per contract
        estimated_cost = order.quantity * 100  # Will be refined with actual price
        
        # Total exposure
        total_exposure = sum(float(v) for v in self._exposure_by_game.values())
        new_total = total_exposure + estimated_cost
        
        limit = self._limits[RiskLimitType.MAX_TOTAL_EXPOSURE]
        if new_total > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Would exceed max total exposure ({new_total}¢ > {limit}¢)",
                limit_type=RiskLimitType.MAX_TOTAL_EXPOSURE,
                current_value=total_exposure,
                limit_value=limit
            )
        
        # Per-game exposure
        game_id = str(order.game_id)
        game_exposure = float(self._exposure_by_game.get(game_id, 0))
        new_game_exposure = game_exposure + estimated_cost
        
        limit = self._limits[RiskLimitType.MAX_EXPOSURE_PER_GAME]
        if new_game_exposure > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Would exceed max exposure per game ({new_game_exposure}¢ > {limit}¢)",
                limit_type=RiskLimitType.MAX_EXPOSURE_PER_GAME,
                current_value=game_exposure,
                limit_value=limit
            )
        
        # Per-strategy exposure
        strategy_id = str(order.strategy_id) if order.strategy_id else None
        if strategy_id:
            strategy_exposure = float(self._exposure_by_strategy.get(strategy_id, 0))
            new_strategy_exposure = strategy_exposure + estimated_cost
            
            limit = self._limits[RiskLimitType.MAX_EXPOSURE_PER_STRATEGY]
            if new_strategy_exposure > limit:
                return RiskCheckResult(
                    approved=False,
                    reason=f"Would exceed max exposure per strategy ({new_strategy_exposure}¢ > {limit}¢)",
                    limit_type=RiskLimitType.MAX_EXPOSURE_PER_STRATEGY,
                    current_value=strategy_exposure,
                    limit_value=limit
                )
        
        return RiskCheckResult(approved=True)
    
    def _check_trading_limits(self) -> RiskCheckResult:
        """Check trading frequency limits."""
        
        now = datetime.utcnow()
        
        # Hourly order limit
        hour_ago = now - timedelta(hours=1)
        recent_hourly = [t for t in self._hourly_orders if t > hour_ago]
        self._hourly_orders = recent_hourly  # Clean up old entries
        
        limit = self._limits[RiskLimitType.MAX_ORDERS_PER_HOUR]
        if len(recent_hourly) >= limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Hourly order limit reached ({len(recent_hourly)} >= {limit})",
                limit_type=RiskLimitType.MAX_ORDERS_PER_HOUR,
                current_value=len(recent_hourly),
                limit_value=limit
            )
        
        # Daily order limit
        limit = self._limits[RiskLimitType.MAX_ORDERS_PER_DAY]
        if len(self._daily_orders) >= limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Daily order limit reached ({len(self._daily_orders)} >= {limit})",
                limit_type=RiskLimitType.MAX_ORDERS_PER_DAY,
                current_value=len(self._daily_orders),
                limit_value=limit
            )
        
        return RiskCheckResult(approved=True)
    
    def _check_per_trade_risk(self, order: SimulatedOrder) -> RiskCheckResult:
        """Check per-trade risk limit."""
        
        # Maximum loss on this trade = quantity * price (lose entire investment)
        # For conservative estimate, use quantity * 100 (max possible loss)
        max_trade_risk = order.quantity * 100
        
        limit = self._limits[RiskLimitType.MAX_PER_TRADE_RISK]
        if max_trade_risk > limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Per-trade risk too high ({max_trade_risk}¢ > {limit}¢)",
                limit_type=RiskLimitType.MAX_PER_TRADE_RISK,
                current_value=max_trade_risk,
                limit_value=limit
            )
        
        return RiskCheckResult(approved=True)
    
    # =========================================================================
    # Update Methods (called after order execution)
    # =========================================================================
    
    def record_order(self, order: SimulatedOrder, fill_price: Decimal) -> None:
        """Record an executed order for tracking."""
        now = datetime.utcnow()
        
        # Update order counts
        self._hourly_orders.append(now)
        self._daily_orders.append(now)
        
        # Update position tracking
        self._contracts_by_market[order.market_ticker] = \
            self._contracts_by_market.get(order.market_ticker, 0) + order.quantity
        
        game_id = str(order.game_id)
        self._contracts_by_game[game_id] = \
            self._contracts_by_game.get(game_id, 0) + order.quantity
        
        # Update exposure tracking
        order_cost = fill_price * order.quantity
        
        self._exposure_by_game[game_id] = \
            self._exposure_by_game.get(game_id, Decimal("0")) + order_cost
        
        strategy_id = str(order.strategy_id) if order.strategy_id else None
        if strategy_id and strategy_id != "manual":
            self._exposure_by_strategy[strategy_id] = \
                self._exposure_by_strategy.get(strategy_id, Decimal("0")) + order_cost
        
        logger.debug(f"Recorded order: {order.market_ticker}, cost: {order_cost}¢")
    
    def record_pnl(self, pnl: Decimal) -> None:
        """Record P&L from a closed position."""
        if pnl < 0:
            # It's a loss
            self._daily_loss += abs(pnl)
            self._weekly_loss += abs(pnl)
            self._consecutive_losses += 1
            self._last_loss_time = datetime.utcnow()
            
            # Check for loss streak cooldown
            streak_limit = self._limits[RiskLimitType.LOSS_STREAK_COOLDOWN]
            if self._consecutive_losses >= streak_limit:
                self._cooldown_until = datetime.utcnow() + timedelta(minutes=5)
                logger.warning(
                    f"Loss streak cooldown triggered: {self._consecutive_losses} consecutive losses. "
                    f"Cooldown until {self._cooldown_until}"
                )
        else:
            # It's a win - reset consecutive losses
            self._consecutive_losses = 0
        
        logger.info(f"Recorded P&L: {pnl}¢, daily loss: {self._daily_loss}¢, streak: {self._consecutive_losses}")
    
    def record_position_close(self, market_ticker: str, game_id: str, quantity: int) -> None:
        """Record a position being closed."""
        # Reduce contract counts
        if market_ticker in self._contracts_by_market:
            self._contracts_by_market[market_ticker] = max(
                0, self._contracts_by_market[market_ticker] - quantity
            )
        
        if game_id in self._contracts_by_game:
            self._contracts_by_game[game_id] = max(
                0, self._contracts_by_game[game_id] - quantity
            )
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def set_limit(self, limit_type: RiskLimitType, value: float) -> None:
        """Set a risk limit."""
        self._limits[limit_type] = value
        logger.info(f"Risk limit updated: {limit_type.value} = {value}")
    
    def get_limit(self, limit_type: RiskLimitType) -> float:
        """Get a risk limit value."""
        return self._limits.get(limit_type, 0)
    
    def get_all_limits(self) -> Dict[str, float]:
        """Get all risk limits."""
        return {k.value: v for k, v in self._limits.items()}
    
    def enable(self) -> None:
        """Enable risk management."""
        self._enabled = True
        logger.info("Risk management enabled")
    
    def disable(self) -> None:
        """Disable risk management (use with caution!)."""
        self._enabled = False
        logger.warning("Risk management DISABLED")
    
    def is_enabled(self) -> bool:
        """Check if risk management is enabled."""
        return self._enabled
    
    # =========================================================================
    # Reset and Status
    # =========================================================================
    
    def _check_resets(self) -> None:
        """Check and perform daily/weekly resets."""
        today = datetime.utcnow().date()
        
        # Daily reset
        if today > self._last_daily_reset:
            self._daily_loss = Decimal("0")
            self._daily_orders = []
            self._last_daily_reset = today
            logger.info("Daily risk counters reset")
        
        # Weekly reset (Monday)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        if week_start > self._last_weekly_reset:
            self._weekly_loss = Decimal("0")
            self._last_weekly_reset = week_start
            logger.info("Weekly risk counters reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk status."""
        self._check_resets()
        
        return {
            "enabled": self._enabled,
            "daily_loss": float(self._daily_loss),
            "weekly_loss": float(self._weekly_loss),
            "consecutive_losses": self._consecutive_losses,
            "cooldown_active": self._cooldown_until is not None and datetime.utcnow() < self._cooldown_until,
            "cooldown_until": self._cooldown_until.isoformat() if self._cooldown_until else None,
            "orders_today": len(self._daily_orders),
            "orders_this_hour": len([t for t in self._hourly_orders if t > datetime.utcnow() - timedelta(hours=1)]),
            "total_exposure": sum(float(v) for v in self._exposure_by_game.values()),
            "total_contracts": sum(self._contracts_by_market.values()),
            "limits": self.get_all_limits()
        }
    
    def reset_all(self) -> None:
        """Reset all tracking (for testing)."""
        self._daily_loss = Decimal("0")
        self._weekly_loss = Decimal("0")
        self._hourly_orders = []
        self._daily_orders = []
        self._consecutive_losses = 0
        self._last_loss_time = None
        self._cooldown_until = None
        self._exposure_by_game = {}
        self._exposure_by_strategy = {}
        self._contracts_by_market = {}
        self._contracts_by_game = {}
        logger.info("Risk manager reset")


# =============================================================================
# Singleton Instance
# =============================================================================

_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """Get or create the global RiskManager instance."""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager
