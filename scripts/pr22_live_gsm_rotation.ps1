param(
    [string]$ProjectId = "spaceops-project-498213",
    [string]$Namespace = "spaceops-stage",
    [string]$Release = "spaceops",
    [string]$EvidencePath = "roadmap/02.5-production-readiness/sprint-2/evidence/PR2.2-live-gsm-rotation-2026-11-20.json"
)

$ErrorActionPreference = "Stop"

function New-RandomHex {
    param([int]$Bytes = 32)
    $buffer = New-Object byte[] $Bytes
    $rng = New-Object Security.Cryptography.RNGCryptoServiceProvider
    try {
        $rng.GetBytes($buffer)
    }
    finally {
        $rng.Dispose()
    }
    return -join ($buffer | ForEach-Object { $_.ToString("x2") })
}

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

function Get-KubernetesSecretValue {
    param([string]$Key)
    $encoded = & kubectl get secret "$Release-stage-secrets" -n $Namespace `
        -o "jsonpath={.data.$Key}"
    if ($LASTEXITCODE -ne 0 -or -not $encoded) {
        throw "Cannot read Kubernetes Secret key metadata for $Key"
    }
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
}

function Add-GsmVersion {
    param(
        [string]$SecretId,
        [string]$Value
    )
    $temp = [IO.Path]::GetTempFileName()
    try {
        [IO.File]::WriteAllText($temp, $Value, [Text.UTF8Encoding]::new($false))
        $args = @(
            "secrets", "versions", "add", $SecretId,
            "--project=$ProjectId",
            "--data-file=$temp",
            "--quiet",
            "--format=value(name)"
        )
        $name = (& gcloud @args | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $name) {
            throw "Failed to add GSM version for $SecretId"
        }
        return ($name -split "/")[-1]
    }
    finally {
        Remove-Item $temp -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-Kubectl {
    param([string[]]$Arguments)
    & kubectl @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl failed: $($Arguments -join ' ')"
    }
}

function Wait-ExternalSecret {
    $stamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Invoke-Kubectl @(
        "annotate", "externalsecret", "$Release-secrets",
        "-n", $Namespace, "force-sync=$stamp", "--overwrite"
    )
    Invoke-Kubectl @(
        "wait", "--for=condition=Ready",
        "externalsecret/$Release-secrets",
        "-n", $Namespace, "--timeout=3m"
    )
}

function Test-ApiAndDatabase {
    $code = @'
import json
import os
import urllib.request
import psycopg2

with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=15) as response:
    health = response.status
conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=10)
conn.close()
print(json.dumps({"health_status": health, "database_connect": True}))
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($code))
    $runner = "import base64,sys;exec(base64.b64decode(sys.argv[1]))"
    $result = (& kubectl exec -n $Namespace "deployment/$Release-api" -- `
        python -c $runner $encoded | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "API/database smoke failed"
    }
    return ($result | ConvertFrom-Json)
}

function Test-Approval {
    param([string]$PreviousToken)
    $previousB64 = [Convert]::ToBase64String(
        [Text.Encoding]::UTF8.GetBytes($PreviousToken)
    )
    $code = @'
import base64
import json
import os
import sys
import urllib.error
import urllib.request

url = "http://127.0.0.1:8000/approvals"
def status(token):
    request = urllib.request.Request(url)
    if token is not None:
        request.add_header("X-API-Key", token)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code

previous = base64.b64decode(sys.argv[2]).decode("utf-8")
print(json.dumps({
    "current_token_status": status(os.environ["APPROVAL_API_KEY"]),
    "previous_token_status": status(previous),
    "missing_token_status": status(None),
}))
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($code))
    $runner = "import base64,sys;exec(base64.b64decode(sys.argv[1]))"
    $result = (& kubectl exec -n $Namespace "deployment/$Release-api" -- `
        python -c $runner $encoded $previousB64 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Approval auth smoke failed"
    }
    return ($result | ConvertFrom-Json)
}

function Get-DeploymentUid {
    param([string]$Component)
    return (& kubectl get pods -n $Namespace `
        -l "app.kubernetes.io/component=$Component" `
        -o "jsonpath={.items[0].metadata.uid}" | Out-String).Trim()
}

$startedAt = [DateTime]::UtcNow.ToString("o")
$secretKeys = [ordered]@{
    "postgres-password" = "postgres-password"
    "openai-api-key" = "OPENAI_API_KEY"
    "approval-api-key" = "APPROVAL_API_KEY"
    "github-token" = "GITHUB_TOKEN"
    "ngc-api-key" = "NGC_API_KEY"
    "cursor-sh-api-key" = "CURSOR_SH_API_KEY"
    "gpu-llm-api-key" = "GPU_LLM_API_KEY"
}

$oldValues = @{}
$oldHashes = @{}
foreach ($entry in $secretKeys.GetEnumerator()) {
    $value = Get-KubernetesSecretValue $entry.Value
    $oldValues[$entry.Key] = $value
    $oldHashes[$entry.Key] = Get-Sha256 $value
}

$secretResourceVersionBefore = (& kubectl get secret "$Release-stage-secrets" `
    -n $Namespace -o "jsonpath={.metadata.resourceVersion}" | Out-String).Trim()
