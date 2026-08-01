/*
  Synthetic control-plane schema for the portfolio DQ gate.

  The objects are intentionally generic and contain no production definitions.
  Validate data types, constraints, indexing, and transaction semantics against
  the target Fabric Warehouse SQL surface before adopting this pattern.
*/

CREATE TABLE dbo.DataQualityContract
(
    ContractId                 varchar(100)  NOT NULL,
    ContractVersion            int           NOT NULL,
    DomainName                 varchar(100)  NOT NULL,
    OwnerRole                  varchar(100)  NOT NULL,
    IsBlocking                 bit           NOT NULL,
    IsActive                   bit           NOT NULL,
    EffectiveFromBusinessDate  date          NOT NULL,
    EffectiveToBusinessDate    date          NULL,
    ExpectedResultCardinality  int           NOT NULL
);

CREATE TABLE dbo.DataQualityResult
(
    RunId              uniqueidentifier NOT NULL,
    BusinessDate       date             NOT NULL,
    ContractId         varchar(100)     NOT NULL,
    ContractVersion    int              NOT NULL,
    TestStatus         varchar(20)      NULL,
    ObservedValue      decimal(38, 10)  NULL,
    ThresholdValue     decimal(38, 10)  NULL,
    DiagnosticMessage varchar(1000)     NULL,
    EvaluatedAtUtc     datetime2(6)     NOT NULL
);

CREATE TABLE dbo.PublishControl
(
    RunId                uniqueidentifier NOT NULL,
    BusinessDate         date             NOT NULL,
    DomainName           varchar(100)     NOT NULL,
    CandidateVersion     varchar(100)     NOT NULL,
    PublishStatus        varchar(20)      NOT NULL,
    FailureReason        varchar(1000)    NULL,
    ApprovedAtUtc        datetime2(6)     NULL,
    RejectedAtUtc        datetime2(6)     NULL,
    LastStateChangedAtUtc datetime2(6)    NOT NULL
);

/*
  Production controls should additionally enforce uniqueness for:
    - DataQualityContract (ContractId, ContractVersion)
    - DataQualityResult (RunId, BusinessDate, ContractId, ContractVersion)
    - PublishControl (RunId, BusinessDate)

  The physical mechanism depends on the SQL feature set and deployment policy.
  The gate procedure below fails closed even when those constraints are absent.
*/
