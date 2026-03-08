param(
  [Parameter(Mandatory=$true)][string]$Src,
  [Parameter(Mandatory=$true)][string]$Dst,
  [int]$ChunkSize = 900
)

$sshArgs = @('-p','2222','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=10','Roy@192.168.3.120')
$tmp = "$Dst.codex_b64"

function Invoke-RemotePs([string]$ScriptText) {
  $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($ScriptText))
  & ssh @sshArgs "powershell -NoProfile -EncodedCommand $enc"
  if ($LASTEXITCODE -ne 0) { throw "remote command failed" }
}

$initScript = @"
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName('$Dst')) | Out-Null
Set-Content -Path '$tmp' -Value '' -NoNewline
"@
Invoke-RemotePs $initScript | Out-Null

$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($Src))
for ($i = 0; $i -lt $b64.Length; $i += $ChunkSize) {
  $len = [Math]::Min($ChunkSize, $b64.Length - $i)
  $chunk = $b64.Substring($i, $len)
  $appendScript = "Add-Content -Path '$tmp' -Value '$chunk' -NoNewline"
  Invoke-RemotePs $appendScript | Out-Null
}

$finishScript = @"
`$b64 = Get-Content -Raw -Path '$tmp'
[IO.File]::WriteAllBytes('$Dst', [Convert]::FromBase64String(`$b64))
Remove-Item '$tmp' -Force
Write-Output 'UPLOAD_OK'
"@
Invoke-RemotePs $finishScript
