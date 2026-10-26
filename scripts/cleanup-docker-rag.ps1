# Cleanup Docker artifacts for this RAG project ONLY.
# Does NOT touch CareerAssistant (careerassistant-* containers/images/volumes).
# Usage (PowerShell):
#   .\scripts\cleanup-docker-rag.ps1
# Then follow docs/CLEANUP_C_DRIVE.md section 3 to compact docker_data.vhdx.

$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Project: $projectRoot" -ForegroundColor Cyan
Write-Host '== 1) docker-compose down (this project only) ==' -ForegroundColor Cyan
docker-compose down --remove-orphans

Write-Host '== 2) Remove this project images ==' -ForegroundColor Cyan
$patterns = @(
  'production-agentic-rag-course-main*',
  'production-agentic-rag-course*',
  'arxiv-paper-curator*'
)
$images = docker images --format '{{.Repository}}:{{.Tag}}'
foreach ($img in $images) {
  if ([string]::IsNullOrWhiteSpace($img)) { continue }
  foreach ($p in $patterns) {
    if ($img -like $p) {
      Write-Host "  rmi $img"
      docker rmi $img 2>$null
    }
  }
}

Write-Host '== 3) Dangling images only ==' -ForegroundColor Cyan
docker image prune -f

Write-Host '== 4) Build cache ==' -ForegroundColor Cyan
docker builder prune -af

Write-Host '== 5) Verify CareerAssistant still present ==' -ForegroundColor Cyan
docker ps -a --filter "name=careerassistant" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'

Write-Host '== 6) Disk usage ==' -ForegroundColor Cyan
docker system df

Write-Host ''
Write-Host 'NEXT (required): compact WSL vhdx — see docs/CLEANUP_C_DRIVE.md section 3' -ForegroundColor Yellow
Write-Host '  1) Quit Docker Desktop'
Write-Host '  2) wsl --shutdown'
Write-Host '  3) diskpart compact on C:\Users\sim\AppData\Local\Docker\wsl\disk\docker_data.vhdx'
