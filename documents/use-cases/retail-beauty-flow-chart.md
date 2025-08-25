## Sephora Recommendation System Activity Diagrams

Here are activity diagrams for five Sephora recommendation use cases, focusing on the system logic behind the recommendations:

**1. Chosen For You (Personalized Recommendations)**

```mermaid
graph LR
A[User Logs In/Browses] --> B{User Profile Exists?};
B -- Yes --> C[Retrieve User Profile - CDP];
B -- No --> D[Create Temporary User Profile - Based on Session Data];
C --> E[Analyze User Data - Purchase History, Browsing History, Ratings, Preferences, Saved Items, Quizzes, etc.];
D --> E;
E --> F[Apply Collaborative Filtering & Content-Based Filtering];
F --> G[Generate Personalized Product Recommendations];
G --> H[Display Chosen For You Recommendations];
H --> I[User Interacts - Click, Add to Cart, Purchase];
I --> J[Capture Interaction Data & Update User Profile];
J --> E;
```

**2. New Arrivals (Category/Brand Specific)**

```mermaid
graph LR
A[User Browses Category/Brand Page] --> B[Retrieve New Arrivals for that Category/Brand];
B --> C[Filter by Stock Availability];
C --> D[Sort by Arrival Date - Newest First];
D --> E[Display New Arrivals Products];
```

**3. Beauty Offers (Best Offers in Specific Category)**

```mermaid
graph LR
A[User Browses Category Page] --> B[Retrieve All Products in Category];
B --> C[Filter by Products with Active Offers/Discounts];
C --> D[Sort by Discount Percentage - Highest First / Offer Value];
D --> E[Display Beauty Offers in Category];
```

**4. Trending Gifts (Occasion/Recipient Based)**

```mermaid
graph LR
A[User Enters Gift Section] --> B{Occasion/Recipient Specified?};
B -- Yes --> C[Retrieve Products Tagged for Occasion/Recipient];
B -- No --> D[Retrieve Globally Trending Gift Products];
C --> E[Filter by Stock Availability and Price Range - If specified];
D --> E;
E --> F[Sort by Popularity/Trending Score];
F --> G[Display Trending Gifts Recommendations];
```

**5. Beauty Insider Rewards (Personalized Rewards & Offers)**

```mermaid
graph LR
A[User Logs In/Identified as Beauty Insider] --> B[Retrieve User's Beauty Insider Tier & Points Balance];
B --> C[Retrieve Eligible Rewards & Offers based on Tier & Points];
C --> D{Personalized Offers Available?};
D -- Yes --> E[Retrieve Personalized Offers based on User Profile - Past Purchases, Preferences, etc.];
D -- No --> F[Retrieve Generic Offers for Tier];
E --> G[Combine Rewards & Personalized Offers];
F --> G;
G --> H[Display Beauty Insider Rewards & Offers];
```


**Key Explanations & Considerations:**

* **CDP (Customer Data Platform):** A central hub storing user profiles and enabling personalized experiences.
* **Collaborative Filtering:** Recommending products based on what similar users have liked or purchased.
* **Content-Based Filtering:** Recommending products based on a user's past interactions and preferences.
* **Trending Score:** A metric calculated based on recent sales, reviews, social media buzz, etc., to identify trending products.
* **Stock Availability:**  Filtering ensures only available products are recommended.
* **Real-time Updates:** User profiles and recommendations are ideally updated in real-time as users interact with the platform.
* **A/B Testing:** Continuous A/B testing helps optimize recommendation algorithms and improve performance.



These activity diagrams provide a high-level overview of the recommendation logic.  Sephora's actual implementation would be significantly more complex, incorporating factors like inventory management, pricing, promotions, and various business rules. However, these diagrams serve as a strong foundation for understanding the key components and flow of information within Sephora's recommendation system.
