```mermaid

flowchart TD
    Start([User Request]) --> LoadIdentity[/Load User ID and Session/]
    LoadIdentity -->|GET /tracking/v2/load-identity| API_Gateway_1[AWS API Gateway]
    API_Gateway_1 --> Lambda_Identity[Lambda: Load Identity Function]
    Lambda_Identity --> Response_Identity[Return sessionKey & visitorId]

    Start --> PushNormalEvent[/Track Normal Event/]
    PushNormalEvent -->|POST /tracking/v2/push-normal-event| API_Gateway_2[AWS API Gateway]
    API_Gateway_2 --> Lambda_NormalEvent[Lambda: Process Normal Event]
    Lambda_NormalEvent --> BatchProcessing[S3 or Batch Processing Service]
    BatchProcessing --> Response_NormalEvent[Return Status & Acknowledgment]

    Start --> PushKeyEvent[/Track Key Event/]
    PushKeyEvent -->|POST /tracking/v2/push-key-event| API_Gateway_3[AWS API Gateway]
    API_Gateway_3 --> Lambda_KeyEvent[Lambda: Process Key Event]
    Lambda_KeyEvent --> RealTimeProcessing[Real-Time Processing Service]
    RealTimeProcessing --> Response_KeyEvent[Return Status & Acknowledgment]

    Response_Identity --> End([End])
    Response_NormalEvent --> End
    Response_KeyEvent --> End

    %% Styling
    classDef lambda fill:#FFD700,stroke:#333,stroke-width:2;
    classDef gateway fill:#87CEFA,stroke:#333,stroke-width:2;
    classDef service fill:#90EE90,stroke:#333,stroke-width:2;

    class Lambda_Identity,Lambda_NormalEvent,Lambda_KeyEvent lambda;
    class API_Gateway_1,API_Gateway_2,API_Gateway_3 gateway;
    class BatchProcessing,RealTimeProcessing service;
