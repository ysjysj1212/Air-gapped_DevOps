# DevOps1 프로젝트 구조 생성 스크립트

# 기본 경로 설정
$rootPath = "$PSScriptRoot\DevOps1"

# 루트 폴더 생성
Write-Host "Creating DevOps1 root folder..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $rootPath -Force | Out-Null

# 서브 폴더 생성
$folders = @(
    "src",
    "tests",
    "docker",
    "templates",
    "docs"
)

foreach ($folder in $folders) {
    $folderPath = Join-Path $rootPath $folder
    Write-Host "Creating folder: $folder" -ForegroundColor Green
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
}

# src 폴더 파일들
$srcFiles = @(
    "__init__.py",
    "app.py",
    "llm_service.py",
    "sandbox_service.py",
    "template_generator.py",
    "validators.py"
)

foreach ($file in $srcFiles) {
    $filePath = Join-Path $rootPath "src" $file
    Write-Host "Creating file: src/$file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# tests 폴더 파일들
$testFiles = @(
    "__init__.py",
    "test_api.py"
)

foreach ($file in $testFiles) {
    $filePath = Join-Path $rootPath "tests" $file
    Write-Host "Creating file: tests/$file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# docker 폴더 파일들
$dockerFiles = @(
    "Dockerfile",
    "Dockerfile.validator"
)

foreach ($file in $dockerFiles) {
    $filePath = Join-Path $rootPath "docker" $file
    Write-Host "Creating file: docker/$file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# templates 폴더 파일들
$templateFiles = @(
    "github_actions.yaml",
    "gitlab_ci.yaml"
)

foreach ($file in $templateFiles) {
    $filePath = Join-Path $rootPath "templates" $file
    Write-Host "Creating file: templates/$file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# docs 폴더 파일들
$docFiles = @(
    "API_SPEC.md",
    "ARCHITECTURE.md"
)

foreach ($file in $docFiles) {
    $filePath = Join-Path $rootPath "docs" $file
    Write-Host "Creating file: docs/$file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# 루트 폴더 파일들
$rootFiles = @(
    "requirements.txt",
    "docker-compose.yml",
    "README.md",
    "QUICKSTART.md",
    ".gitignore"
)

foreach ($file in $rootFiles) {
    $filePath = Join-Path $rootPath $file
    Write-Host "Creating file: $file" -ForegroundColor Yellow
    New-Item -ItemType File -Path $filePath -Force | Out-Null
}

# 완료 메시지
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "✓ DevOps1 구조 생성 완료!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan

# 생성된 구조 표시
Write-Host "`n생성된 디렉토리 구조:" -ForegroundColor Cyan
Get-ChildItem -Path $rootPath -Recurse | ForEach-Object {
    $indent = "  " * ($_.FullName.Split("\").Count - $rootPath.Split("\").Count)
    Write-Host "$indent$($_.Name)"
}
