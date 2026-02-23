import unittest
import os
from unittest.mock import patch
from decimal import Decimal

from app.services.budget_service import BudgetService


class TestBudgetService(unittest.TestCase):
    """
    Test suite for BudgetService in the Secure AI Studio application
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Enable testing mode to use smaller amounts
        os.environ['TESTING_MODE'] = 'true'
        self.budget_service = BudgetService()
        self.budget_service.reset_budget()  # Start fresh for each test

    def tearDown(self):
        """
        Clean up after each test method.
        """
        if 'TESTING_MODE' in os.environ:
            del os.environ['TESTING_MODE']

    def test_initial_budget_state(self):
        """
        Test that the budget service initializes with correct values
        """
        status = self.budget_service.get_budget_status()
        self.assertEqual(status['current_spending'], 0.0)
        self.assertEqual(status['total_budget'], 5.0)
        self.assertEqual(status['percentage_used'], 0.0)
        self.assertEqual(status['remaining_balance'], 5.0)
        self.assertFalse(status['alert_threshold_reached'])
        self.assertFalse(status['block_threshold_reached'])

    def test_can_proceed_with_generation_within_budget(self):
        """
        Test that generation can proceed when within budget limits
        """
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['reason'], 'WITHIN_BUDGET')
        self.assertEqual(result['current_spending'], 0.0)
        self.assertEqual(result['cost_of_request'], 0.01)  # Testing mode cost

    def test_alert_threshold_reached(self):
        """
        Test that alert threshold is triggered when appropriate
        """
        # In testing mode, alert threshold is still 92% of $5 = $4.60
        # But the individual generation costs are smaller (0.01 for wan model in testing mode)
        # So we need to get close to $4.60 to trigger the alert
        
        # Set spending to $4.595, then a generation costing $0.01 would bring us to $4.605
        # which exceeds the alert threshold of $4.60
        self.budget_service.set_current_spending_for_testing(4.595)  # This + 0.01 = 4.605 > 4.60
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['reason'], 'WITHIN_BUDGET_BUT_ALERT_THRESHOLD')
        
        # Now test with exactly at alert threshold
        self.budget_service.current_spending = Decimal('4.60')  # At alert threshold
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        self.assertTrue(result['allowed'])
        
        # Now test just over alert threshold
        self.budget_service.current_spending = Decimal('4.61')
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        self.assertTrue(result['allowed'])

    def test_block_threshold_exceeded(self):
        """
        Test that generation is blocked when it would exceed the block threshold
        """
        # Set spending close to block threshold (99% of $5 = $4.95)
        # In testing mode: block at 99% of $5 = $4.95, with 0.01 cost per gen
        self.budget_service.set_current_spending_for_testing(4.94)  # Need 0.01 more to hit block
        
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        # Should still be allowed since 4.94 + 0.01 = 4.95 which is equal to block amount, not greater
        self.assertTrue(result['allowed'])
        
        # Now test where it would exceed
        self.budget_service.set_current_spending_for_testing(4.945)  # Need 0.01 more to exceed
        result = self.budget_service.can_proceed_with_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'BUDGET_EXCEEDED')

    def test_record_generation_updates_spending(self):
        """
        Test that recording a generation updates the spending correctly
        """
        initial_status = self.budget_service.get_budget_status()
        initial_spending = initial_status['current_spending']
        
        result = self.budget_service.record_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        self.assertEqual(result['amount_added'], 0.01)  # Testing mode cost
        self.assertEqual(result['current_spending'], 0.01)  # New total spending
        
        final_status = self.budget_service.get_budget_status()
        self.assertEqual(final_status['current_spending'], 0.01)

    def test_calculate_expected_cost_by_model_type(self):
        """
        Test that cost calculation works correctly for different model types
        """
        # Test Wan model (default)
        cost = self.budget_service.calculate_expected_cost('wan-video/wan-2.2-t2v-fast', 'wan')
        self.assertEqual(float(cost), 0.01)
        
        # Test Veo model (premium)
        cost = self.budget_service.calculate_expected_cost('google/veo-3-fast', 'veo')
        self.assertEqual(float(cost), 0.05)
        
        # Test SDXL image model
        cost = self.budget_service.calculate_expected_cost('stability-ai/sdxl:...', 'sdxl')
        self.assertEqual(float(cost), 0.005)
        
        # Test Playground image model
        cost = self.budget_service.calculate_expected_cost('playgroundai/playground-v2.5-1024px-aesthetic:...', 'playground')
        self.assertEqual(float(cost), 0.0075)

    def test_budget_reset_functionality(self):
        """
        Test that budget can be reset to zero
        """
        # Record some spending
        self.budget_service.record_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        self.budget_service.record_generation('wan-video/wan-2.2-t2v-fast', 'wan')
        
        status = self.budget_service.get_budget_status()
        self.assertEqual(status['current_spending'], 0.02)
        
        # Reset the budget
        self.budget_service.reset_budget()
        
        status = self.budget_service.get_budget_status()
        self.assertEqual(status['current_spending'], 0.0)


class TestBudgetServiceRealAmounts(unittest.TestCase):
    """
    Test suite for BudgetService with real amounts (not testing mode)
    """

    def setUp(self):
        """
        Set up test fixtures before each test method using real amounts.
        """
        if 'TESTING_MODE' in os.environ:
            del os.environ['TESTING_MODE']
        self.budget_service = BudgetService()
        self.budget_service.reset_budget()  # Start fresh for each test

    def test_real_amounts_budget_thresholds(self):
        """
        Test that budget thresholds are correct with real amounts
        """
        status = self.budget_service.get_budget_status()
        
        # Real amounts: total budget $5.00, alert at $4.60 (92%), block at $4.95 (99%)
        self.assertEqual(status['total_budget'], 5.0)
        self.assertEqual(status['alert_amount'], 4.6)  # 92% of $5
        self.assertEqual(status['block_amount'], 4.95)  # 99% of $5
        
    def test_real_amounts_model_costs(self):
        """
        Test that model costs are correct with real amounts
        """
        # Wan Video model costs
        cost = self.budget_service.calculate_expected_cost('wan-video/wan-2.2-t2v-fast', 'wan')
        self.assertEqual(float(cost), 0.02)  # Real cost: $0.02
        
        # Google Veo model costs
        cost = self.budget_service.calculate_expected_cost('google/veo-3-fast', 'veo')
        self.assertEqual(float(cost), 0.10)  # Real cost: $0.10
        
        # Image model costs
        cost = self.budget_service.calculate_expected_cost('stability-ai/sdxl', 'sdxl')
        self.assertEqual(float(cost), 0.01)  # Real cost: $0.01


if __name__ == '__main__':
    unittest.main(verbosity=2)