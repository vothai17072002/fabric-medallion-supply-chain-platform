/*
  Synthetic, fail-closed approval gate for a Gold candidate publication.

  Preconditions:
    - Candidate data has already been built outside the trusted publication.
    - Every active blocking contract is expected to emit exactly one terminal
      result for @RunId and @ExpectedBusinessDate.
    - PublishControl contains exactly one candidate row for that boundary.

  This procedure approves or rejects control state. It does not itself switch
  physical Gold tables/views or update a semantic model.
*/
CREATE OR ALTER PROCEDURE dbo.usp_gate_gold_publish
    @RunId uniqueidentifier,
    @ExpectedBusinessDate date
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @PublishRowCount int;
    DECLARE @CurrentStatus varchar(20);
    DECLARE @ExpectedContractCount int;
    DECLARE @InvalidContractDefinitionCount int;
    DECLARE @CoverageOrFailureCount int;
    DECLARE @GateFailureMessage varchar(1000);

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT
            @PublishRowCount = COUNT(*),
            @CurrentStatus = MAX(PublishStatus)
        FROM dbo.PublishControl WITH (UPDLOCK, HOLDLOCK)
        WHERE RunId = @RunId
          AND BusinessDate = @ExpectedBusinessDate;

        IF @PublishRowCount <> 1
        BEGIN
            SET @GateFailureMessage =
                'Gold candidate rejected: expected exactly one PublishControl row.';
        END;

        /* Repeating an already-approved call is an explicit idempotent no-op. */
        IF @GateFailureMessage IS NULL AND @CurrentStatus = 'Approved'
        BEGIN
            COMMIT TRANSACTION;
            RETURN;
        END;

        IF @GateFailureMessage IS NULL
           AND (@CurrentStatus IS NULL OR @CurrentStatus NOT IN ('Pending', 'Validated'))
        BEGIN
            SET @GateFailureMessage =
                'Gold candidate rejected: invalid publication state transition.';
        END;

        SELECT @ExpectedContractCount = COUNT(*)
        FROM dbo.DataQualityContract
        WHERE IsActive = 1
          AND IsBlocking = 1
          AND EffectiveFromBusinessDate <= @ExpectedBusinessDate
          AND (
                EffectiveToBusinessDate IS NULL
                OR EffectiveToBusinessDate >= @ExpectedBusinessDate
              );

        /* Zero expected tests is a configuration failure, never an automatic pass. */
        IF @GateFailureMessage IS NULL AND @ExpectedContractCount = 0
        BEGIN
            SET @GateFailureMessage =
                'Gold candidate rejected: no active blocking DQ contracts were configured.';
        END;

        /* Fail closed if configuration uniqueness is not physically enforced. */
        SELECT @InvalidContractDefinitionCount = COUNT(*)
        FROM
        (
            SELECT ContractId, ContractVersion
            FROM dbo.DataQualityContract
            WHERE IsActive = 1
              AND IsBlocking = 1
              AND EffectiveFromBusinessDate <= @ExpectedBusinessDate
              AND (
                    EffectiveToBusinessDate IS NULL
                    OR EffectiveToBusinessDate >= @ExpectedBusinessDate
                  )
            GROUP BY ContractId, ContractVersion
            HAVING COUNT(*) <> 1
                OR MIN(ExpectedResultCardinality) <= 0
        ) AS InvalidContract;

        IF @GateFailureMessage IS NULL AND @InvalidContractDefinitionCount > 0
        BEGIN
            SET @GateFailureMessage =
                'Gold candidate rejected: active DQ contract definition is duplicate or invalid.';
        END;

        IF @GateFailureMessage IS NULL
        BEGIN
            ;WITH Expected AS
            (
                SELECT
                    ContractId,
                    ContractVersion,
                    ExpectedResultCardinality
                FROM dbo.DataQualityContract
                WHERE IsActive = 1
                  AND IsBlocking = 1
                  AND EffectiveFromBusinessDate <= @ExpectedBusinessDate
                  AND (
                        EffectiveToBusinessDate IS NULL
                        OR EffectiveToBusinessDate >= @ExpectedBusinessDate
                      )
            ),
            Actual AS
            (
                SELECT
                    ContractId,
                    ContractVersion,
                    COUNT(*) AS ResultCount,
                    SUM(CASE WHEN TestStatus = 'Passed' THEN 1 ELSE 0 END) AS PassedCount,
                    SUM(
                        CASE
                            WHEN TestStatus IS NULL
                                 OR TestStatus NOT IN ('Passed', 'Failed')
                            THEN 1
                            ELSE 0
                        END
                    ) AS NullOrUnknownStatusCount
                FROM dbo.DataQualityResult
                WHERE RunId = @RunId
                  AND BusinessDate = @ExpectedBusinessDate
                GROUP BY ContractId, ContractVersion
            )
            SELECT @CoverageOrFailureCount = COUNT(*)
            FROM Expected AS e
            LEFT JOIN Actual AS a
              ON a.ContractId = e.ContractId
             AND a.ContractVersion = e.ContractVersion
            WHERE COALESCE(a.ResultCount, 0) <> e.ExpectedResultCardinality
               OR COALESCE(a.PassedCount, 0) <> e.ExpectedResultCardinality
               OR COALESCE(a.NullOrUnknownStatusCount, 0) > 0;

            IF @CoverageOrFailureCount > 0
            BEGIN
                SET @GateFailureMessage =
                    'Gold candidate rejected: blocking DQ result is missing, duplicate, null, unknown, or failed.';
            END;
        END;

        IF @GateFailureMessage IS NOT NULL
        BEGIN
            /* Persist the rejected state before surfacing a failing return path. */
            IF @PublishRowCount = 1
            BEGIN
                UPDATE dbo.PublishControl
                   SET PublishStatus = 'Rejected',
                       FailureReason = @GateFailureMessage,
                       RejectedAtUtc = SYSUTCDATETIME(),
                       ApprovedAtUtc = NULL,
                       LastStateChangedAtUtc = SYSUTCDATETIME()
                 WHERE RunId = @RunId
                   AND BusinessDate = @ExpectedBusinessDate;
            END;

            COMMIT TRANSACTION;
            THROW 51000, @GateFailureMessage, 1;
        END;

        UPDATE dbo.PublishControl
           SET PublishStatus = 'Approved',
               FailureReason = NULL,
               ApprovedAtUtc = SYSUTCDATETIME(),
               RejectedAtUtc = NULL,
               LastStateChangedAtUtc = SYSUTCDATETIME()
         WHERE RunId = @RunId
           AND BusinessDate = @ExpectedBusinessDate
           AND PublishStatus IN ('Pending', 'Validated');

        IF @@ROWCOUNT <> 1
        BEGIN
            THROW 51001, 'Gold candidate approval lost its expected state transition.', 1;
        END;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
        BEGIN
            ROLLBACK TRANSACTION;
        END;

        THROW;
    END CATCH;
END;
