"""
P&L (Profit & Loss) Calculator.

Calculates unrealized and realized P&L for positions and portfolios.
Handles Kalshi's binary contract payout structure.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import logging

from backend.models.order import ExecutionPosition, OrderSide

logger = logging.getLogger(__name__)


class PnLCalculator:
    """
    Calculate P&L for positions and portfolios.
    
    Kalshi contracts are binary:
    - YES pays 100¢ if true, 0¢ if false
    - NO pays 100¢ if false, 0¢ if true
    """
    
    @staticmethod
    def calculate_unrealized_pnl(
        position: ExecutionPosition,
        current_price: Decimal
    ) -> Decimal:
        """
        Calculate unrealized P&L for a position.
        
        Args:
            position: The position to calculate P&L for
            current_price: Current market price (mid price, 0-100 cents)
        
        Returns:
            Unrealized P&L in cents
        """
        if position.quantity <= 0:
            return Decimal("0")
        
        # Current value of position
        current_value = current_price * position.quantity
        
        # Cost basis
        cost_basis = position.total_cost
        
        # Unrealized P&L
        unrealized = current_value - cost_basis
        
        return unrealized
    
    @staticmethod
    def calculate_realized_pnl(
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: int,
        side: OrderSide
    ) -> Decimal:
        """
        Calculate realized P&L when closing a position.
        
        Args:
            entry_price: Average entry price (cents)
            exit_price: Exit/close price (cents)
            quantity: Number of contracts closed
            side: Position side (YES or NO)
        
        Returns:
            Realized P&L in cents
        """
        if side == OrderSide.YES:
            # Bought YES: profit if price went up
            pnl = (exit_price - entry_price) * quantity
        else:
            # Bought NO: profit if YES price went down (NO price went up)
            # NO price = 100 - YES price
            pnl = (entry_price - exit_price) * quantity
        
        return pnl
    
    @staticmethod
    def calculate_settlement_pnl(
        position: ExecutionPosition,
        outcome: bool  # True = YES won, False = NO won
    ) -> Decimal:
        """
        Calculate P&L at contract settlement.
        
        Args:
            position: The position being settled
            outcome: True if YES outcome, False if NO outcome
        
        Returns:
            Settlement P&L in cents
        """
        if position.quantity <= 0:
            return Decimal("0")
        
        settlement_price = Decimal("100") if outcome else Decimal("0")
        
        if position.side == OrderSide.YES:
            # YES position: worth 100¢ if outcome is YES, 0¢ if NO
            final_value = settlement_price * position.quantity
        else:
            # NO position: worth 100¢ if outcome is NO, 0¢ if YES
            final_value = (Decimal("100") - settlement_price) * position.quantity
        
        pnl = final_value - position.total_cost
        
        return pnl
    
    @staticmethod
    def calculate_position_value(
        position: ExecutionPosition,
        current_price: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate full position valuation.
        
        Returns dict with:
        - current_value: Current market value
        - cost_basis: Total cost paid
        - unrealized_pnl: Paper profit/loss
        - unrealized_pnl_percent: P&L as percentage of cost
        """
        if position.quantity <= 0:
            return {
                "current_value": Decimal("0"),
                "cost_basis": Decimal("0"),
                "unrealized_pnl": Decimal("0"),
                "unrealized_pnl_percent": Decimal("0")
            }
        
        current_value = current_price * position.quantity
        cost_basis = position.total_cost
        unrealized_pnl = current_value - cost_basis
        
        if cost_basis > 0:
            unrealized_pnl_percent = (unrealized_pnl / cost_basis) * 100
        else:
            unrealized_pnl_percent = Decimal("0")
        
        return {
            "current_value": current_value,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent
        }


