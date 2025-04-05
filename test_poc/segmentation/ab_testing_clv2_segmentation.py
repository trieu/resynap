# generate data for A/B testing CLV uplift by Gemini

import random
import numpy as np
import pandas as pd

segments = ["wedding", "gifts", "daily_wear", "luxury"]  # Added a "luxury" segment
 
def simulate_jewellery_transactions_with_segments(
    num_customers=100,
    simulation_duration_months=12,
    personalization_effectiveness=0.1,
    churn_rate=0.02,
    discount_rate=0.1,
    acquisition_cost_range=(20, 50),
    segment_preferences_strength=0.7,  # Strength of customer preference for their primary segment
):
    """
    Simulates jewellery transactions with customer segmentation and persona-based targeting.

    Args:
        num_customers (int): Number of customers.
        simulation_duration_months (int): Simulation duration in months.
        personalization_effectiveness (float): Uplift from personalization.
        churn_rate (float): Monthly churn rate.
        discount_rate (float): Annual discount rate for CLV.
        acquisition_cost_range (tuple): Range for random acquisition costs.
        segment_preferences_strength (float): How strongly customers prefer their segment.

    Returns:
        pandas.DataFrame: Simulation results.
    """

   
    customer_data = []

    for customer_id in range(num_customers):
        # --- Customer Profile & Segmentation ---
        # Assign a primary segment preference
        primary_segment = random.choice(segments)
        # Create a dictionary for segment preferences (including all segments)
        segment_preferences = {seg: 0.1 for seg in segments}  # Base interest in all
        segment_preferences[primary_segment] = segment_preferences_strength # Stronger preference

        purchase_frequency_base = random.uniform(0.05, 0.3)
        # Base AOV, now influenced by primary segment (luxury has higher AOV)
        if primary_segment == "luxury":
            average_order_value_base = random.uniform(500, 1500)
        else:
            average_order_value_base = random.uniform(50, 500)

        is_personalized = random.random() < 0.4  # 40% get personalized offers
        acquisition_cost = random.uniform(acquisition_cost_range[0], acquisition_cost_range[1])
        is_active = True
        months_active = 0

        customer = {
            "customer_id": customer_id,
            "primary_segment": primary_segment,
            "segment_preferences": segment_preferences,  # Store all preferences
            "is_personalized": is_personalized,
            "purchase_frequency_base": purchase_frequency_base,
            "average_order_value_base": average_order_value_base,
            "acquisition_cost": acquisition_cost,
            "is_active": is_active,
            "transactions": [],
            "total_spending": 0,
            "months_active": 0,
        }

        for month in range(1, simulation_duration_months + 1):
            if not is_active:
                break

            # --- Purchase Probability (Segment-Specific) ---
            # Choose a segment for this month's potential purchase
            # Weighted random choice based on segment preferences
            chosen_segment = random.choices(
                list(segment_preferences.keys()),
                weights=list(segment_preferences.values()),
            )[0]

            purchase_probability = purchase_frequency_base * segment_preferences[chosen_segment]
            if is_personalized:
                # Personalization boosts probability *more* if it's the preferred segment
                if chosen_segment == primary_segment:
                  purchase_probability *= 1 + (personalization_effectiveness * 1.5) # extra boost
                else:
                  purchase_probability *= 1 + personalization_effectiveness


            purchase_probability = min(purchase_probability, 1)

            # --- Transaction Simulation ---
            if random.random() < purchase_probability:
                # AOV influenced by chosen segment
                if chosen_segment == "luxury":
                    order_value = np.random.normal(
                        average_order_value_base, average_order_value_base * 0.3
                    )  # Higher variance for luxury
                else:
                    order_value = np.random.normal(
                        average_order_value_base, average_order_value_base * 0.2
                    )

                if is_personalized:
                    order_value *= 1 + personalization_effectiveness
                order_value = max(10, order_value)

                customer["transactions"].append(
                    {
                        "month": month,
                        "segment": chosen_segment,  # Record the segment
                        "amount": order_value,
                    }
                )
                customer["total_spending"] += order_value
                customer["months_active"] += 1

            # --- Churn ---
            if random.random() < churn_rate:
                is_active = False

        # --- CLV Calculation ---
        monthly_discount_rate = (1 + discount_rate) ** (1 / 12) - 1
        clv = 0
        if customer["months_active"] > 0:
          for i in range(customer["months_active"]):
            clv += (customer["total_spending"] / customer["months_active"]) / (
                (1 + monthly_discount_rate) ** i
            )
        customer["clv"] = clv - customer["acquisition_cost"]

        customer_data.append(customer)

    return pd.DataFrame(customer_data)



# --- Run Simulation ---
simulation_results_df = simulate_jewellery_transactions_with_segments(
    num_customers=500,  # Increased customer number
    simulation_duration_months=18,
    churn_rate=0.02,
    segment_preferences_strength=0.6,  # Adjusted preference strength
)

