#!/usr/bin/env python3
"""Unit tests for guardrail engine"""

import unittest
import json
from guardrail_engine import GuardrailEngine, Policy, Input


class TestGuardrailEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.policies = [
            Policy('P1', 'medical', ['escalate'], 0.95),
            Policy('P2', 'financial', ['sanitize', 'escalate'], 0.85),
            Policy('P3', 'general', ['allow'], 0.7),
        ]
        self.engine = GuardrailEngine(self.policies, 'block')
    
    def test_high_confidence_medical(self):
        """Test medical input with high confidence"""
        input_item = Input('R1', 'medical', 'Take medicine', 0.96)
        decision = self.engine.make_decision(input_item)
        self.assertEqual(decision['decision'], 'escalate')
    
    def test_low_confidence_medical(self):
        """Test medical input with low confidence"""
        input_item = Input('R2', 'medical', 'Take medicine', 0.80)
        decision = self.engine.make_decision(input_item)
        self.assertEqual(decision['decision'], 'escalate')  # Still escalate due to medical risk
    
    def test_high_confidence_financial(self):
        """Test financial input with high confidence"""
        input_item = Input('R3', 'financial', 'Refund approved', 0.90)
        decision = self.engine.make_decision(input_item)
        self.assertIn(decision['decision'], ['sanitize', 'escalate'])
    
    def test_general_allow(self):
        """Test general input that should be allowed"""
        input_item = Input('R4', 'general', 'Reset password', 0.92)
        decision = self.engine.make_decision(input_item)
        self.assertEqual(decision['decision'], 'allow')
    
    def test_no_matching_policy(self):
        """Test input with no matching policy"""
        input_item = Input('R5', 'unknown', 'Something', 0.99)
        decision = self.engine.make_decision(input_item)
        self.assertEqual(decision['decision'], 'block')
    
    def test_multi_policy_matching(self):
        """Test that multiple policies can match"""
        policies = [
            Policy('P1', 'medical', ['block'], 0.0),
            Policy('P2', 'medical', ['escalate'], 0.95),
        ]
        engine = GuardrailEngine(policies, 'block')
        input_item = Input('R1', 'medical', 'Take medicine', 0.96)
        decision = engine.make_decision(input_item)
        # Should choose most restrictive (block > escalate)
        self.assertEqual(decision['decision'], 'block')


if __name__ == '__main__':
    unittest.main()