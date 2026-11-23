param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,
    [Parameter(Mandatory = $true)]
    [string]$ReleaseId,
    [Parameter(Mandatory = $true)]
    [string]$StaticEvidencePath,
    [string]$EvidencePath = "roadmap/02.5-production-readiness/sprint-3/evidence/PR3.1-live-stage.json",
    [string]$Namespace = "spaceops-stage",
    [string]$Release = "spaceops",
    [int]$MaxDlqRows = 0
)

$ErrorActionPreference = "Stop"
$startedAt = [DateTime]::UtcNow.ToString("o")

function Get-Sha256 {
    param([string]$Value)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })
    }
    finally {
        $sha.Dispose()
    }
}

function Invoke-NativeCapture {
    param(
        [string]$Id,
        [string]$Command,
        [string[]]$Arguments,
        [switch]$HashOnly
    )
    $started = [DateTime]::UtcNow.ToString("o")
    $output = (& $Command @Arguments 2>&1 | Out-String).Trim()
    $exitCode = $LASTEXITCODE
    return [ordered]@{
        id = $Id
        status = if ($exitCode -eq 0) { "pass" } else { "fail" }
        returncode = $exitCode
        started_at = $started
        finished_at = [DateTime]::UtcNow.ToString("o")
        output_sha256 = Get-Sha256 $output
        output_tail = if ($HashOnly) {
            "[redacted; SHA-256 only]"
        }
        elseif ($output.Length -le 2000) {
            $output
        }
        else {
            $output.Substring($output.Length - 2000)
        }
    }
}

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body
    )
    $params = @{
        Method = $Method
        Uri = $Url
        TimeoutSec = 240
        UseBasicParsing = $true
    }
    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = $Body | ConvertTo-Json -Depth 8 -Compress
    }
    return Invoke-RestMethod @params
}

if (-not (Test-Path $StaticEvidencePath)) {
    throw "Static evidence not found: $StaticEvidencePath"
}
$staticEvidence = Get-Content $StaticEvidencePath -Raw | ConvertFrom-Json
if ($staticEvidence.result -ne "pass") {
    throw "Static release gate did not pass"
}
if ($staticEvidence.release_id -ne $ReleaseId) {
    throw "Static evidence release_id does not match requested release"
}

$steps = New-Object Collections.Generic.List[object]
$healthStarted = [DateTime]::UtcNow.ToString("o")
$health = Invoke-JsonRequest -Method "GET" -Url "$($ApiUrl.TrimEnd('/'))/health"
$steps.Add([ordered]@{
    id = "stage_health"
    status = if ($health.status -eq "ok") { "pass" } else { "fail" }
    started_at = $healthStarted
    finished_at = [DateTime]::UtcNow.ToString("o")
    response_status = $health.status
})

$fixturePath = Join-Path $PSScriptRoot "..\data\telemetry\telemetry.ndjson"
$fixture = Get-Content $fixturePath -Raw
$ingestStarted = [DateTime]::UtcNow.ToString("o")
$ingest = Invoke-WebRequest `
    -Method "POST" `
    -Uri "$($ApiUrl.TrimEnd('/'))/ingest?source=telemetry" `
    -ContentType "application/x-ndjson" `
    -Body $fixture `
    -TimeoutSec 60 `
    -UseBasicParsing
$steps.Add([ordered]@{
    id = "stage_ingest"
    status = if ($ingest.StatusCode -in @(200, 202)) { "pass" } else { "fail" }
    started_at = $ingestStarted
    finished_at = [DateTime]::UtcNow.ToString("o")
    http_status = $ingest.StatusCode
})

$scenarioA = [ordered]@{
    incident_id = "pr31-release-gate-a"
    payload = [ordered]@{
        time_range_start = "2025-02-14T09:00:00Z"
        time_range_end = "2025-02-14T11:00:00Z"
        message = "power bus voltage anomaly"
        channels = @("bus_voltage")
    }
}
$scenarioB = [ordered]@{
    incident_id = "pr31-release-gate-b"
    payload = [ordered]@{
        time_range_start = "2025-02-14T09:00:00Z"
        time_range_end = "2025-02-14T09:00:01Z"
        ref = "no-data"
    }
}

