# generate data for A/B testing CLV uplift by grok

import random
import numpy as np
from collections import defaultdict

def simulate_jewellery_transactions(num_customers=100, simulation_duration_months=12, discount_rate=0.0):
    """
    Simulates jewellery retail transactions for a number of customers over a given duration,
    incorporating customer segmentation and persona development.

    Args:
        num_customers (int): The number of customers to simulate.
        simulation_duration_months (int): The duration of the simulation in months.
        discount_rate (float): Monthly discount rate for CLV calculation. Default is 0.0 (no discounting).

    Returns:
        dict: A dictionary containing transaction data and calculated CLV for each customer.
    """
    # Define customer segments with their characteristics
    segments = [
        {'name': 'Luxury Shoppers', 'prob_min': 0.1, 'prob_max': 0.2, 'value_min': 500, 'value_max': 2000, 'personalization': 0.2, 'weight': 0.15},
        {'name': 'Bridal Couples', 'prob_min': 0.01, 'prob_max': 0.05, 'value_min': 1000, 'value_max': 5000, 'personalization': 0.1, 'weight': 0.10},
        {'name': 'Fashion-Forward Individuals', 'prob_min': 0.2, 'prob_max': 0.3, 'value_min': 100, 'value_max': 300, 'personalization': 0.3, 'weight': 0.15},
        {'name': 'Gift Givers', 'prob_min': 0.1, 'prob_max': 0.2, 'value_min': 200, 'value_max': 500, 'personalization': 0.15, 'weight': 0.20},
        {'name': 'Collectors', 'prob_min': 0.05, 'prob_max': 0.1, 'value_min': 1000, 'value_max': 5000, 'personalization': 0.25, 'weight': 0.05},
        {'name': 'Young Adults', 'prob_min': 0.15, 'prob_max': 0.25, 'value_min': 50, 'value_max': 150, 'personalization': 0.2, 'weight': 0.15},
        {'name': 'Corporate Professionals', 'prob_min': 0.1, 'prob_max': 0.15, 'value_min': 300, 'value_max': 600, 'personalization': 0.1, 'weight': 0.10},
        {'name': 'Eco-Conscious Shoppers', 'prob_min': 0.1, 'prob_max': 0.2, 'value_min': 100, 'value_max': 300, 'personalization': 0.25, 'weight': 0.05},
        {'name': 'Special Occasion Shoppers', 'prob_min': 0.05, 'prob_max': 0.1, 'value_min': 300, 'value_max': 1000, 'personalization': 0.15, 'weight': 0.05},
    ]

    customer_data = {}
    for customer_id in range(num_customers):
        # Select segment based on weights
        selected_segment = random.choices(segments, weights=[s['weight'] for s in segments])[0]
        
        # Define customer profiles based on segment
        base_purchase_probability = random.uniform(selected_segment['prob_min'], selected_segment['prob_max'])
        base_avg_order_value = random.uniform(selected_segment['value_min'], selected_segment['value_max'])
        
        # Simulate personalization
        is_personalized = random.random() < 0.4  # 40% chance
        
        customer_data[customer_id] = {
            'segment': selected_segment['name'],
            'is_personalized': is_personalized,
            'transactions': [],
            'clv': 0.0
        }
        
        for month in range(simulation_duration_months):
            # Determine purchase probability
            purchase_probability = base_purchase_probability
            if is_personalized:
                purchase_probability *= (1 + selected_segment['personalization'])
                purchase_probability = min(1.0, purchase_probability)
            
            if random.random() < purchase_probability:
                # Simulate order value
                order_value = np.random.normal(base_avg_order_value, base_avg_order_value * 0.2)
                if is_personalized:
                    order_value *= (1 + selected_segment['personalization'])
                order_value = max(10, order_value)  # Minimum order value
                
                # Apply discount factor for CLV
                discount_factor = 1 / (1 + discount_rate) ** month
                discounted_order_value = order_value * discount_factor
                
                # Record transaction (undiscounted amount)
                customer_data[customer_id]['transactions'].append({
                    'month': month + 1,
                    'amount': order_value
                })
                
                # Add discounted order value to CLV
                customer_data[customer_id]['clv'] += discounted_order_value
    
    return customer_data

# For reproducibility, you can set seeds:
# random.seed(42)
# np.random.seed(42)

# Run the simulation
simulation_results = simulate_jewellery_transactions(num_customers=150, simulation_duration_months=18, discount_rate=0.005)

# Print first 10 customers
print("Simulated Jewellery Transaction Data and CLV (First 10 Customers):")
for i in range(min(10, len(simulation_results))):
    customer = simulation_results[i]
    print(f"Customer {i+1}:")
    print(f"  Segment: {customer['segment']}")
    print(f"  Personalized: {customer['is_personalized']}")
    print(f"  Number of Transactions: {len(customer['transactions'])}")
    print(f"  Total Spending (CLV over simulation): £{customer['clv']:.2f}")
    print("-" * 20)

# Calculate average CLV by segment
clv_by_segment = defaultdict(lambda: {'personalized': [], 'non_personalized': []})
for customer in simulation_results.values():
    segment = customer['segment']
    is_personalized = customer['is_personalized']
    clv = customer['clv']
    if is_personalized:
        clv_by_segment[segment]['personalized'].append(clv)
    else:
        clv_by_segment[segment]['non_personalized'].append(clv)

print("\nAverage CLV by Segment:")
for segment, data in clv_by_segment.items():
    if data['personalized']:
        avg_personalized = sum(data['personalized']) / len(data['personalized'])
        print(f"  {segment} - Personalized: £{avg_personalized:.2f}")
    else:
        print(f"  {segment} - Personalized: No data")
    
    if data['non_personalized']:
        avg_non_personalized = sum(data['non_personalized']) / len(data['non_personalized'])
        print(f"  {segment} - Non-Personalized: £{avg_non_personalized:.2f}")
    else:
        print(f"  {segment} - Non-Personalized: No data")
    
    if data['personalized'] and data['non_personalized']:
        uplift = (avg_personalized / avg_non_personalized) - 1
        print(f"  CLV Uplift for {segment}: {uplift*100:.2f}%")
    print("-" * 20)

# Overall averages
personalized_clvs = [c['clv'] for c in simulation_results.values() if c['is_personalized']]
non_personalized_clvs = [c['clv'] for c in simulation_results.values() if not c['is_personalized']]

print("\nOverall Average Customer Lifetime Value (CLV):")
if personalized_clvs:
    print(f"  Average CLV (Personalized Group): £{sum(personalized_clvs) / len(personalized_clvs):.2f}")
else:
    print("  No customers in the Personalized Group.")

if non_personalized_clvs:
    print(f"  Average CLV (Non-Personalized Group): £{sum(non_personalized_clvs) / len(non_personalized_clvs):.2f}")
else:
    print("  No customers in the Non-Personalized Group.")

if personalized_clvs and non_personalized_clvs:
    overall_uplift = (sum(personalized_clvs) / len(personalized_clvs)) / (sum(non_personalized_clvs) / len(non_personalized_clvs)) - 1
    print(f"\nOverall CLV Uplift for Personalized Group: {overall_uplift*100:.2f}%")