param(
    [string]$Namespace = "spaceops-dev",
    [string]$Release = "spaceops",
    [string]$EvidencePath = "roadmap/02.5-production-readiness/sprint-3/evidence/PR3.2-game-day-local-2026-11-23.json",
    [string]$Operator = $env:USERNAME
)

$ErrorActionPreference = "Stop"
$timeline = New-Object Collections.Generic.List[object]

function Add-Timeline {
    param(
        [string]$Phase,
        [string]$Event,
        [string]$Result
    )
    $timeline.Add([ordered]@{
        at = [DateTime]::UtcNow.ToString("o")
        phase = $Phase
        event = $Event
        result = $Result
    })
}

function Invoke-Native {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [switch]$AllowFailure
    )
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = (& $Command @Arguments 2>&1 | Out-String).Trim()
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$Command failed with exit code ${exitCode}: $output"
    }
    return [ordered]@{
        exit_code = $exitCode
        output = $output
    }
}

function Test-ApiHealth {
    $code = @'
import json
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as response:
    body = json.loads(response.read().decode("utf-8"))
print(body.get("status", ""))
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($code))
    $runner = "import base64,sys;exec(base64.b64decode(sys.argv[1]))"
    $result = Invoke-Native `
        -Command "kubectl" `
        -Arguments @(
            "exec", "-n", $Namespace, "deployment/$Release-api", "--",
            "python", "-c", $runner, $encoded
        )
    return $result.output -eq "ok"
}

$startedAt = [DateTime]::UtcNow.ToString("o")
$context = (Invoke-Native -Command "kubectl" -Arguments @(
    "config", "current-context"
)).output
if ($context -notlike "kind-*") {
    throw "Refusing game day outside kind context; current context: $context"
}

$historyRaw = (Invoke-Native -Command "helm" -Arguments @(
    "history", $Release, "-n", $Namespace, "-o", "json"
)).output
$history = $historyRaw | ConvertFrom-Json
$baselineRevision = [int](($history | Sort-Object revision -Descending)[0].revision)
if (-not (Test-ApiHealth)) {
    throw "Baseline API health failed"
}
Add-Timeline "prepare" "Baseline revision and API health verified" "pass"

$upgrade = Invoke-Native -Command "helm" -Arguments @(
    "upgrade", $Release, "deploy/helm/spaceops",
    "-n", $Namespace,
    "-f", "deploy/helm/spaceops/values.yaml",
    "-f", "deploy/helm/spaceops/values-dev.yaml",
    "-f", "deploy/helm/spaceops/values-minimal-dev.yaml",
    "--set", "secrets.postgresPassword=spaceops",
    "--set", "api.extraEnv.PR32_GAME_DAY=api-outage",
    "--wait", "--timeout", "5m"
)
$historyRaw = (Invoke-Native -Command "helm" -Arguments @(
    "history", $Release, "-n", $Namespace, "-o", "json"
)).output
$history = $historyRaw | ConvertFrom-Json
$incidentRevision = [int](($history | Sort-Object revision -Descending)[0].revision)
if ($incidentRevision -le $baselineRevision) {
    throw "Game-day upgrade did not create a new Helm revision"
}
Add-Timeline "inject" "Deployed game-day marker revision $incidentRevision" "pass"

Invoke-Native -Command "kubectl" -Arguments @(
    "scale", "deployment/$Release-api", "-n", $Namespace, "--replicas=0"
) | Out-Null
$observedReplicas = (Invoke-Native -Command "kubectl" -Arguments @(
    "get", "deployment/$Release-api", "-n", $Namespace,
    "-o", "jsonpath={.status.availableReplicas}"
) -AllowFailure).output
$syntheticAlert = ($observedReplicas -in @("", "0"))
if (-not $syntheticAlert) {
    throw "API outage injection did not reduce available replicas to zero"
}
Add-Timeline "detect" "Synthetic APIUnavailable signal: available replicas = 0" "pass"

$triage = Invoke-Native -Command "kubectl" -Arguments @(
    "get", "deployment,pods", "-n", $Namespace,
    "-l", "app.kubernetes.io/component=api", "-o", "wide"
)
Add-Timeline "triage" "Primary on-call captured API deployment and pod state" "pass"
Add-Timeline "escalate" "Incident commander declared SEV-2 and selected Helm rollback" "pass"

$rollbackStarted = [DateTime]::UtcNow
Invoke-Native -Command "helm" -Arguments @(
    "rollback", $Release, "$baselineRevision",
    "-n", $Namespace, "--wait", "--timeout", "10m"
) | Out-Null
Invoke-Native -Command "kubectl" -Arguments @(
    "rollout", "status", "deployment/$Release-api",
    "-n", $Namespace, "--timeout=5m"
) | Out-Null
if (-not (Test-ApiHealth)) {
    throw "Post-rollback API health failed"
}
$rollbackSeconds = [math]::Round(
    ([DateTime]::UtcNow - $rollbackStarted).TotalSeconds,
    2
)
Add-Timeline "mitigate" "Rolled back to revision $baselineRevision; API health restored" "pass"

$marker = (Invoke-Native -Command "kubectl" -Arguments @(
    "get", "deployment/$Release-api", "-n", $Namespace,
    "-o", "jsonpath={.spec.template.spec.containers[0].env[?(@.name=='PR32_GAME_DAY')].value}"
) -AllowFailure).output
$markerRemoved = [string]::IsNullOrWhiteSpace($marker)
if (-not $markerRemoved) {
    throw "Rollback did not remove the game-day marker"
}
Add-Timeline "verify" "Game-day marker removed and rollback state verified" "pass"

$evidence = [ordered]@{
    schema_version = "pr32.game-day.v1"
    result = "pass"
    environment = "local-kind"
    context = $context
    namespace = $Namespace
    operator = $Operator
    started_at = $startedAt
    finished_at = [DateTime]::UtcNow.ToString("o")
    incident_class = "api_outage"
    severity = "SEV-2"
    detection = [ordered]@{
        signal = "synthetic APIUnavailable"
        available_replicas = 0
        fired = $syntheticAlert
    }
    escalation = [ordered]@{
        primary_on_call = "platform"
        incident_commander = "production-readiness lead"
        communications = "simulated status update using the PR3.2 template"
    }
    rollback = [ordered]@{
        baseline_revision = $baselineRevision
        incident_revision = $incidentRevision
        command = "helm rollback $Release $baselineRevision -n $Namespace --wait"
        duration_seconds = $rollbackSeconds
        api_health_after = "ok"
        marker_removed = $markerRemoved
    }
    triage = [ordered]@{
        command = "kubectl get deployment,pods -l app.kubernetes.io/component=api"
        output_retained = $false
        output_length = $triage.output.Length
    }
    timeline = $timeline
    action_items = @(
        [ordered]@{
            id = "PR3.2-A1"
            action = "Automate game-day evidence and keep it CI-safe"
            owner = "platform"
            status = "done"
            evidence = "scripts/pr32_game_day.ps1"
        },
        [ordered]@{
            id = "PR3.2-A2"
            action = "Exercise alert-manager delivery with a real paging integration"
            owner = "on-call lead"
            status = "backlog"
            target = "before production pilot"
            tracking = "roadmap/backlog/BL-006-live-paging-integration-drill.md"
        }
    )
    safety = [ordered]@{
        production_traffic = $false
        cloud_cost = $false
        secrets_in_evidence = $false
    }
}

$directory = Split-Path -Parent $EvidencePath
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$evidence | ConvertTo-Json -Depth 12 | Set-Content $EvidencePath -Encoding UTF8
Write-Output "PR3.2 game day passed; evidence: $EvidencePath"
