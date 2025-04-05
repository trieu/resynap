# generate data for A/B testing CLV uplift by grok

import random
import numpy as np
from typing import Dict, List, Union

class JewelleryTransactionSimulator:
    """Simulates jewellery retail transactions and calculates customer lifetime value."""
    
    def __init__(self, 
                 num_customers: int = 100,
                 simulation_duration_months: int = 12,
                 personalization_effectiveness: float = 0.1):
        """
        Initialize the simulator with simulation parameters.
        
        Args:
            num_customers: Number of customers to simulate
            simulation_duration_months: Duration of simulation in months
            personalization_effectiveness: Value between 0-1 for personalization impact
        """
        self.num_customers = num_customers
        self.duration = simulation_duration_months
        self.personalization_effect = personalization_effectiveness
        self.customer_data = {}

    def _create_customer_profile(self) -> tuple[float, float, bool]:
        """Generate base customer characteristics."""
        purchase_freq = random.uniform(0.05, 0.3)  # Monthly purchase probability
        avg_order_value = random.uniform(50, 500)  # Base order value
        is_personalized = random.random() < 0.4    # 40% receive personalization
        return purchase_freq, avg_order_value, is_personalized

    def _simulate_customer_transactions(self, customer_id: int) -> None:
        """Simulate transactions for a single customer."""
        freq_base, value_base, personalized = self._create_customer_profile()
        
        self.customer_data[customer_id] = {
            'is_personalized': personalized,
            'transactions': [],
            'total_spending': 0.0
        }

        for month in range(self.duration):
            purchase_prob = freq_base * (1 + self.personalization_effect if personalized else 1)
            
            if random.random() < purchase_prob:
                order_value = np.random.normal(value_base, value_base * 0.2)
                if personalized:
                    order_value *= (1 + self.personalization_effect)
                order_value = max(10, order_value)

                self.customer_data[customer_id]['transactions'].append({
                    'month': month + 1,
                    'amount': float(order_value)
                })
                self.customer_data[customer_id]['total_spending'] += order_value

        self.customer_data[customer_id]['clv'] = self.customer_data[customer_id]['total_spending']

    def run_simulation(self) -> Dict[int, dict]:
        """Execute the full simulation for all customers."""
        self.customer_data.clear()
        for customer_id in range(self.num_customers):
            self._simulate_customer_transactions(customer_id)
        return self.customer_data

    def analyze_results(self) -> Dict[str, Union[float, List[float]]]:
        """Calculate key metrics from simulation results."""
        personalized_clvs = [c['clv'] for c in self.customer_data.values() if c['is_personalized']]
        non_personalized_clvs = [c['clv'] for c in self.customer_data.values() if not c['is_personalized']]
        
        metrics = {
            'personalized_clvs': personalized_clvs,
            'non_personalized_clvs': non_personalized_clvs,
            'avg_personalized_clv': sum(personalized_clvs) / len(personalized_clvs) if personalized_clvs else 0,
            'avg_non_personalized_clv': sum(non_personalized_clvs) / len(non_personalized_clvs) if non_personalized_clvs else 0
        }
        
        if personalized_clvs and non_personalized_clvs:
            metrics['clv_uplift'] = (metrics['avg_personalized_clv'] / metrics['avg_non_personalized_clv']) - 1
        else:
            metrics['clv_uplift'] = 0
            
        return metrics

def print_simulation_summary(simulation_results: Dict[int, dict], metrics: Dict[str, Union[float, List[float]]]) -> None:
    """Print formatted summary of simulation results."""
    print("\n=== Simulated Jewellery Transaction Summary ===")
    print(f"First {min(10, len(simulation_results))} Customers:")
    
    for i in range(min(10, len(simulation_results))):
        customer = simulation_results[i]
        print(f"\nCustomer {i+1}:")
        print(f"  Personalized: {customer['is_personalized']}")
        print(f"  Transactions: {len(customer['transactions'])}")
        print(f"  CLV: £{customer['clv']:.2f}")

    print("\nAverage Customer Lifetime Value:")
    print(f"  Personalized Group: £{metrics['avg_personalized_clv']:.2f}")
    print(f"  Non-Personalized Group: £{metrics['avg_non_personalized_clv']:.2f}")
    print(f"  CLV Uplift: {metrics['clv_uplift']*100:.2f}%")


# Example usage
if __name__ == "__main__":
    simulator = JewelleryTransactionSimulator(
        num_customers=150,
        simulation_duration_months=18,
        personalization_effectiveness=0.1
    )
    
    results = simulator.run_simulation()
    metrics = simulator.analyze_results()
    print_simulation_summary(results, metrics)