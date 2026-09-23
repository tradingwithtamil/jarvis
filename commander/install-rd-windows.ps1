# RD Commander Windows Bootstrap v0.1.0
$ErrorActionPreference='Stop'
$Root='C:\RDCommander'
$EnrollBase='https://45-67-52-142.sslip.io/rd'
$RelayBase='https://45-67-52-142.sslip.io/jarvis'
$AgentUrl='https://raw.githubusercontent.com/tradingwithtamil/jarvis/6600b2b924c4a83a4c4cdedf96dcbca3c7c5015f/commander/agent-safe.js'
$AgentSha256='653ba6119bb6ca1a48940e06eede8d9739f61ca3b7f213cb7e5ae2d1c76eece4'

function Assert-Admin {
  $p=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if(-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run this command in Administrator PowerShell'}
}
function Get-Fingerprint {
  $uuid=[string](Get-CimInstance Win32_ComputerSystemProduct).UUID
  $mg=[string](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography').MachineGuid
  $sha=[Security.Cryptography.SHA256]::Create()
  try{return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($uuid+'|'+$mg))))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Ensure-Node22 {
  $nodeRoot=Join-Path $Root 'node'; $nodeExe=Join-Path $nodeRoot 'node.exe'
  if(Test-Path $nodeExe){$v=& $nodeExe --version 2>$null;if($LASTEXITCODE -eq 0 -and $v -match '^v22\.'){return $nodeExe}}
  $zip=Join-Path $env:TEMP 'rdcommander-node22.zip'; $tmp=Join-Path $env:TEMP ('rdcommander-node22-'+[guid]::NewGuid().ToString('N'))
  Remove-Item $nodeRoot -Recurse -Force -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Force -Path $Root|Out-Null
  $idx=Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json'; $rel=$idx|Where-Object {$_.version -match '^v22\.' -and $_.files -contains 'win-x64-zip'}|Select-Object -First 1
  if(-not $rel){throw 'Could not resolve portable Node 22'}
  Invoke-WebRequest -UseBasicParsing -Uri ('https://nodejs.org/dist/'+$rel.version+'/node-'+$rel.version+'-win-x64.zip') -OutFile $zip
  Expand-Archive -Path $zip -DestinationPath $tmp -Force; $src=Get-ChildItem $tmp -Directory|Select-Object -First 1
  if(-not $src){throw 'Portable Node archive invalid'}; Move-Item $src.FullName $nodeRoot; Remove-Item $zip,$tmp -Recurse -Force -ErrorAction SilentlyContinue
  $v=& $nodeExe --version;if($LASTEXITCODE -ne 0 -or $v -notmatch '^v22\.'){throw 'Portable Node 22 verification failed'}; return $nodeExe
}

Assert-Admin
New-Item -ItemType Directory -Force -Path $Root|Out-Null
$fp=Get-Fingerprint; $name=$env:COMPUTERNAME; $slug=($name.ToLowerInvariant() -replace '[^a-z0-9._-]','-').Trim('-')
if(-not $slug){$slug='windows'}; $deviceId=($slug+'-'+$fp.Substring(0,8))
$req=@{deviceId=$deviceId;name=$name;platform='win32';version='0.1.1';fingerprint=$fp}|ConvertTo-Json -Compress
$enroll=Invoke-RestMethod -Method Post -Uri ($EnrollBase+'/device/request') -ContentType 'application/json' -Body $req
Write-Host ''; Write-Host 'RD COMMANDER APPROVAL REQUIRED' -ForegroundColor Yellow
Write-Host ('Code: '+$enroll.code) -ForegroundColor Cyan; Write-Host ('Approval: '+$enroll.approvalUrl)
try{Start-Process $enroll.approvalUrl}catch{}
$approved=$null
for($i=0;$i -lt 200;$i++){Start-Sleep -Seconds 3;try{$s=Invoke-RestMethod -Uri ($EnrollBase+'/device/status?claim='+[uri]::EscapeDataString($enroll.claim));if($s.state -eq 'approved'){$approved=$s;break}}catch{}}
if(-not $approved -or -not $approved.agentToken){throw 'RD Commander approval timed out'}
$nodeExe=Ensure-Node22
$agentPath=Join-Path $Root 'agent-safe.js'; Invoke-WebRequest -UseBasicParsing -Uri $AgentUrl -OutFile $agentPath
$actual=(Get-FileHash -Algorithm SHA256 $agentPath).Hash.ToLowerInvariant(); if($actual -ne $AgentSha256){Remove-Item $agentPath -Force;throw 'RD Commander agent SHA256 mismatch'}
$roots=@(Get-PSDrive -PSProvider FileSystem|Where-Object {$_.Root -match '^[A-Za-z]:\\$'}|ForEach-Object {$_.Root})
$cfg=[ordered]@{relayUrl=$approved.relayUrl;deviceId=$deviceId;name=$name;agentToken=$approved.agentToken;allowedRoots=$roots;allowedTriggers=@();pollSeconds=2}
$json=$cfg|ConvertTo-Json -Depth 6; [IO.File]::WriteAllText((Join-Path $Root 'agent-config.json'),$json,(New-Object Text.UTF8Encoding($false)))
$run='@echo off'+[Environment]::NewLine+':loop'+[Environment]::NewLine+'"'+$nodeExe+'" "'+$agentPath+'" "'+(Join-Path $Root 'agent-config.json')+'" >> "'+(Join-Path $Root 'agent.log')+'" 2>> "'+(Join-Path $Root 'agent.err.log')+'"'+[Environment]::NewLine+'timeout /t 5 /nobreak >nul'+[Environment]::NewLine+'goto loop'
[IO.File]::WriteAllText((Join-Path $Root 'run-agent.cmd'),$run,(New-Object Text.ASCIIEncoding))
$sentinel=@'
$ErrorActionPreference='Continue'
$Root='C:\RDCommander'; $StatusRoot='C:\Sentinel\RDCommander'; New-Item -ItemType Directory -Force -Path $StatusRoot|Out-Null
function Log($m){Add-Content -LiteralPath (Join-Path $StatusRoot 'watchdog.log') -Value ((Get-Date -Format s)+' '+$m)}
while($true){
  $p=Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue|Where-Object {$_.CommandLine -match 'RDCommander.*agent-safe\.js'}|Select-Object -First 1
  if(-not $p){Log 'agent missing; restarting task'; Start-ScheduledTask -TaskName 'RDCommanderAgent' -ErrorAction SilentlyContinue; Start-Sleep 5; $p=Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue|Where-Object {$_.CommandLine -match 'RDCommander.*agent-safe\.js'}|Select-Object -First 1}
  $status=[ordered]@{time=(Get-Date).ToUniversalTime().ToString('o');agentRunning=[bool]$p;pid=if($p){$p.ProcessId}else{$null}}|ConvertTo-Json -Compress
  Set-Content -LiteralPath (Join-Path $StatusRoot 'status.json') -Value $status -Encoding UTF8; Start-Sleep 15
}
'@
[IO.File]::WriteAllText((Join-Path $Root 'RDCommander-Sentinel.ps1'),$sentinel,(New-Object Text.UTF8Encoding($false)))
$principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$startup=New-ScheduledTaskTrigger -AtStartup
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$agentAction=New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c "'+(Join-Path $Root 'run-agent.cmd')+'"')
Register-ScheduledTask -TaskName 'RDCommanderAgent' -Action $agentAction -Trigger $startup -Principal $principal -Settings $settings -Force|Out-Null
$sentAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Root 'RDCommander-Sentinel.ps1')+'"')
Register-ScheduledTask -TaskName 'RDCommanderSentinel' -Action $sentAction -Trigger $startup -Principal $principal -Settings $settings -Force|Out-Null
Start-ScheduledTask -TaskName 'RDCommanderAgent'; Start-ScheduledTask -TaskName 'RDCommanderSentinel'
Start-Sleep -Seconds 6
$proof=Invoke-RestMethod -Uri ($RelayBase+'/status'); $row=$proof.devices|Where-Object {$_.deviceId -eq $deviceId}|Select-Object -First 1
if(-not $row){throw 'RD Commander enrolled but relay proof not found yet'}
Write-Host ''; Write-Host ('RD COMMANDER CONNECTED: '+$row.name+' / '+$row.status) -ForegroundColor Green
Write-Host 'Auto-start: RDCommanderAgent + RDCommanderSentinel' -ForegroundColor Green
Write-Host 'Reconnect/self-heal: ENABLED' -ForegroundColor Green
