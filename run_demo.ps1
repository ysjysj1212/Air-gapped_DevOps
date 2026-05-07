# LLM YAML 생성 스크립트 (PowerShell)
# 사용법: .\run_demo.ps1

Write-Host "🎬 LLM YAML Generator" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 사용 방법:" -ForegroundColor Yellow
Write-Host "   자연어로 원하는 CI/CD 파이프라인을 설명해주세요." -ForegroundColor Gray
Write-Host "   예: 'Node.js 프로젝트용 CI YAML 만들어줘'" -ForegroundColor Gray
Write-Host ""

Write-Host "📝 프롬프트를 입력하세요:" -ForegroundColor Green
Write-Host ""

# 사용자 입력
$selectedPrompt = Read-Host "프롬프트"

# 입력 유효성 검사
if ([string]::IsNullOrWhiteSpace($selectedPrompt)) {
    Write-Host ""
    Write-Host "❌ 프롬프트를 입력해주세요." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ 입력된 프롬프트:" -ForegroundColor Green
Write-Host "   $selectedPrompt" -ForegroundColor Cyan
Write-Host ""

Write-Host "⏳ Flask 서버에 요청 중..." -ForegroundColor Yellow
Write-Host "   (Gemma 2B 처리: 10-30초 소요)" -ForegroundColor Gray
Write-Host ""

try {
    # API 호출
    $body = @{ requirements = $selectedPrompt } | ConvertTo-Json -Compress
    
    $response = Invoke-WebRequest `
        -Uri "http://localhost:5000/api/generate-yaml" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $body `
        -ErrorAction Stop

    $data = $response.Content | ConvertFrom-Json

    # 결과 출력
    Write-Host "✅ YAML 생성 완료!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📊 생성 정보:" -ForegroundColor Cyan
    Write-Host "  • 생성 방식: $($data.generated_by)" -ForegroundColor White
    Write-Host "  • 타임스탬프: $($data.timestamp)" -ForegroundColor White
    Write-Host "  • 크기: $($data.yaml.Length) bytes" -ForegroundColor White
    Write-Host "  • 라인수: $($data.yaml.Split("`n").Count) 줄" -ForegroundColor White
    Write-Host ""

    Write-Host "📝 생성된 YAML:" -ForegroundColor Cyan
    Write-Host "=" * 70
    Write-Host $data.yaml
    Write-Host "=" * 70
    Write-Host ""

    # 파일로 저장
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $filename = "generated_yamls/llm-$timestamp.yml"
    
    # 폴더 생성 확인
    if (-not (Test-Path "generated_yamls")) {
        New-Item -ItemType Directory -Path "generated_yamls" -Force | Out-Null
    }
    
    $data.yaml | Out-File -FilePath $filename -Encoding UTF8
    
    Write-Host "✅ 파일 저장 완료:" -ForegroundColor Green
    Write-Host "   📁 $filename" -ForegroundColor Cyan
    Write-Host ""

    # 추가 정보
    Write-Host "🎯 다음 단계:" -ForegroundColor Magenta
    Write-Host "  • 생성된 YAML을 프로젝트에 맞게 수정" -ForegroundColor White
    Write-Host "  • 다른 프롬프트로 다시 실행: .\run_demo.ps1" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "❌ 오류 발생:" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 확인사항:" -ForegroundColor Yellow
    Write-Host "   1️⃣  Flask 서버가 실행 중인지 확인" -ForegroundColor White
    Write-Host "      → 터미널에서: cd DevOps\src && python app.py" -ForegroundColor Gray
    Write-Host "   2️⃣  http://localhost:5000 에 접속 가능한지 확인" -ForegroundColor White
    Write-Host "   3️⃣  Ollama/Gemma가 실행 중인지 확인" -ForegroundColor White
    Write-Host ""
    exit 1
}

