``` mermaid
graph TD
    subgraph Nguồn dữ liệu - Data Sources
        A[Website] --> C(Data Ingestion)
        B[Ứng dụng di động] --> C
        D[CRM] --> C
        E[POS - Point of Sale] --> C
        F[Game Marketing] --> C
        G[Loyalty Program] --> C
        H[Social Media] --> C
    end

    C --> I[Data Standardization & Cleansing]

    I --> J{Deterministic Matching}

    J -- Khớp --> K[Unified Customer Profile]
    J -- Không khớp --> L{Probabilistic Matching}

    L -- Khớp --> K
    L -- Không khớp --> M[Potential Duplicate Profiles]

    M --> N[Manual Review & Merge]

    N --> K

    K --> O[Segmented Customer Profiles]

    O --> P[Marketing Automation & Personalization]

    P --> Q[Kết quả: Tăng doanh số, cải thiện trải nghiệm khách hàng]