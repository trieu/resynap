# generate data for A/B testing CLV uplift by Gemini
# Paper: https://docs.google.com/document/d/1eEqCK7y9v2hVKuANLnkHJuUAl2uMuhXZBkS91aiIRRA/edit?usp=sharing

import random
import numpy as np
import pandas as pd

def simulate_jewellery_transactions_enhanced(
    num_customers=100,
    simulation_duration_months=12,
    personalization_effectiveness=0.1,
    churn_rate=0.02,
    discount_rate=0.1,
    acquisition_cost_range=(20, 50),
    customer_segments=None,
    customer_personas=None,
    persona_category_probabilities=None
):
    """
    Simulates jewellery retail transactions for a number of customers over a given duration,
    incorporating customer segmentation and personas.

    Args:
        num_customers (int): The number of customers to simulate.
        simulation_duration_months (int): The duration of the simulation in months.
        personalization_effectiveness (float): Uplift in purchase probability and AOV.
        churn_rate (float): Monthly churn rate.
        discount_rate (float): Annual discount rate for CLV calculation.
        acquisition_cost_range (tuple): Range for random customer acquisition costs.
        customer_segments (dict): Dictionary defining customer segments.
        customer_personas (dict): Dictionary defining customer personas.
        persona_category_probabilities (dict): Dictionary linking personas to purchase probabilities for categories.

    Returns:
        pandas.DataFrame: A DataFrame containing transaction data and CLV for each customer.
    """

    customer_data = []
    for customer_id in range(num_customers):
        # --- Assign Segment and Persona ---
        assigned_segment = random.choice(list(customer_segments.keys())) if customer_segments else "General"
        assigned_persona = random.choice(customer_segments[assigned_segment]) if customer_segments and assigned_segment in customer_segments and customer_segments[assigned_segment].__len__() > 0 else "General Customer"  # Corrected segment assignment and added a default persona

        # --- Customer Profile ---
        base_purchase_frequency = random.uniform(0.05, 0.3)
        base_average_order_value = random.uniform(50, 500)
        is_personalized = random.random() < 0.4
        acquisition_cost = random.uniform(acquisition_cost_range[0], acquisition_cost_range[1])  # Corrected indexing
        is_active = True
        months_active = 0
        total_spending = 0
        transactions = []

        customer = {
            "customer_id": customer_id,
            "assigned_segment": assigned_segment,
            "assigned_persona": assigned_persona,
            "is_personalized": is_personalized,
            "base_purchase_frequency": base_purchase_frequency,
            "base_average_order_value": base_average_order_value,
            "acquisition_cost": acquisition_cost,
            "is_active": is_active,
            "transactions": transactions,
            "total_spending": total_spending,
            "months_active": months_active,
        }

        for month in range(1, simulation_duration_months + 1):
            if not is_active:
                break

            purchase_probability = base_purchase_frequency
            average_order_value = base_average_order_value

            # --- Adjust Purchase Probability and AOV based on Persona ---
            if persona_category_probabilities and assigned_persona in persona_category_probabilities:
                category_probs = persona_category_probabilities[assigned_persona]
                # Determine which category the customer might purchase from this month
                possible_categories = list(category_probs.keys())
                purchase_category = random.choices(possible_categories, weights=list(category_probs.values()), k=1)[0] # Corrected: extract the category from the list

                # Adjust base probability based on persona's general purchase tendency
                if assigned_persona in customer_personas and "purchase_frequency_multiplier" in customer_personas[assigned_persona]: #check that the persona exists
                    purchase_probability *= customer_personas[assigned_persona]["purchase_frequency_multiplier"]

                # Adjust AOV based on persona's spending habits
                if assigned_persona in customer_personas and "average_order_value_multiplier" in customer_personas[assigned_persona]:  #check that the persona exists
                    average_order_value *= customer_personas[assigned_persona]["average_order_value_multiplier"]

                # Further adjust probability if the persona is likely to buy in this general category
                if category_probs[purchase_category] > 0:
                    purchase_probability *= 1 + (category_probs[purchase_category] * 0.5) # Increase probability if category match

                # Adjust AOV more specifically based on the assumed purchase category
                if purchase_category == "wedding":
                    average_order_value *= 2  # Wedding jewelry tends to be higher value
                elif purchase_category == "gift":
                    average_order_value *= 1.2 # Gifts might be slightly higher value

            if is_personalized:
                purchase_probability *= 1 + personalization_effectiveness
                average_order_value *= 1 + personalization_effectiveness

            purchase_probability = min(purchase_probability, 1)

            if random.random() < purchase_probability:
                order_value = np.random.normal(average_order_value, average_order_value * 0.2)
                order_value = max(10, order_value)

                transactions.append({"month": month, "amount": order_value, "category": purchase_category}) # simplified
                total_spending += order_value
                months_active += 1

            if random.random() < churn_rate:
                is_active = False

        monthly_discount_rate = (1 + discount_rate) ** (1/12) - 1
        clv = 0
        if months_active > 0:
            for i in range(months_active):
                clv += (total_spending / months_active) / ((1 + monthly_discount_rate) ** i)

        customer['clv'] = clv - acquisition_cost
        customer['total_spending'] = total_spending
        customer['months_active'] = months_active
        customer['transactions'] = transactions  # Corrected: Assign transactions to the customer
        customer_data.append(customer)

    return pd.DataFrame(customer_data)

