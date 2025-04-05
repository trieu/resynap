# generate data for A/B testing CLV uplift by chatgpt
import random
import numpy as np

segments = ["wedding jewelry", "gifts", "daily wear"]

def simulate_jewellery_transactions(
    num_customers=100, 
    simulation_duration_months=12, 
    personalization_effectiveness=0.1
):
    """
    Simulates jewellery retail transactions for a number of customers over a given duration,
    incorporating segmentation and persona-based behavior.

    Args:
        num_customers (int): Number of customers to simulate.
        simulation_duration_months (int): Duration of the simulation in months.
        personalization_effectiveness (float): Factor influencing purchase probability and
                                              order value for targeted customers.
    
    Returns:
        dict: Dictionary containing transaction data, customer personas, and CLV calculations.
    """
    
    customer_data = {}
    
    for customer_id in range(num_customers):
        # Assign customer persona based on segmentation analysis
        persona = random.choice(segments)
        purchase_frequency_base = random.uniform(0.05, 0.3)  # Monthly purchase probability
        average_order_value_base = random.uniform(50, 500)  # Base order value

        is_personalized = random.random() < 0.4  # 40% of customers receive personalization

        customer_data[customer_id] = {
            'persona': persona,
            'is_personalized': is_personalized,
            'transactions': [],
            'total_spending': 0
        }

        for month in range(simulation_duration_months):
            purchase_probability = purchase_frequency_base * (1 + personalization_effectiveness if is_personalized else 1)

            if random.random() < purchase_probability:
                order_value = np.random.normal(average_order_value_base, average_order_value_base * 0.2)
                order_value *= (1 + personalization_effectiveness if is_personalized else 1)
                order_value = max(10, order_value)

                customer_data[customer_id]['transactions'].append({
                    'month': month + 1,
                    'amount': order_value
                })
                customer_data[customer_id]['total_spending'] += order_value

        customer_data[customer_id]['clv'] = customer_data[customer_id]['total_spending']

    return customer_data

# Run the simulation
simulation_results = simulate_jewellery_transactions(num_customers=150, simulation_duration_months=18)

# Analyze and print results
print("Simulated Jewellery Transaction Data and CLV (First 10 Customers):")
for i in range(min(10, len(simulation_results))):
    customer = simulation_results[i]
    print(f"Customer {i+1}:")
    print(f"  Persona Segment: {customer['persona']}")
    print(f"  Personalized: {customer['is_personalized']}")
    print(f"  Number of Transactions: {len(customer['transactions'])}")
    print(f"  Total Spending (CLV over simulation): £{customer['clv']:.2f}")
    print("-" * 20)

# Calculate CLV per persona segment
persona_clvs = {segment: [] for segment in segments}
for customer in simulation_results.values():
    persona_clvs[customer['persona']].append(customer['clv'])

print("\nAverage Customer Lifetime Value (CLV) by Persona Segment:")
for segment, clvs in persona_clvs.items():
    if clvs:
        print(f"  {segment}: £{sum(clvs) / len(clvs):.2f}")
    else:
        print(f"  {segment}: No data")

# CLV comparison for personalized vs. non-personalized
personalized_clvs = [c['clv'] for c in simulation_results.values() if c['is_personalized']]
non_personalized_clvs = [c['clv'] for c in simulation_results.values() if not c['is_personalized']]

print("\nAverage CLV for Personalized vs. Non-Personalized Customers:")
if personalized_clvs:
    print(f"  Personalized: £{sum(personalized_clvs) / len(personalized_clvs):.2f}")
if non_personalized_clvs:
    print(f"  Non-Personalized: £{sum(non_personalized_clvs) / len(non_personalized_clvs):.2f}")

if personalized_clvs and non_personalized_clvs:
    clv_uplift = (sum(personalized_clvs) / len(personalized_clvs)) / (sum(non_personalized_clvs) / len(non_personalized_clvs)) - 1
    print(f"\nCLV Uplift for Personalized Group: {clv_uplift*100:.2f}%")
