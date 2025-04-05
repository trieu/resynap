# generate data for A/B testing CLV uplift by Gemini

import random
import numpy as np
import pandas as pd  # Using pandas for better data handling and analysis


def simulate_jewellery_transactions(
    num_customers=100,
    simulation_duration_months=12,
    personalization_effectiveness=0.1,
    churn_rate=0.02,  # Added customer churn
    discount_rate=0.1, # Added discount rate for CLV calculation
    acquisition_cost_range=(20, 50), # Range for random acquisition costs
):
    """
    Simulates jewellery retail transactions for a number of customers over a given duration.

    Args:
        num_customers (int): The number of customers to simulate.
        simulation_duration_months (int): The duration of the simulation in months.
        personalization_effectiveness (float): Uplift in purchase probability and AOV.
        churn_rate (float): Monthly churn rate.
        discount_rate (float): Annual discount rate for CLV calculation.
        acquisition_cost_range (tuple): Range for random customer acquisition costs.

    Returns:
        pandas.DataFrame: A DataFrame containing transaction data and CLV for each customer.
    """

    customer_data = []
    for customer_id in range(num_customers):
        # --- Customer Profile ---
        purchase_frequency_base = random.uniform(0.05, 0.3)
        average_order_value_base = random.uniform(50, 500)
        is_personalized = random.random() < 0.4
        acquisition_cost = random.uniform(acquisition_cost_range[0], acquisition_cost_range[1])
        is_active = True  # Customer starts as active
        months_active = 0 # Counter for CLV

        customer = {
            "customer_id": customer_id,
            "is_personalized": is_personalized,
            "purchase_frequency_base": purchase_frequency_base,
            "average_order_value_base": average_order_value_base,
            "acquisition_cost": acquisition_cost,
            "is_active": is_active,
            "transactions": [],
            "total_spending": 0,
            "months_active" : 0,
        }


        for month in range(1, simulation_duration_months + 1):
            if not is_active:
                break  # Skip if customer has churned

            # --- Purchase Probability ---
            purchase_probability = purchase_frequency_base
            if is_personalized:
                purchase_probability *= 1 + personalization_effectiveness
            purchase_probability = min(purchase_probability, 1)  # Cap at 1

            # --- Transaction Simulation ---
            if random.random() < purchase_probability:
                order_value = np.random.normal(
                    average_order_value_base, average_order_value_base * 0.2
                )
                if is_personalized:
                    order_value *= 1 + personalization_effectiveness
                order_value = max(10, order_value)

                customer["transactions"].append(
                    {"month": month, "amount": order_value}
                )
                customer["total_spending"] += order_value
                customer["months_active"] += 1

            # --- Churn Simulation ---
            if random.random() < churn_rate:
                is_active = False  # Customer churns

        # --- CLV Calculation (Improved) ---
        monthly_discount_rate = (1 + discount_rate) ** (1/12) - 1
        clv = 0
        if customer["months_active"] > 0:  # Avoid division by zero
            for i in range(customer["months_active"]):
              clv += (customer['total_spending']/customer['months_active']) / ((1 + monthly_discount_rate) ** i)

        customer['clv'] = clv - customer['acquisition_cost'] #subtract acquisition cost



        customer_data.append(customer)

    return pd.DataFrame(customer_data)


# --- Run Simulation ---
simulation_results_df = simulate_jewellery_transactions(
    num_customers=150, simulation_duration_months=18, churn_rate=0.03
)

# --- Analysis and Output (Using Pandas) ---

# 1. Basic Customer Information:
print("Customer Data (First 10 Rows):\n", simulation_results_df.head(10))

# 2. Descriptive Statistics:
print("\nDescriptive Statistics:\n", simulation_results_df.describe())


# 3. Transaction Details (Example for a Specific Customer):
customer_id_to_check = 5  # Example
transactions = simulation_results_df.loc[
    simulation_results_df["customer_id"] == customer_id_to_check, "transactions"
].iloc[0]
if transactions:  # Check if the list is not empty
    print(f"\nTransactions for Customer {customer_id_to_check}:\n")
    for transaction in transactions:
        print(f"  Month {transaction['month']}: £{transaction['amount']:.2f}")
else:
    print(f"\nNo transactions found for Customer {customer_id_to_check}")

# 4. CLV Analysis (Personalized vs. Non-Personalized):
avg_clv_personalized = simulation_results_df[
    simulation_results_df["is_personalized"] == True
]["clv"].mean()
avg_clv_non_personalized = simulation_results_df[
    simulation_results_df["is_personalized"] == False
]["clv"].mean()

print("\nAverage CLV Comparison:")
print(f"  Average CLV (Personalized): £{avg_clv_personalized:.2f}")
print(f"  Average CLV (Non-Personalized): £{avg_clv_non_personalized:.2f}")

if not np.isnan(avg_clv_personalized) and not np.isnan(avg_clv_non_personalized) and avg_clv_non_personalized != 0:
     clv_uplift = (avg_clv_personalized / avg_clv_non_personalized - 1) * 100
     print(f"  CLV Uplift (Personalized): {clv_uplift:.2f}%")
else:
    print("  Cannot calculate CLV uplift (division by zero or NaN).")

#5. Active customers
active_customers = simulation_results_df[simulation_results_df["is_active"] == True].shape[0]
print(f"\nNumber of Active Customers at Simulation End: {active_customers}")

#6. churned customers
churned_customers = simulation_results_df[simulation_results_df["is_active"] == False].shape[0]
print(f"\nNumber of Churned Customers at Simulation End: {churned_customers}")

#7.  Distribution of CLV
print("\nDistribution of CLV:")
print(simulation_results_df['clv'].describe())

# 8. Check for Negative CLV
negative_clv_count = (simulation_results_df['clv'] < 0).sum()
print(f"\nNumber of Customers with Negative CLV: {negative_clv_count}")


# 9.  Average Acquisition Cost
print(f"\nAverage Acquisition Cost: £{simulation_results_df['acquisition_cost'].mean():.2f}")