# --- Analysis and Output ---

print("Customer Data (First 10 Rows):\n", simulation_results_df.head(10))
print("\nDescriptive Statistics:\n", simulation_results_df.describe())

# 1. Segment Distribution:
print("\nSegment Distribution:\n", simulation_results_df["primary_segment"].value_counts())

# 2. Average CLV per Segment:
print("\nAverage CLV per Segment:\n", simulation_results_df.groupby("primary_segment")["clv"].mean())

# 3.  Transactions by Segment (for a specific customer):
customer_id_to_check = 10
transactions = simulation_results_df.loc[
    simulation_results_df["customer_id"] == customer_id_to_check, "transactions"
].iloc[0]

if transactions:
    print(f"\nTransactions for Customer {customer_id_to_check}:")
    for transaction in transactions:
        print(
            f"  Month {transaction['month']}, Segment: {transaction['segment']}, Amount: £{transaction['amount']:.2f}"
        )
else:
    print(f"\nNo transactions found for Customer {customer_id_to_check}")



# 4. CLV Uplift (Personalized vs. Non-Personalized, overall)
avg_clv_personalized = simulation_results_df[simulation_results_df["is_personalized"] == True]["clv"].mean()
avg_clv_non_personalized = simulation_results_df[simulation_results_df["is_personalized"] == False]["clv"].mean()

print("\nOverall CLV Comparison:")
print(f"  Average CLV (Personalized): £{avg_clv_personalized:.2f}")
print(f"  Average CLV (Non-Personalized): £{avg_clv_non_personalized:.2f}")

if not np.isnan(avg_clv_personalized) and not np.isnan(avg_clv_non_personalized) and avg_clv_non_personalized !=0:
  clv_uplift = (avg_clv_personalized / avg_clv_non_personalized - 1) * 100
  print(f"  Overall CLV Uplift (Personalized): {clv_uplift:.2f}%")
else:
    print("Cannot calculate overall CLV Uplift.")

#5. CLV Uplift by Segment:
print("\nCLV Uplift by Segment:")
for segment in segments:
  personalized_segment = simulation_results_df[
      (simulation_results_df["is_personalized"] == True) & (simulation_results_df["primary_segment"] == segment)]
  non_personalized_segment = simulation_results_df[
      (simulation_results_df["is_personalized"] == False) & (simulation_results_df["primary_segment"] == segment)]

  avg_clv_personalized_segment = personalized_segment["clv"].mean()
  avg_clv_non_personalized_segment = non_personalized_segment["clv"].mean()

  if not np.isnan(avg_clv_personalized_segment) and not np.isnan(avg_clv_non_personalized_segment) and avg_clv_non_personalized_segment != 0:
      clv_uplift_segment = (avg_clv_personalized_segment / avg_clv_non_personalized_segment - 1) * 100
      print(f"  {segment}: {clv_uplift_segment:.2f}%")
  else:
      print(f"  {segment}: Cannot calculate (division by zero or NaN).")

#6. Number of Active/Churned by segment
print("\nActive/Churned Customers per Segment:")
print(simulation_results_df.groupby(["primary_segment", "is_active"]).size().unstack(fill_value=0))

#7.  Segment Preferences (Example for a specific customer):
customer_id_pref = 2
preferences = simulation_results_df.loc[
    simulation_results_df["customer_id"] == customer_id_pref, "segment_preferences"
].iloc[0]
print(f"\nSegment Preferences for Customer {customer_id_pref}:\n", preferences)

#8. Total Spending Per segment:
print("\nTotal spending per segment:")
# Initialize a dictionary to hold total spending per segment
total_spending_per_segment = {segment: 0 for segment in segments}

# Iterate through each customer
for _, customer in simulation_results_df.iterrows():
    # Iterate through each transaction for the customer
    for transaction in customer['transactions']:
        segment = transaction['segment']
        amount = transaction['amount']
        total_spending_per_segment[segment] += amount

# Print total spending per segment
for segment, total_spending in total_spending_per_segment.items():
    print(f"Total spending in {segment}: £{total_spending:.2f}")

#9. Average order value per segment
print("\nAverage Order Value per segment:")
# Initialize dictionaries to hold total spending and transaction count per segment
total_spending_per_segment = {segment: 0 for segment in segments}
transaction_count_per_segment = {segment: 0 for segment in segments}

for _, customer in simulation_results_df.iterrows():
    for transaction in customer['transactions']:
        segment = transaction['segment']
        amount = transaction['amount']
        total_spending_per_segment[segment] += amount
        transaction_count_per_segment[segment] += 1

# Calculate and print Average Order Value per segment
for segment in segments:
    if transaction_count_per_segment[segment] > 0:
        average_order_value = total_spending_per_segment[segment] / transaction_count_per_segment[segment]
        print(f"Average Order Value in {segment}: £{average_order_value:.2f}")
    else:
        print(f"No transactions in {segment}")