class PortfolioPnL:
    """Calculate portfolio-level P&L across all positions."""
    
    @staticmethod
    def calculate_total_unrealized(
        positions: List[ExecutionPosition],
        current_prices: Dict[str, Decimal]  # ticker -> price
    ) -> Dict[str, Any]:
        """
        Calculate total unrealized P&L across all positions.
        
        Args:
            positions: List of open positions
            current_prices: Dict mapping ticker to current price
        
        Returns:
            Portfolio summary dict
        """
        total_value = Decimal("0")
        total_cost = Decimal("0")
        total_unrealized = Decimal("0")
        position_details = []
        
        calc = PnLCalculator()
        
        for position in positions:
            if position.quantity <= 0:
                continue
            
            current_price = current_prices.get(position.market_ticker)
            if current_price is None:
                continue
            
            valuation = calc.calculate_position_value(position, current_price)
            
            total_value += valuation["current_value"]
            total_cost += valuation["cost_basis"]
            total_unrealized += valuation["unrealized_pnl"]
            
            position_details.append({
                "ticker": position.market_ticker,
                "side": position.side.value,
                "quantity": position.quantity,
                "avg_entry": float(position.avg_entry_price),
                "current_price": float(current_price),
                "unrealized_pnl": float(valuation["unrealized_pnl"]),
                "unrealized_pnl_percent": float(valuation["unrealized_pnl_percent"])
            })
        
        total_pnl_percent = (total_unrealized / total_cost * 100) if total_cost > 0 else Decimal("0")
        
        return {
            "total_value": float(total_value),
            "total_cost": float(total_cost),
            "total_unrealized_pnl": float(total_unrealized),
            "total_unrealized_pnl_percent": float(total_pnl_percent),
            "position_count": len(position_details),
            "positions": position_details
        }


class StrategyPerformance:
    """Calculate performance metrics for a strategy."""
    
    @staticmethod
    def calculate_from_orders(orders: List[dict]) -> Dict[str, Any]:
        """
        Calculate strategy performance from order history.
        
        Args:
            orders: List of order dicts from database
        
        Returns:
            Performance metrics dict
        """
        if not orders:
            return {
                "total_orders": 0,
                "filled_orders": 0,
                "rejected_orders": 0,
                "fill_rate": 0,
                "total_quantity": 0,
                "total_cost": 0,
                "avg_fill_price": 0,
                "unique_markets": 0,
                "first_order": None,
                "last_order": None,
                "win_rate": 0,
                "total_realized_pnl": 0
            }
        
        filled_orders = [o for o in orders if o.get("status") == "filled"]
        rejected_orders = [o for o in orders if o.get("status") in ("rejected", "cancelled")]
        
        total_quantity = sum(o.get("quantity", 0) for o in filled_orders)
        total_cost = sum(
            (o.get("filled_price", 0) or 0) * (o.get("quantity", 0) or 0) 
            for o in filled_orders
        )
        
        avg_fill_price = total_cost / total_quantity if total_quantity > 0 else 0
        
        # Get timestamps
        timestamps = [o.get("created_at") or o.get("placed_at") for o in orders if o.get("created_at") or o.get("placed_at")]
        
        return {
            "total_orders": len(orders),
            "filled_orders": len(filled_orders),
            "rejected_orders": len(rejected_orders),
            "fill_rate": len(filled_orders) / len(orders) * 100 if orders else 0,
            "total_quantity": total_quantity,
            "total_cost": total_cost,
            "avg_fill_price": avg_fill_price,
            "unique_markets": len(set(o.get("market_ticker") for o in filled_orders)),
            "first_order": min(timestamps) if timestamps else None,
            "last_order": max(timestamps) if timestamps else None
        }
    
    @staticmethod
    def calculate_win_rate(
        settled_positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate win rate from settled positions.
        
        Args:
            settled_positions: List of position dicts with realized_pnl
        
        Returns:
            Win rate metrics
        """
        if not settled_positions:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "total_realized_pnl": 0
            }
        
        winners = [p for p in settled_positions if p.get("realized_pnl", 0) > 0]
        losers = [p for p in settled_positions if p.get("realized_pnl", 0) < 0]
        
        total_wins = sum(p.get("realized_pnl", 0) for p in winners)
        total_losses = abs(sum(p.get("realized_pnl", 0) for p in losers))
        
        avg_win = total_wins / len(winners) if winners else 0
        avg_loss = total_losses / len(losers) if losers else 0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0
        
        return {
            "total_trades": len(settled_positions),
            "winning_trades": len(winners),
            "losing_trades": len(losers),
            "win_rate": len(winners) / len(settled_positions) * 100 if settled_positions else 0,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor if profit_factor != float('inf') else 999999,
            "total_realized_pnl": sum(p.get("realized_pnl", 0) for p in settled_positions)
        }
