# AutoDrama 프로젝트 정리 스크립트 (Windows PowerShell)
# 삭제 가능한 구버전 파일 및 불필요한 파일 제거

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AutoDrama 프로젝트 정리 스크립트" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 삭제할 파일 목록
$filesToDelete = @(
    "prompts\outline.py",
    "prompts\outline_v2.py",
    "prompts\part.py",
    "prompts\backup\outline_old.py",
    "prompts\backup\part_old.py",
    "test_phase1_7.py",
    "prompt.md",
    "workflow.md"
)

# 삭제할 폴더 목록
$foldersToDelete = @(
    "prompts\backup",
    "audio",
    "llm"
)

Write-Host "다음 파일들이 삭제됩니다:" -ForegroundColor Yellow
Write-Host ""
Write-Host "[파일]" -ForegroundColor Green
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Write-Host "  - $file" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "[폴더]" -ForegroundColor Green
foreach ($folder in $foldersToDelete) {
    if (Test-Path $folder) {
        Write-Host "  - $folder\" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "⚠️  주의: 이 작업은 되돌릴 수 없습니다!" -ForegroundColor Red
Write-Host ""

# 사용자 확인
$confirmation = Read-Host "정말 삭제하시겠습니까? (Y/N)"

if ($confirmation -ne "Y" -and $confirmation -ne "y") {
    Write-Host ""
    Write-Host "❌ 삭제 작업이 취소되었습니다." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "🗑️  삭제 작업을 시작합니다..." -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
$notFoundCount = 0

# 파일 삭제
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force
            Write-Host "✓ 삭제 완료: $file" -ForegroundColor Green
            $deletedCount++
        } catch {
            Write-Host "✗ 삭제 실패: $file - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "○ 파일 없음: $file" -ForegroundColor DarkGray
        $notFoundCount++
    }
}

# 폴더 삭제
foreach ($folder in $foldersToDelete) {
    if (Test-Path $folder) {
        try {
            Remove-Item $folder -Recurse -Force
            Write-Host "✓ 폴더 삭제 완료: $folder\" -ForegroundColor Green
            $deletedCount++
        } catch {
            Write-Host "✗ 폴더 삭제 실패: $folder\ - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "○ 폴더 없음: $folder\" -ForegroundColor DarkGray
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  정리 작업 완료!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "삭제된 항목: $deletedCount" -ForegroundColor Green
Write-Host "존재하지 않음: $notFoundCount" -ForegroundColor DarkGray
Write-Host ""