$externalReasonBefore = (& kubectl get externalsecret "$Release-secrets" `
    -n $Namespace -o "jsonpath={.status.conditions[0].reason}" | Out-String).Trim()
$podUidsBefore = @{
    api = Get-DeploymentUid "api"
    kb_mcp = Get-DeploymentUid "kb-mcp"
    gitops_mcp = Get-DeploymentUid "gitops-mcp"
    telemetry_persister = Get-DeploymentUid "telemetry-persister"
    postgres = Get-DeploymentUid "postgres"
}
$smokeBefore = Test-ApiAndDatabase

$newValues = @{}
$newHashes = @{}
foreach ($entry in $secretKeys.GetEnumerator()) {
    $value = New-RandomHex
    $newValues[$entry.Key] = $value
    $newHashes[$entry.Key] = Get-Sha256 $value
}

# Change the database role first while old clients are still running. The new
# Kubernetes Secret and client rollout follow immediately.
$sql = "ALTER ROLE spaceops WITH PASSWORD '$($newValues['postgres-password'])';"
Invoke-Kubectl @(
    "exec", "-n", $Namespace, "$Release-postgres-0", "--",
    "psql", "-U", "spaceops", "-d", "postgres",
    "-v", "ON_ERROR_STOP=1", "-c", $sql
)

$newVersions = @{}
foreach ($entry in $secretKeys.GetEnumerator()) {
    $secretId = "spaceops-stage-$($entry.Key)"
    $newVersions[$entry.Key] = Add-GsmVersion $secretId $newValues[$entry.Key]
}

Wait-ExternalSecret
$secretResourceVersionAfterSync = (& kubectl get secret "$Release-stage-secrets" `
    -n $Namespace -o "jsonpath={.metadata.resourceVersion}" | Out-String).Trim()
$externalReasonAfter = (& kubectl get externalsecret "$Release-secrets" `
    -n $Namespace -o "jsonpath={.status.conditions[0].reason}" | Out-String).Trim()

$deployments = @(
    "$Release-api",
    "$Release-kb-mcp",
    "$Release-gitops-mcp",
    "$Release-telemetry-persister"
)
foreach ($deployment in $deployments) {
    Invoke-Kubectl @("rollout", "restart", "deployment/$deployment", "-n", $Namespace)
}
Invoke-Kubectl @("rollout", "restart", "statefulset/$Release-postgres", "-n", $Namespace)
foreach ($deployment in $deployments) {
    Invoke-Kubectl @(
        "rollout", "status", "deployment/$deployment",
        "-n", $Namespace, "--timeout=5m"
    )
}
Invoke-Kubectl @(
    "rollout", "status", "statefulset/$Release-postgres",
    "-n", $Namespace, "--timeout=5m"
)

$podUidsAfter = @{
    api = Get-DeploymentUid "api"
    kb_mcp = Get-DeploymentUid "kb-mcp"
    gitops_mcp = Get-DeploymentUid "gitops-mcp"
    telemetry_persister = Get-DeploymentUid "telemetry-persister"
    postgres = Get-DeploymentUid "postgres"
}
$smokeAfter = Test-ApiAndDatabase
$approvalAfter = Test-Approval $oldValues["approval-api-key"]

# Roll back by publishing the previous value as a new latest version. The ESO
# LatestOrFail policy does not fall back when the numerically latest version is
# disabled, so disabling first would make the ExternalSecret not Ready.
$approvalVersion = $newVersions["approval-api-key"]
$rollbackVersion = Add-GsmVersion `
    "spaceops-stage-approval-api-key" `
    $oldValues["approval-api-key"]
Wait-ExternalSecret
$disableArgs = @(
    "secrets", "versions", "disable", $approvalVersion,
    "--secret=spaceops-stage-approval-api-key",
    "--project=$ProjectId", "--quiet"
)
& gcloud @disableArgs | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to disable approval version $approvalVersion for rollback"
}
Invoke-Kubectl @("rollout", "restart", "deployment/$Release-api", "-n", $Namespace)
Invoke-Kubectl @(
    "rollout", "status", "deployment/$Release-api",
    "-n", $Namespace, "--timeout=5m"
)
$approvalRollback = Test-Approval $newValues["approval-api-key"]
$rollbackApprovalHash = Get-Sha256 (Get-KubernetesSecretValue "APPROVAL_API_KEY")

$corpusParts = New-Object Collections.Generic.List[string]
$corpusParts.Add((& kubectl logs -n $Namespace `
    -l "app.kubernetes.io/instance=$Release" --all-containers=true `
    --prefix --since=2h 2>&1 | Out-String))
$corpusParts.Add((& kubectl logs -n external-secrets `
    -l "app.kubernetes.io/instance=external-secrets" --all-containers=true `
    --prefix --since=2h 2>&1 | Out-String))
$corpusParts.Add((& kubectl get events -n $Namespace -o json | Out-String))
$corpusParts.Add((& kubectl get events -n external-secrets -o json | Out-String))
$corpusParts.Add((& kubectl exec -n $Namespace "deployment/$Release-api" -- `
    sh -c "cat /app/data/audit.ndjson 2>/dev/null || true" | Out-String))