# --- Define Customer Segments ---
customer_segments_data = {
    "Wedding Shoppers": ["The Romantic Bride", "The Groom"],
    "Gift Shoppers": ["The Thoughtful Gifter"],
    "Daily Wear Enthusiasts": ["The Fashion-Forward Individual", "The Classic Minimalist", "The Corporate Professional", "The Budget-Conscious Student"],
    "General": ["General Customer"]
}

# --- Define Customer Personas with some attributes ---
customer_personas_data = {
    "The Romantic Bride": {
        "age_range": (25, 35),
        "income_level": "Medium-High",
        "values":[],
        "interests":[],
        "purchase_frequency_multiplier": 0.6, # Tend to make fewer but higher value purchases
        "average_order_value_multiplier": 1.5
    },
    "The Groom": {
        "age_range": (27, 37),
        "income_level": "Medium-High",
        "values": ["Commitment", "Partnership", "Quality"],
        "interests":[],
        "purchase_frequency_multiplier": 0.4,
        "average_order_value_multiplier": 1.2
    },
    "The Thoughtful Gifter": {
        "age_range": (30, 45),
        "income_level": "Medium",
        "values":[],
        "interests":[],
        "purchase_frequency_multiplier": 1.2, # More frequent purchases around events
        "average_order_value_multiplier": 0.9
    },
    "The Occasional Buyer": {
        "age_range": (20, 55),
        "income_level": "Medium",
        "values": ["Practicality", "Value"],
        "interests":[],
        "purchase_frequency_multiplier": 0.5,
        "average_order_value_multiplier": 0.8
    },
    "The Fashion-Forward Individual": {
        "age_range": (18, 35),
        "income_level": "Medium",
        "values":[],
        "interests":[],
        "purchase_frequency_multiplier": 1.5, # More frequent purchases to stay trendy
        "average_order_value_multiplier": 0.7
    },
    "The Classic Minimalist": {
        "age_range": (25, 50),
        "income_level": "Medium-High",
        "values":[],
        "interests": ["Design", "Ethical Consumption"],
        "purchase_frequency_multiplier": 0.8,
        "average_order_value_multiplier": 1.1
    },
    "The Corporate Professional": {
        "age_range": (30, 55),
        "income_level": "High",
        "values": ["Elegance", "Professionalism", "Quality"],
        "interests": ["Career", "Culture"],
        "purchase_frequency_multiplier": 0.7,
        "average_order_value_multiplier": 1.3
    },
    "The Budget-Conscious Student": {
        "age_range": (18, 24),
        "income_level": "Low",
        "values":[],
        "interests":[],
        "purchase_frequency_multiplier": 1.3,
        "average_order_value_multiplier": 0.6
    },
    "General Customer": {
        "age_range": (20, 60),
        "income_level": "Medium",
        "values": ["Value", "Convenience"],
        "interests":[],
        "purchase_frequency_multiplier": 1.0,
        "average_order_value_multiplier": 1.0
    }
}