$scenarioStarted = [DateTime]::UtcNow.ToString("o")
$resultA = Invoke-JsonRequest `
    -Method "POST" `
    -Url "$($ApiUrl.TrimEnd('/'))/runs" `
    -Body $scenarioA
$reportA = $resultA.report
$scenarioAPass = (
    -not [string]::IsNullOrWhiteSpace([string]$reportA.executive_summary) -and
    $null -ne $reportA.evidence -and
    @($reportA.evidence).Count -gt 0
)
$steps.Add([ordered]@{
    id = "stage_scenario_a"
    status = if ($scenarioAPass) { "pass" } else { "fail" }
    started_at = $scenarioStarted
    finished_at = [DateTime]::UtcNow.ToString("o")
    run_id = $resultA.run_id
    has_executive_summary = -not [string]::IsNullOrWhiteSpace(
        [string]$reportA.executive_summary
    )
    evidence_count = @($reportA.evidence).Count
    citation_count = @($reportA.citation_refs).Count
})

$scenarioStarted = [DateTime]::UtcNow.ToString("o")
$resultB = Invoke-JsonRequest `
    -Method "POST" `
    -Url "$($ApiUrl.TrimEnd('/'))/runs" `
    -Body $scenarioB
$reportB = $resultB.report
$scenarioBPass = ($null -ne $reportB.escalation_packet -or $resultB.escalated -eq $true)
$steps.Add([ordered]@{
    id = "stage_scenario_b"
    status = if ($scenarioBPass) { "pass" } else { "fail" }
    started_at = $scenarioStarted
    finished_at = [DateTime]::UtcNow.ToString("o")
    run_id = $resultB.run_id
    escalated = $scenarioBPass
    reason = $reportB.escalation_packet.reason
})

$dlqStarted = [DateTime]::UtcNow.ToString("o")
$dlq = Invoke-JsonRequest `
    -Method "GET" `
    -Url "$($ApiUrl.TrimEnd('/'))/dlq/telemetry?limit=$($MaxDlqRows + 1)"
$dlqCount = [int]$dlq.count
$steps.Add([ordered]@{
    id = "dlq_threshold"
    status = if ($dlqCount -le $MaxDlqRows) { "pass" } else { "fail" }
    started_at = $dlqStarted
    finished_at = [DateTime]::UtcNow.ToString("o")
    observed_rows = $dlqCount
    maximum_rows = $MaxDlqRows
})

$steps.Add((Invoke-NativeCapture `
    -Id "queue_stream_status" `
    -Command "kubectl" `
    -Arguments @(
        "wait", "--for=condition=Ready", "pod", "-n", $Namespace,
        "-l", "app.kubernetes.io/component=telemetry-persister", "--timeout=2m"
    )))
$steps.Add((Invoke-NativeCapture `
    -Id "rollback_helm_snapshot" `
    -Command "helm" `
    -Arguments @("get", "values", $Release, "-n", $Namespace, "-a") `
    -HashOnly))
$steps.Add((Invoke-NativeCapture `
    -Id "rollback_image_snapshot" `
    -Command "kubectl" `
    -Arguments @(
        "get", "deployment", "$Release-api", "-n", $Namespace,
        "-o", "jsonpath={.spec.template.spec.containers[*].image}"
    )))

$failed = @($steps | Where-Object { $_.status -ne "pass" })
$evidence = [ordered]@{
    schema_version = "pr31.release-gate.live.v1"
    release_id = $ReleaseId
    operator = $env:USERNAME
    environment = "stage"
    blocking = $true
    generated_at = $startedAt
    finished_at = [DateTime]::UtcNow.ToString("o")
    static_evidence = $StaticEvidencePath
    result = if ($failed.Count -eq 0) { "pass" } else { "fail" }
    steps = $steps
}

$directory = Split-Path -Parent $EvidencePath
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$evidence | ConvertTo-Json -Depth 12 | Set-Content $EvidencePath -Encoding UTF8

if ($failed.Count -gt 0) {
    throw "PR3.1 live release gate failed; evidence: $EvidencePath"
}
Write-Output "PR3.1 live release gate passed; evidence: $EvidencePath"