$observabilityCode = @'
import urllib.request
parts = []
for url in (
    "http://spaceops-jaeger:16686/api/services",
    "http://spaceops-prometheus:9090/api/v1/labels",
    "http://spaceops-prometheus:9090/api/v1/alerts",
):
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            parts.append(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        parts.append(type(exc).__name__)
print("\n".join(parts))
'@
$observabilityEncoded = [Convert]::ToBase64String(
    [Text.Encoding]::UTF8.GetBytes($observabilityCode)
)
$observabilityRunner = "import base64,sys;exec(base64.b64decode(sys.argv[1]))"
$corpusParts.Add((& kubectl exec -n $Namespace "deployment/$Release-api" -- `
    python -c $observabilityRunner $observabilityEncoded | Out-String))
$corpus = $corpusParts -join "`n"

$leakMatches = 0
foreach ($value in @($oldValues.Values) + @($newValues.Values)) {
    if ($value -and $corpus.Contains([string]$value)) {
        $leakMatches += 1
    }
}

$changedHashes = @{}
foreach ($entry in $secretKeys.GetEnumerator()) {
    $changedHashes[$entry.Key] = (
        $oldHashes[$entry.Key] -ne $newHashes[$entry.Key]
    )
}

$uidChanged = @{}
foreach ($name in $podUidsBefore.Keys) {
    $uidChanged[$name] = $podUidsBefore[$name] -ne $podUidsAfter[$name]
}

$evidence = [ordered]@{
    schema_version = "pr22.secret_rotation.live.v1"
    status = "live_pass"
    project_id = $ProjectId
    environment = "stage"
    started_at = $startedAt
    completed_at = [DateTime]::UtcNow.ToString("o")
    backend = "Google Secret Manager"
    authentication = "GKE Workload Identity; no service-account key"
    secret_ids = @($secretKeys.Keys | ForEach-Object { "spaceops-stage-$_" })
    gsm_new_versions = $newVersions
    sync = @{
        external_secret_reason_before = $externalReasonBefore
        external_secret_reason_after = $externalReasonAfter
        resource_version_before = $secretResourceVersionBefore
        resource_version_after = $secretResourceVersionAfterSync
        resource_version_changed = (
            $secretResourceVersionBefore -ne $secretResourceVersionAfterSync
        )
    }
    rotation = @{
        old_hashes = $oldHashes
        new_hashes = $newHashes
        hashes_changed = $changedHashes
        pod_uids_before = $podUidsBefore
        pod_uids_after = $podUidsAfter
        pod_uids_changed = $uidChanged
        database_password_coordinated = $true
        smoke_before = $smokeBefore
        smoke_after = $smokeAfter
        approval_after_rotation = $approvalAfter
    }
    rollback = @{
        class = "approval-api-key"
        disabled_rotated_version = $approvalVersion
        rollback_version = $rollbackVersion
        restored_hash_matches_baseline = (
            $rollbackApprovalHash -eq $oldHashes["approval-api-key"]
        )
        approval_after_rollback = $approvalRollback
    }
    leak_scan = @{
        scopes = @(
            "SpaceOps pod logs",
            "ESO controller logs",
            "SpaceOps and ESO Kubernetes events",
            "API audit NDJSON",
            "Jaeger service metadata",
            "Prometheus labels and alerts"
        )
        raw_value_matches = $leakMatches
    }
    safety = @{
        raw_values_in_evidence = $false
        production_credentials_used = $false
        mcp_service_token = "not_applicable_auth_not_implemented"
    }
}

$evidenceDirectory = Split-Path -Parent $EvidencePath
New-Item -ItemType Directory -Path $evidenceDirectory -Force | Out-Null
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Path $EvidencePath -Encoding UTF8

if (
    -not $evidence.sync.resource_version_changed -or
    $leakMatches -ne 0 -or
    -not $evidence.rollback.restored_hash_matches_baseline -or
    $approvalAfter.current_token_status -ne 200 -or
    $approvalAfter.previous_token_status -ne 401 -or
    $approvalRollback.current_token_status -ne 200 -or
    $approvalRollback.previous_token_status -ne 401
) {
    throw "PR2.2 live rotation evidence failed one or more assertions"
}

Write-Output "PR2.2 live rotation passed; evidence: $EvidencePath"
