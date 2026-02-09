#!/usr/bin/env python3
"""
Policy-Driven AI Guardrail Engine
Evaluates AI outputs against configurable policies and determines safe actions.
"""

import json
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    """Possible actions in order of restrictiveness (most to least)"""
    BLOCK = 4
    ESCALATE = 3
    SANITIZE = 2
    ALLOW = 1


@dataclass
class Policy:
    """Represents a guardrail policy"""
    id: str
    risk: str
    allowed_actions: List[str]
    min_confidence: float

    @classmethod
    def from_dict(cls, data: Dict) -> 'Policy':
        return cls(
            id=data['id'],
            risk=data['risk'],
            allowed_actions=data['allowed_actions'],
            min_confidence=data['min_confidence']
        )


@dataclass
class Input:
    """Represents an AI-generated output to evaluate"""
    id: str
    risk: str
    output: str
    confidence: float

    @classmethod
    def from_dict(cls, data: Dict) -> 'Input':
        return cls(
            id=data['id'],
            risk=data['risk'],
            output=data['output'],
            confidence=data['confidence']
        )


class GuardrailEngine:
    """Core engine for policy-driven guardrail decisions"""
    
    SANITIZED_RESPONSE = "This response cannot be shown. Please consult a qualified professional."
    ESCALATED_RESPONSE = "Sent for human review"
    BLOCKED_RESPONSE = "Output blocked by policy"
    
    def __init__(self, policies: List[Policy], default_action: str = "block"):
        self.policies = policies
        self.default_action = default_action.lower()
    
    def find_matching_policies(self, input_item: Input) -> List[Policy]:
        """Find all policies that apply to the given input's risk type"""
        return [p for p in self.policies if p.risk == input_item.risk]
    
    def evaluate_policy(self, policy: Policy, input_item: Input) -> Optional[str]:
        """
        Evaluate a single policy against an input.
        Returns the most restrictive action if confidence threshold is met,
        otherwise returns a more restrictive action.
        """
        # Check if confidence meets threshold
        if input_item.confidence >= policy.min_confidence:
            # Confidence met - return least restrictive allowed action
            return self._get_least_restrictive_action(policy.allowed_actions)
        else:
            # Confidence not met - return most restrictive allowed action
            # or escalate if available, otherwise block
            if 'block' in policy.allowed_actions:
                return 'block'
            elif 'escalate' in policy.allowed_actions:
                return 'escalate'
            elif 'sanitize' in policy.allowed_actions:
                return 'sanitize'
            else:
                return 'block'  # Safety fallback
    
    def _get_least_restrictive_action(self, allowed_actions: List[str]) -> str:
        """Get the least restrictive action from allowed actions"""
        action_priority = ['allow', 'sanitize', 'escalate', 'block']
        for action in action_priority:
            if action in allowed_actions:
                return action
        return 'block'
    
    def _get_most_restrictive_action(self, actions: List[str]) -> str:
        """Get the most restrictive action from a list"""
        action_priority = ['block', 'escalate', 'sanitize', 'allow']
        for action in action_priority:
            if action in actions:
                return action
        return 'block'
    
    def make_decision(self, input_item: Input) -> Dict[str, Any]:
        """
        Make a guardrail decision for the given input.
        Returns a decision dictionary with action, policies, output, and reason.
        """
        matching_policies = self.find_matching_policies(input_item)
        
        # No matching policies - use default action
        if not matching_policies:
            return self._make_default_decision(input_item)
        
        # Evaluate all matching policies
        policy_actions = {}
        for policy in matching_policies:
            action = self.evaluate_policy(policy, input_item)
            policy_actions[policy.id] = action
        
        # Choose most restrictive action
        final_action = self._get_most_restrictive_action(list(policy_actions.values()))
        applied_policies = [pid for pid, action in policy_actions.items() 
                          if action == final_action]
        
        # Generate output and reason
        final_output, reason = self._generate_output_and_reason(
            input_item, final_action, matching_policies, applied_policies
        )
        
        return {
            'id': input_item.id,
            'decision': final_action,
            'applied_policies': applied_policies,
            'final_output': final_output,
            'reason': reason
        }
    
    def _make_default_decision(self, input_item: Input) -> Dict[str, Any]:
        """Make decision when no policies match"""
        final_output = self.BLOCKED_RESPONSE if self.default_action == 'block' else input_item.output
        
        return {
            'id': input_item.id,
            'decision': self.default_action,
            'applied_policies': [],
            'final_output': final_output,
            'reason': f"No policies found for risk type '{input_item.risk}'; applied default action"
        }
    
    def _generate_output_and_reason(
        self, 
        input_item: Input, 
        action: str,
        matching_policies: List[Policy],
        applied_policies: List[str]
    ) -> tuple:
        """Generate final output text and decision reason"""
        
        # Determine output text
        if action == 'allow':
            final_output = input_item.output
        elif action == 'sanitize':
            final_output = self.SANITIZED_RESPONSE
        elif action == 'escalate':
            final_output = self.ESCALATED_RESPONSE
        else:  # block
            final_output = self.BLOCKED_RESPONSE
        
        # Generate reason
        reasons = []
        reasons.append(f"{input_item.risk} risk")
        
        # Check confidence thresholds
        confidence_issues = []
        for policy in matching_policies:
            if policy.id in applied_policies:
                if input_item.confidence < policy.min_confidence:
                    confidence_issues.append(
                        f"confidence {input_item.confidence} < required {policy.min_confidence} ({policy.id})"
                    )
        
        if confidence_issues:
            reasons.extend(confidence_issues)
        else:
            reasons.append(f"confidence {input_item.confidence}")
        
        # Mention action taken
        if action == 'escalate':
            reasons.append("requires human review")
        elif action == 'sanitize':
            reasons.append("output sanitized for safety")
        elif action == 'block':
            reasons.append("output blocked")
        
        reason = "; ".join(reasons)
        
        return final_output, reason


def load_json_file(filepath: str) -> Any:
    """Load and parse a JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}': {e}")
        sys.exit(1)


def main():
    """Main execution function"""
    
    # Load input files
    print("Loading policies...")
    policies_data = load_json_file('policies.json')
    policies = [Policy.from_dict(p) for p in policies_data['policies']]
    default_action = policies_data.get('default_action', 'block')
    
    print("Loading inputs...")
    inputs_data = load_json_file('inputs.json')
    inputs = [Input.from_dict(i) for i in inputs_data]
    
    # Initialize engine
    print("Initializing guardrail engine...")
    engine = GuardrailEngine(policies, default_action)
    
    # Process all inputs
    print(f"Processing {len(inputs)} inputs...")
    results = []
    for input_item in inputs:
        decision = engine.make_decision(input_item)
        results.append(decision)
        print(f"  {input_item.id}: {decision['decision']}")
    
    # Write output
    print("Writing output.json...")
    with open('output.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Complete! Processed {len(results)} decisions")
    print("Output saved to output.json")


if __name__ == '__main__':
    main()