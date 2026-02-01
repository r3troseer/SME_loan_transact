"""
Credit System Module
Manages per-transaction credits for the GFA Exchange platform.
"""

from datetime import datetime
from typing import List, Dict, Optional


class CreditManager:
    """
    Manages credit balance and transactions for platform monetization.

    GFA Exchange uses a credit-based model where users spend credits to:
    - View detailed swap recommendations (1 credit)
    - Generate LLM explanations (2 credits)
    - Express transaction interest (5 credits)
    - De-anonymize counterparty details (10 credits)
    """

    # Credit costs for different actions
    COSTS = {
        # Loan Sale/Buy actions
        'view_details': 1,
        'generate_explanation': 2,
        'express_interest': 5,
        'submit_bid': 3,
        'view_bids': 3,
        'reveal_counterparty': 5,
        # Loan Swap actions
        'view_swap_details': 1,
        'accept_swap': 3,
        'browse_unlisted_loans': 2,
        'propose_swap': 5,
        'view_swap_proposal': 1,
        'generate_swap_story': 2,
    }

    # Action descriptions for display
    ACTION_LABELS = {
        # Loan Sale/Buy actions
        'view_details': 'View Recommendation Details',
        'generate_explanation': 'Generate AI Explanation',
        'express_interest': 'Express Transaction Interest',
        'submit_bid': 'Submit Bid on Loan',
        'view_bids': 'View Incoming Bids',
        'reveal_counterparty': 'Reveal Counterparty Identity',
        # Loan Swap actions
        'view_swap_details': 'View Swap Details',
        'accept_swap': 'Accept Swap Proposal',
        'browse_unlisted_loans': 'Browse Unlisted Loans',
        'propose_swap': 'Propose Loan Swap',
        'view_swap_proposal': 'View Incoming Swap Proposal',
        'generate_swap_story': 'Generate Swap Inclusion Story',
    }

    def __init__(self, initial_credits: int = 100):
        """
        Initialize credit manager with starting balance.

        Args:
            initial_credits: Starting credit balance (default 100 for demo)
        """
        self.credits = initial_credits
        self.initial_credits = initial_credits
        self.transaction_log: List[Dict] = []

    def check_balance(self) -> int:
        """Get current credit balance."""
        return self.credits

    def can_afford(self, action: str) -> bool:
        """
        Check if user can afford an action.

        Args:
            action: Action key from COSTS

        Returns:
            True if sufficient credits available
        """
        cost = self.COSTS.get(action, 0)
        return self.credits >= cost

    def get_cost(self, action: str) -> int:
        """Get the cost for a specific action."""
        return self.COSTS.get(action, 0)

    def spend(self, action: str, item_id: Optional[str] = None) -> bool:
        """
        Spend credits on an action.

        Args:
            action: Action key from COSTS
            item_id: Optional identifier for the item (e.g., SME_ID)

        Returns:
            True if transaction successful, False if insufficient credits
        """
        cost = self.COSTS.get(action, 0)

        if self.credits >= cost:
            self.credits -= cost
            self.transaction_log.append({
                'action': action,
                'action_label': self.ACTION_LABELS.get(action, action),
                'amount': cost,
                'item_id': item_id,
                'timestamp': datetime.now(),
                'balance_after': self.credits
            })
            return True
        return False

    def get_history(self) -> List[Dict]:
        """Get transaction history."""
        return self.transaction_log

    def get_spent_total(self) -> int:
        """Get total credits spent."""
        return self.initial_credits - self.credits

    def get_action_count(self, action: str) -> int:
        """Get count of times an action was performed."""
        return sum(1 for t in self.transaction_log if t['action'] == action)

    def has_viewed_item(self, action: str, item_id: str) -> bool:
        """
        Check if a specific item has already been paid for.

        Args:
            action: Action type
            item_id: Item identifier

        Returns:
            True if already paid, so no need to charge again
        """
        for t in self.transaction_log:
            if t['action'] == action and t['item_id'] == item_id:
                return True
        return False

    def add_credits(self, amount: int, reason: str = "purchase") -> None:
        """
        Add credits to balance (for demo/purchase simulation).

        Args:
            amount: Credits to add
            reason: Reason for credit addition
        """
        self.credits += amount
        self.transaction_log.append({
            'action': 'credit_added',
            'action_label': f'Credits Added ({reason})',
            'amount': amount,
            'item_id': None,
            'timestamp': datetime.now(),
            'balance_after': self.credits
        })

    def reset(self) -> None:
        """Reset to initial state (for demo purposes)."""
        self.credits = self.initial_credits
        self.transaction_log = []

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        return {
            'current_balance': self.credits,
            'initial_balance': self.initial_credits,
            'total_spent': self.get_spent_total(),
            'total_transactions': len([t for t in self.transaction_log if t['action'] != 'credit_added']),
            'details_viewed': self.get_action_count('view_details'),
            'explanations_generated': self.get_action_count('generate_explanation'),
            'interests_expressed': self.get_action_count('express_interest'),
            'counterparties_revealed': self.get_action_count('reveal_counterparty')
        }


# Credit tier pricing (for display purposes)
CREDIT_PACKAGES = [
    {'credits': 50, 'price': '£25', 'per_credit': '£0.50'},
    {'credits': 100, 'price': '£40', 'per_credit': '£0.40', 'popular': True},
    {'credits': 250, 'price': '£75', 'per_credit': '£0.30'},
    {'credits': 500, 'price': '£125', 'per_credit': '£0.25', 'best_value': True},
]


if __name__ == "__main__":
    # Test the credit manager
    print("Testing Credit Manager...")

    cm = CreditManager(initial_credits=100)

    print(f"Initial balance: {cm.check_balance()}")

    # Test spending
    print("\n--- Test spending ---")
    print(f"Can afford view_details? {cm.can_afford('view_details')}")

    success = cm.spend('view_details', 'SME_0001')
    print(f"Spent 1 credit on view_details: {success}")
    print(f"Balance: {cm.check_balance()}")

    success = cm.spend('generate_explanation', 'SME_0001')
    print(f"Spent 2 credits on generate_explanation: {success}")
    print(f"Balance: {cm.check_balance()}")

    # Check if already viewed
    print(f"\nAlready viewed SME_0001? {cm.has_viewed_item('view_details', 'SME_0001')}")
    print(f"Already viewed SME_0002? {cm.has_viewed_item('view_details', 'SME_0002')}")

    # Summary
    print("\n--- Summary ---")
    summary = cm.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    # History
    print("\n--- Transaction History ---")
    for t in cm.get_history():
        print(f"{t['timestamp'].strftime('%H:%M:%S')} | {t['action_label']} | -{t['amount']} | Balance: {t['balance_after']}")
