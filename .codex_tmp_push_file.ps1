param(
  [Parameter(Mandatory=$true)][string]$Src,
  [Parameter(Mandatory=$true)][string]$Dst
)
$content = Get-Content -Raw -Encoding UTF8 -Path $Src
$remote = @"
`$c=[Console]::In.ReadToEnd()
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName('$Dst')) | Out-Null
Set-Content -Path '$Dst' -Value `$c -Encoding UTF8
Write-Output 'UPLOAD_OK'
"@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($remote))
$content | ssh -p 2222 -o StrictHostKeyChecking=no Roy@192.168.3.120 "powershell -NoProfile -EncodedCommand $encoded"
