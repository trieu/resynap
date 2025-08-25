```mermaid

sequenceDiagram
    participant AI RAG Agent 
    participant PostgreSQL
    participant Qdrant Vector Database
    participant AI Models
    participant Customer

    AI RAG Agent ->>PostgreSQL: Store customer data
    AI RAG Agent ->>AI RAG Agent : Customer Analytics
    AI RAG Agent ->>PostgreSQL: Update Insights
    PostgreSQL->>AI RAG Agent : Provide customer insights
    AI RAG Agent ->>Qdrant Vector Database: Sync data as embeddings
    Qdrant Vector Database->>AI RAG Agent : Enable similarity-based searches
    AI RAG Agent ->>AI Models: Train models for segmentation and personalization
    AI Models->>AI RAG Agent : Provide recommendations and clusters
    AI RAG Agent ->>Customer: Engage with personalized experiences
    Customer->>AI RAG Agent : Interact and provide feedback
    AI RAG Agent ->>AI Models: Update models with new data
    AI RAG Agent ->>PostgreSQL: Save updated customer insights

