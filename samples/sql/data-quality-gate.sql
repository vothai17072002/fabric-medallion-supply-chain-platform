/*
  Synthetic example: fail a Gold publish when a Silver batch violates
  freshness, uniqueness, or reconciliation contracts.
*/
CREATE OR ALTER PROCEDURE dbo.usp_gate_gold_publish
    @RunId uniqueidentifier,
    @ExpectedBusinessDate date
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @FailureCount int = 0;

    SELECT @FailureCount = COUNT(*)
    FROM dbo.DataQualityResult
    WHERE RunId = @RunId
      AND BusinessDate = @ExpectedBusinessDate
      AND TestStatus <> 'Passed';

    IF @FailureCount > 0
    BEGIN
        THROW 51000, 'Gold publish blocked by data-quality gate.', 1;
    END;

    UPDATE dbo.PublishControl
       SET PublishStatus = 'Approved',
           ApprovedAtUtc = SYSUTCDATETIME()
     WHERE RunId = @RunId;
END;
