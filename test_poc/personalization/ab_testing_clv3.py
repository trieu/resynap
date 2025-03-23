# generate data for A/B testing CLV uplift by chatgpt

import random
import numpy as np

def simulate_jewellery_transactions(num_customers=100, simulation_months=12, personalization_effectiveness=0.1):
    """
    Simulates jewellery retail transactions for customers over a given period.
    
    Args:
        num_customers (int): Number of customers to simulate.
        simulation_months (int): Duration of the simulation in months.
        personalization_effectiveness (float): Uplift in purchase probability and order value due to personalization.
    
    Returns:
        dict: Customer transaction data and calculated CLV.
    """
    customer_data = {}
    
    for customer_id in range(num_customers):
        purchase_frequency = random.uniform(0.05, 0.3)  # Monthly purchase probability
        avg_order_value = random.uniform(50, 500)  # Base order value
        is_personalized = random.random() < 0.4  # 40% of customers receive personalization
        
        transactions = []
        total_spending = 0
        
        for month in range(1, simulation_months + 1):
            purchase_prob = purchase_frequency * (1 + personalization_effectiveness if is_personalized else 1)
            
            if random.random() < purchase_prob:
                order_value = np.random.normal(avg_order_value, avg_order_value * 0.2)
                order_value *= (1 + personalization_effectiveness) if is_personalized else 1
                order_value = max(10, round(order_value, 2))  # Ensure minimum order value
                
                transactions.append({"month": month, "amount": order_value})
                total_spending += order_value
        
        customer_data[customer_id] = {
            "is_personalized": is_personalized,
            "transactions": transactions,
            "total_spending": round(total_spending, 2),
            "clv": round(total_spending, 2)  # Simplified CLV as total spending
        }
    
    return customer_data

# Run simulation
simulation_results = simulate_jewellery_transactions(num_customers=150, simulation_months=18)

# Print results for first 10 customers
print("Simulated Jewellery Transactions and CLV (First 10 Customers):")
for i, customer in list(simulation_results.items())[:10]:
    print(f"Customer {i+1}:")
    print(f"  Personalized: {'Yes' if customer['is_personalized'] else 'No'}")
    print(f"  Transactions: {len(customer['transactions'])}")
    print(f"  Total Spending (CLV): £{customer['clv']:.2f}")
    print("-" * 30)

# CLV analysis for personalized vs. non-personalized groups
personalized_clvs = [c['clv'] for c in simulation_results.values() if c['is_personalized']]
non_personalized_clvs = [c['clv'] for c in simulation_results.values() if not c['is_personalized']]

def calculate_average_clv(clv_list):
    return sum(clv_list) / len(clv_list) if clv_list else 0

avg_clv_personalized = calculate_average_clv(personalized_clvs)
avg_clv_non_personalized = calculate_average_clv(non_personalized_clvs)

print("\nAverage Customer Lifetime Value (CLV):")
print(f"  Personalized Group: £{avg_clv_personalized:.2f}")
print(f"  Non-Personalized Group: £{avg_clv_non_personalized:.2f}")

if avg_clv_non_personalized > 0:
    clv_uplift = (avg_clv_personalized / avg_clv_non_personalized - 1) * 100
    print(f"  CLV Uplift for Personalized Group: {clv_uplift:.2f}%")
