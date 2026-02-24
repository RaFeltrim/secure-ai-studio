"""
Budget service to track and limit spending on AI model usage according to the $5 budget constraint.
Implements the 92% alert threshold and 99% blocking limit as specified.
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal


class BudgetService:
    """
    Service to manage and enforce the $5 budget limit for AI model usage.
    Tracks spending and enforces limits at 92% ($4.60) alert and 99% ($4.95) block thresholds.
    """
    
    def __init__(self):
        # Total budget limit in USD
        self.total_budget = Decimal('5.00')
        
        # Thresholds for alerts and blocks
        self.alert_threshold = Decimal('0.92')  # 92% of budget = $4.60
        self.block_threshold = Decimal('0.99')  # 99% of budget = $4.95
        
        # Calculate actual dollar amounts
        self.alert_amount = self.total_budget * self.alert_threshold  # $4.60
        self.block_amount = self.total_budget * self.block_threshold  # $4.95
        
        # Setup persistence
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.state_file = os.path.join(base_dir, 'data', 'budget_state.json')
        
        # Track current spending loaded from disk
        self.current_spending = self._load_state()
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Model cost mapping (per generation)
        self.model_costs = {
            # Wan Video (budget-friendly)
            'wan-video/wan-2.2-t2v-fast': Decimal('0.02'),  # $0.02 per generation
            'wan-video/wan-2.2-i2v-fast': Decimal('0.02'),  # $0.02 per generation
            
            # Google Veo (premium)
            'google/veo-3-fast': Decimal('0.10'),  # $0.10 per generation
            
            # Image models
            'stability-ai/sdxl': Decimal('0.01'),  # $0.01 per generation
            'playgroundai/playground-v2.5-1024px-aesthetic': Decimal('0.015'),  # $0.015 per generation
        }
        
        # For testing purposes, we can override costs
        if os.getenv('TESTING_MODE', '').lower() == 'true':
            # Use smaller amounts for testing to avoid hitting limits quickly
            self.model_costs = {
                'wan-video/wan-2.2-t2v-fast': Decimal('0.01'),
                'wan-video/wan-2.2-i2v-fast': Decimal('0.01'),
                'google/veo-3-fast': Decimal('0.05'),
                'stability-ai/sdxl': Decimal('0.005'),
                'playgroundai/playground-v2.5-1024px-aesthetic': Decimal('0.0075'),
            }

    def _load_state(self) -> Decimal:
        """Load budget state from disk."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return Decimal(str(data.get('current_spending', '0.00')))
        except Exception as e:
            print(f"Error loading budget state: {e}")
        return Decimal('0.00')

    def _save_state(self):
        """Save budget state to disk."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'current_spending': str(self.current_spending),
                    'last_updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"Error saving budget state: {e}")

    def get_cost_for_model(self, model_name: str) -> Decimal:
        """
        Get the cost for a specific model.
        """
        return self.model_costs.get(model_name, Decimal('0.05'))  # Default to $0.05 if unknown

    def calculate_expected_cost(self, model_name: str, model_type: str = 'wan') -> Decimal:
        """
        Calculate the expected cost based on model type selection.
        """
        # Map model_type to actual model names
        if model_type.lower() == 'veo':
            return self.model_costs.get('google/veo-3-fast', Decimal('0.10'))
        elif model_type.lower() == 'wan':
            if 'i2v' in model_name:
                return self.model_costs.get('wan-video/wan-2.2-i2v-fast', Decimal('0.02'))
            else:
                return self.model_costs.get('wan-video/wan-2.2-t2v-fast', Decimal('0.02'))
        elif model_type.lower() == 'playground':
            return self.model_costs.get('playgroundai/playground-v2.5-1024px-aesthetic', Decimal('0.015'))
        elif model_type.lower() == 'sdxl':
            return self.model_costs.get('stability-ai/sdxl', Decimal('0.01'))
        else:
            # Default to wan model cost if unknown type
            return self.model_costs.get('wan-video/wan-2.2-t2v-fast', Decimal('0.02'))

    def can_proceed_with_generation(self, model_name: str, model_type: str = 'wan') -> Dict[str, Any]:
        """
        Check if we can proceed with a generation based on current budget.
        Returns a dict with 'allowed' boolean and additional info.
        """
        with self._lock:
            expected_cost = self.calculate_expected_cost(model_name, model_type)
            # Convert current_spending to Decimal if it's not already
            current_as_decimal = Decimal(str(self.current_spending)) if not isinstance(self.current_spending, Decimal) else self.current_spending
            projected_spending = current_as_decimal + expected_cost
            
            # Check if this would exceed the block threshold
            if projected_spending > self.block_amount:
                return {
                    'allowed': False,
                    'reason': 'BUDGET_EXCEEDED',
                    'message': f'Budget limit would be exceeded. Current: ${current_as_decimal:.2f}, '
                              f'Projected after generation: ${projected_spending:.2f}, '
                              f'Max allowed: ${self.block_amount:.2f}',
                    'current_spending': float(current_as_decimal),
                    'projected_spending': float(projected_spending),
                    'block_threshold': float(self.block_amount),
                    'cost_of_request': float(expected_cost)
                }
            
            # Check if this would exceed the alert threshold
            if projected_spending > self.alert_amount:
                return {
                    'allowed': True,
                    'reason': 'WITHIN_BUDGET_BUT_ALERT_THRESHOLD',
                    'message': f'Proceeding with generation but budget alert threshold would be reached. '
                              f'Current: ${current_as_decimal:.2f}, '
                              f'After generation: ${projected_spending:.2f}. '
                              f'Alert threshold: ${self.alert_amount:.2f}',
                    'current_spending': float(current_as_decimal),
                    'projected_spending': float(projected_spending),
                    'alert_threshold': float(self.alert_amount),
                    'cost_of_request': float(expected_cost)
                }
            
            # Within budget limits
            return {
                'allowed': True,
                'reason': 'WITHIN_BUDGET',
                'message': f'Within budget. Current: ${current_as_decimal:.2f}, '
                          f'After generation: ${projected_spending:.2f}',
                'current_spending': float(current_as_decimal),
                'projected_spending': float(projected_spending),
                'cost_of_request': float(expected_cost)
            }

    def record_generation(self, model_name: str, model_type: str = 'wan') -> Dict[str, Any]:
        """
        Record a completed generation and update spending.
        """
        with self._lock:
            cost = self.calculate_expected_cost(model_name, model_type)
            # Convert to Decimal if current_spending is not already
            current_as_decimal = Decimal(str(self.current_spending)) if not isinstance(self.current_spending, Decimal) else self.current_spending
            self.current_spending = current_as_decimal + cost  # Store as Decimal
            self._save_state()
            
            # Check if we've crossed thresholds after recording
            if self.current_spending > self.block_amount:
                status = 'BUDGET_EXCEEDED_BLOCK'
                message = f'Budget has been exceeded. Current spending: ${self.current_spending:.2f}, ' \
                         f'Max allowed: ${self.block_amount:.2f}'
            elif self.current_spending > self.alert_amount:
                status = 'BUDGET_ALERT_THRESHOLD_REACHED'
                message = f'Budget alert threshold reached. Current spending: ${self.current_spending:.2f}, ' \
                         f'Alert threshold: ${self.alert_amount:.2f}'
            else:
                status = 'WITHIN_BUDGET'
                message = f'Generation recorded. Current spending: ${self.current_spending:.2f}'
            
            return {
                'status': status,
                'message': message,
                'current_spending': float(self.current_spending),
                'amount_added': float(cost),
                'budget_percentage': float((self.current_spending / self.total_budget) * 100)
            }

    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get the current budget status.
        """
        with self._lock:
            percentage_used = (self.current_spending / self.total_budget) * 100 if self.total_budget > 0 else 0
            
            return {
                'current_spending': float(self.current_spending),
                'total_budget': float(self.total_budget),
                'percentage_used': float(percentage_used),
                'remaining_balance': float(self.total_budget - self.current_spending),
                'alert_threshold_reached': self.current_spending > self.alert_amount,
                'block_threshold_reached': self.current_spending > self.block_amount,
                'alert_amount': float(self.alert_amount),
                'block_amount': float(self.block_amount)
            }

    def reset_budget(self):
        """
        Reset the budget tracking (for testing purposes).
        """
        with self._lock:
            self.current_spending = Decimal('0.00')
            self._save_state()

    def set_current_spending_for_testing(self, value):
        """
        Set current spending value directly for testing purposes, converting to Decimal if needed.
        """
        with self._lock:
            if not isinstance(value, Decimal):
                self.current_spending = Decimal(str(value))
            else:
                self.current_spending = value
            self._save_state()


# Global budget service instance
budget_service = BudgetService()