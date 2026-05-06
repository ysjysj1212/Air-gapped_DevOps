import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5000/api"

# 생성된 YAML 디렉토리
YAML_DIR = os.path.join(os.path.dirname(__file__), "generated_yamls")

print("=" * 80)
print("🔍 저장된 YAML 파일 유효성 검사")
print("=" * 80)

# 디렉토리 확인
if not os.path.exists(YAML_DIR):
    print(f"❌ 디렉토리 없음: {YAML_DIR}")
    exit(1)

# YAML 파일 목록 가져오기
yaml_files = sorted([f for f in os.listdir(YAML_DIR) if f.endswith(('.yml', '.yaml'))])

if not yaml_files:
    print(f"❌ YAML 파일 없음: {YAML_DIR}")
    exit(1)

print(f"\n📂 {len(yaml_files)}개의 YAML 파일 발견\n")

results = []

for idx, filename in enumerate(yaml_files, 1):
    filepath = os.path.join(YAML_DIR, filename)
    print(f"[{idx}/{len(yaml_files)}] 검증 중: {filename}")
    
    try:
        # 파일 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        # 유효성 검사
        r = requests.post(
            f'{BASE_URL}/validate-yaml',
            json={'yaml': yaml_content, 'ci_type': 'auto'},
            timeout=30
        )
        
        if r.status_code != 200:
            print(f"❌ 검증 요청 실패: {r.status_code}")
            print(f"   응답: {r.text}\n")
            results.append({
                "filename": filename,
                "status": "검증_요청_실패",
                "details": r.text
            })
            continue
        
        validation = json.loads(r.text)
        
        if validation.get('valid'):
            print(f"✅ 유효함!")
            print(f"   형식: {validation.get('ci_type', 'unknown')}")
            print(f"   크기: {len(yaml_content)} bytes")
            results.append({
                "filename": filename,
                "status": "✅ 유효함",
                "details": validation,
                "size": len(yaml_content)
            })
        else:
            print(f"⚠️ 검증 경고 또는 실패")
            errors = validation.get('errors', [])
            warnings = validation.get('warnings', [])
            
            if errors:
                print(f"   ❌ 에러:")
                for error in errors:
                    print(f"      - {error}")
            
            if warnings:
                print(f"   ⚠️ 경고:")
                for warning in warnings:
                    print(f"      - {warning}")
            
            results.append({
                "filename": filename,
                "status": "⚠️ 경고/에러" if errors else "⚠️ 경고",
                "details": validation,
                "size": len(yaml_content)
            })
        
        print()
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}\n")
        results.append({
            "filename": filename,
            "status": "오류",
            "details": str(e)
        })

# 최종 요약
print("=" * 80)
print("📊 검증 결과 요약")
print("=" * 80 + "\n")

valid_count = sum(1 for r in results if "✅" in r["status"])
warning_count = sum(1 for r in results if "⚠️" in r["status"])
error_count = len(results) - valid_count - warning_count

for result in results:
    print(f"📄 {result['filename']}")
    print(f"   상태: {result['status']}")
    if 'size' in result:
        print(f"   크기: {result['size']} bytes")
    print()

print("=" * 80)
print(f"✅ 유효: {valid_count}개")
print(f"⚠️  경고/에러: {warning_count}개")
print(f"❌ 실패: {error_count}개")
print(f"\n🎯 전체 성공률: {(valid_count + warning_count) / len(results) * 100:.1f}%")
print("=" * 80)

# JSON 형식으로 상세 결과 저장
summary_file = os.path.join(YAML_DIR, "validation_summary.json")
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n💾 상세 결과 저장: {summary_file}")
