```mermaid

flowchart LR
    %% Client Side and Server Side
    ClientSide[Client Side<br> API, SDK] --> ExperienceEdge[Experience Edge Network]
    ServerSide[Server Side] --> ExperienceEdge

    %% Streaming Data Stores
    StreamingDataStores[Streaming Data Stores<br> API, Connectors] --> RealTimeProfile[Real-Time Customer Profile]
    StreamingDataStores --> DataIngestion[Data Ingestion]

    %% Enterprise Data Stores
    EnterpriseDataStores[Enterprise Data Stores<br> API, Connectors] --> DataIngestion
    EnterpriseDataStores --> DataLake[Data Lake]

    %% Real-Time Customer Profile
    RealTimeProfile --> Identity[Identity]
    RealTimeProfile --> Profile[Profile]
    RealTimeProfile --> Segments[Segments]

    %% Data Ingestion
    DataIngestion --> Batch[Batch]
    DataIngestion --> Stream[Stream]

    %% Data Lake
    DataLake --> Governance[Governance]
    DataLake --> QueryService[Query Service]

    %% Customer Journey Analytics
    RealTimeProfile -->|Audience Sync| Connections[Connections - sandbox]
    Connections --> IndividualProfiles[Individual Profile Datasets]
    Connections --> ExperienceEvent[Experience Event Datasets]
    Connections --> LookupDatasets[Lookup Datasets]

    Connections --> DataView1[Data View 1]
    Connections --> DataView2[Data View 2]
    Connections --> DataView3[Data View 3]
    Connections --> DataViewN[Data View N]

    DataView1 --> EmailProgram[Email Program Performance]
    DataView2 --> AttributionResearch[Attribution Research]
    DataView3 --> CallCenter[Call Center Analysis]
    DataViewN --> ProjectN[Project N]

    %% Reporting & Analysis
    EmailProgram --> Reporting[Reporting & Analysis]
    AttributionResearch --> Reporting
    CallCenter --> Reporting
    ProjectN --> Reporting

    %% Flow Definitions
    classDef dataFlow stroke-width:2px,stroke:#333
    classDef egressFlow stroke-width:2px,stroke:#FF0000
    classDef audienceFlow stroke-width:2px,stroke-dasharray:5,stroke:#FF0000
    classDef syncFlow stroke-width:2px,stroke-dasharray:5,stroke:#333

    %% Styling the flows
    ExperienceEdge -->|Streaming Data| RealTimeProfile:::dataFlow
    ExperienceEdge -->|Streaming Data| DataIngestion:::dataFlow
    DataIngestion --> DataLake:::dataFlow
    RealTimeProfile -->|Audience Sync| Connections:::audienceFlow
    Connections --> DataView1:::egressFlow
    Connections --> DataView2:::egressFlow
    Connections --> DataView3:::egressFlow
    Connections --> DataViewN:::egressFlow
    DataLake --> Connections:::syncFlow

    %% Grouping
    subgraph Adobe_Experience_Platform[Resynap Experience Platform]
        RealTimeProfile
        DataIngestion
        DataLake
    end

    subgraph Customer_Journey_Analytics[Customer Journey Analytics]
        Connections
        DataView1
        DataView2
        DataView3
        DataViewN
        EmailProgram
        AttributionResearch
        CallCenter
        ProjectN
    end
