#!/bin/bash
# AutoDrama 프로젝트 정리 스크립트 (Linux/Mac Bash)
# 삭제 가능한 구버전 파일 및 불필요한 파일 제거

echo "============================================"
echo "  AutoDrama 프로젝트 정리 스크립트"
echo "============================================"
echo ""

# 삭제할 파일 목록
FILES_TO_DELETE=(
    "prompts/outline.py"
    "prompts/outline_v2.py"
    "prompts/part.py"
    "prompts/backup/outline_old.py"
    "prompts/backup/part_old.py"
    "test_phase1_7.py"
    "prompt.md"
    "workflow.md"
)

# 삭제할 폴더 목록
FOLDERS_TO_DELETE=(
    "prompts/backup"
    "audio"
    "llm"
)

echo -e "\033[33m다음 파일들이 삭제됩니다:\033[0m"
echo ""
echo -e "\033[32m[파일]\033[0m"
for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo -e "\033[32m[폴더]\033[0m"
for folder in "${FOLDERS_TO_DELETE[@]}"; do
    if [ -d "$folder" ]; then
        echo "  - $folder/"
    fi
done

echo ""
echo -e "\033[31m⚠️  주의: 이 작업은 되돌릴 수 없습니다!\033[0m"
echo ""

# 사용자 확인
read -p "정말 삭제하시겠습니까? (Y/N): " confirmation

if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "\033[33m❌ 삭제 작업이 취소되었습니다.\033[0m"
    exit 0
fi

echo ""
echo -e "\033[36m🗑️  삭제 작업을 시작합니다...\033[0m"
echo ""

deleted_count=0
not_found_count=0

# 파일 삭제
for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        if rm -f "$file"; then
            echo -e "\033[32m✓ 삭제 완료: $file\033[0m"
            ((deleted_count++))
        else
            echo -e "\033[31m✗ 삭제 실패: $file\033[0m"
        fi
    else
        echo -e "\033[90m○ 파일 없음: $file\033[0m"
        ((not_found_count++))
    fi
done

# 폴더 삭제
for folder in "${FOLDERS_TO_DELETE[@]}"; do
    if [ -d "$folder" ]; then
        if rm -rf "$folder"; then
            echo -e "\033[32m✓ 폴더 삭제 완료: $folder/\033[0m"
            ((deleted_count++))
        else
            echo -e "\033[31m✗ 폴더 삭제 실패: $folder/\033[0m"
        fi
    else
        echo -e "\033[90m○ 폴더 없음: $folder/\033[0m"
        ((not_found_count++))
    fi
done

echo ""
echo "============================================"
echo "  정리 작업 완료!"
echo "============================================"
echo -e "\033[32m삭제된 항목: $deleted_count\033[0m"
echo -e "\033[90m존재하지 않음: $not_found_count\033[0m"
echo ""