# --- Define Probabilities of Personas Purchasing from Different Categories ---
persona_category_probabilities_data = {
    "The Romantic Bride": {"wedding": 0.9, "gift": 0.1, "daily": 0.2},
    "The Groom": {"wedding": 0.8, "gift": 0.2, "daily": 0.1},
    "The Thoughtful Gifter": {"wedding": 0.3, "gift": 0.8, "daily": 0.4},
    "The Occasional Buyer": {"wedding": 0.1, "gift": 0.4, "daily": 0.6},
    "The Fashion-Forward Individual": {"wedding": 0.05, "gift": 0.3, "daily": 0.9},
    "The Classic Minimalist": {"wedding": 0.2, "gift": 0.2, "daily": 0.7},
    "The Corporate Professional": {"wedding": 0.1, "gift": 0.5, "daily": 0.8},
    "The Budget-Conscious Student": {"wedding": 0.01, "gift": 0.4, "daily": 0.85},
    "General Customer": {"wedding": 0.2, "gift": 0.3, "daily": 0.5}
}

# --- Run Enhanced Simulation ---
enhanced_simulation_results_df = simulate_jewellery_transactions_enhanced(
    num_customers=150,
    simulation_duration_months=18,
    churn_rate=0.03,
    customer_segments=customer_segments_data,
    customer_personas=customer_personas_data,
    persona_category_probabilities=persona_category_probabilities_data
)

# --- Analysis and Output (Using Pandas) ---

# 1. Basic Customer Information:
print("Enhanced Customer Data (First 10 Rows):\n", enhanced_simulation_results_df.head(10))

# 2. Descriptive Statistics:
print("\nEnhanced Descriptive Statistics:\n", enhanced_simulation_results_df.describe())

# 3. Transaction Details (Example for a Specific Customer):
customer_id_to_check = 5  # Example
customer_data_row = enhanced_simulation_results_df[enhanced_simulation_results_df["customer_id"] == customer_id_to_check]
if not customer_data_row.empty:
    transactions = customer_data_row["transactions"].iloc[0] # Corrected to access the first element (the list of transactions)
    if transactions:
        print(f"\nTransactions for Customer {customer_id_to_check} (Segment: {customer_data_row['assigned_segment'].iloc[0]}, Persona: {customer_data_row['assigned_persona'].iloc[0]}):\n") #corrected
        for transaction in transactions:
            print(f"  Month {transaction['month']}: £{transaction['amount']:.2f} (Category: {transaction['category']})")
    else:
        print(f"\nNo transactions found for Customer {customer_id_to_check}")
else:
    print(f"\nCustomer {customer_id_to_check} not found.")

# 4. CLV Analysis by Segment:
avg_clv_by_segment = enhanced_simulation_results_df.groupby("assigned_segment")["clv"].mean()
print("\nAverage CLV by Customer Segment:\n", avg_clv_by_segment)

# 5. CLV Analysis by Persona:
avg_clv_by_persona = enhanced_simulation_results_df.groupby("assigned_persona")["clv"].mean()
print("\nAverage CLV by Customer Persona:\n", avg_clv_by_persona)

# 6. Purchase Category Analysis:
all_transactions = [trans for sublist in enhanced_simulation_results_df['transactions'] for trans in sublist]
transactions_df = pd.DataFrame(all_transactions)
if not transactions_df.empty:
    category_counts = transactions_df['category'].value_counts()
    print("\nPurchase Category Distribution:\n", category_counts)

# 7. Active customers
active_customers_enhanced = enhanced_simulation_results_df[enhanced_simulation_results_df["is_active"] == True].shape[0] # Corrected: Use shape[0] to get the number of rows
print(f"\nNumber of Active Customers at Simulation End (Enhanced): {active_customers_enhanced}")

# 8. churned customers
churned_customers_enhanced = enhanced_simulation_results_df[enhanced_simulation_results_df["is_active"] == False].shape[0] # Corrected: Use shape[0] to get the number of rows
print(f"\nNumber of Churned Customers at Simulation End (Enhanced): {churned_customers_enhanced}")

# 9. Distribution of CLV
print("\nDistribution of CLV (Enhanced):")
print(enhanced_simulation_results_df['clv'].describe())

# 10. Check for Negative CLV
negative_clv_count_enhanced = (enhanced_simulation_results_df['clv'] < 0).sum()
print(f"\nNumber of Customers with Negative CLV (Enhanced): {negative_clv_count_enhanced}")

# 11. Average Acquisition Cost
print(f"\nAverage Acquisition Cost (Enhanced): £{enhanced_simulation_results_df['acquisition_cost'].mean():.2f}")