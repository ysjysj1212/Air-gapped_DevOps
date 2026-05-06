#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:5000/api"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_yamls")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_menu():
    print_header("🎯 YAML 관리 도구 - 메인 메뉴")
    print("\n[1] 📝 새 YAML 파일 생성 (대화형)")
    print("[2] 🔄 배치 생성 (여러 프로젝트)")
    print("[3] 🔍 저장된 YAML 검증")
    print("[4] 📂 생성된 파일 목록 보기")
    print("[5] ❌ 종료")
    print("\n" + "-" * 80)

def generate_single():
    """대화형 YAML 생성"""
    print_header("🆕 새로운 YAML 파일 생성")
    
    project_name = input("\n1️⃣  프로젝트 이름: ").strip()
    if not project_name:
        print("❌ 프로젝트 이름은 필수입니다!")
        return
    
    print("\n2️⃣  요구사항을 설명해주세요:")
    requirements = input("   > ").strip()
    if not requirements:
        print("❌ 요구사항은 필수입니다!")
        return
    
    # GitLab CI + LLM 자동 선택 (폐쇠망 환경)
    ci_type = "gitlab_ci"
    use_llm = True
    
    # 확인
    print("\n" + "-" * 80)
    print("📋 설정 요약")
    print("-" * 80)
    print(f"프로젝트: {project_name}")
    print(f"요구사항: {requirements}")
    print(f"플랫폼: GitLab CI ✅")
    print(f"LLM 사용: Yes ✅")
    
    proceed = input("\n생성할까요? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ 취소했습니다.")
        return
    
    # 생성
    print("\n⏳ YAML 생성 중...\n")
    try:
        r = requests.post(
            f'{BASE_URL}/generate-yaml',
            json={'requirements': requirements, 'ci_type': ci_type, 'use_llm': use_llm},
            timeout=120
        )
        
        if r.status_code != 200:
            print(f"❌ 생성 실패: {r.status_code}\n{r.text}")
            return
        
        yaml_content = json.loads(r.text)['yaml']
        
        # GitLab CI 고정
        filename = ".gitlab-ci.yml"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print_header("✅ YAML 생성 완료!")
        print(f"\n📄 생성된 YAML:\n")
        print(yaml_content)
        
        print("\n💾 파일 정보")
        print(f"파일명: {filename}")
        print(f"경로: {filepath}")
        print(f"크기: {len(yaml_content)} bytes")
        
        # 검증
        print("\n🔍 유효성 검사 중...\n")
        v = requests.post(
            f'{BASE_URL}/validate-yaml',
            json={'yaml': yaml_content, 'ci_type': 'auto'},
            timeout=30
        )
        
        if v.status_code == 200:
            validation = json.loads(v.text)
            if validation.get('valid'):
                print("✅ 검증 성공! (유효한 YAML)")
            else:
                print("⚠️ 검증 경고/에러:")
                if validation.get('errors'):
                    for error in validation['errors']:
                        print(f"   ❌ {error}")
                if validation.get('warnings'):
                    for warning in validation['warnings']:
                        print(f"   ⚠️ {warning}")
        
        print("=" * 80)
        
    except requests.exceptions.Timeout:
        print(f"❌ 타임아웃 (120초 초과)")
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

def generate_batch():
    """배치 생성"""
    print_header("🔄 배치 생성")
    
    requirements_list = [
        {"name": "Node.js 마이크로서비스", "req": "Node.js microservice with Jest testing, Docker build"},
        {"name": "Java Spring Boot", "req": "Java Spring Boot with Maven and SonarQube scanning"},
        {"name": "Go CLI", "req": "Go CLI application with tests and Docker build"},
    ]
    
    print(f"\n📋 기본 {len(requirements_list)}개 프로젝트로 생성합니다:\n")
    for i, r in enumerate(requirements_list, 1):
        print(f"  [{i}] {r['name']}")
    
    proceed = input("\n진행할까요? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ 취소했습니다.")
        return
    
    print("\n⏳ 배치 생성 중...\n")
    
    for idx, req in enumerate(requirements_list, 1):
        print(f"[{idx}/{len(requirements_list)}] {req['name']} 생성 중...")
        
        try:
            r = requests.post(
                f'{BASE_URL}/generate-yaml',
                json={'requirements': req['req'], 'ci_type': 'gitlab_ci', 'use_llm': True},
                timeout=120
            )
            
            if r.status_code != 200:
                print(f"  ❌ 실패: {r.status_code}")
                continue
            
            yaml_content = json.loads(r.text)['yaml']
            
            # GitLab CI 고정
            filename = ".gitlab-ci.yml"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            print(f"  ✅ 생성 완료: {filename}")
        
        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✨ 배치 생성 완료!")
    print("=" * 80)

def validate_files():
    """저장된 파일 검증"""
    print_header("🔍 저장된 YAML 파일 검증")
    
    yaml_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(('.yml', '.yaml'))])
    
    if not yaml_files:
        print("\n❌ YAML 파일이 없습니다.")
        return
    
    print(f"\n📂 {len(yaml_files)}개의 YAML 파일 발견\n")
    
    results = []
    for idx, filename in enumerate(yaml_files, 1):
        filepath = os.path.join(OUTPUT_DIR, filename)
        print(f"[{idx}/{len(yaml_files)}] {filename} 검증 중...", end=" ")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            r = requests.post(
                f'{BASE_URL}/validate-yaml',
                json={'yaml': yaml_content, 'ci_type': 'auto'},
                timeout=30
            )
            
            if r.status_code != 200:
                print(f"❌ 실패")
                results.append({"filename": filename, "status": "실패", "errors": r.text})
                continue
            
            validation = json.loads(r.text)
            
            if validation.get('valid'):
                print(f"✅ 유효함")
                results.append({"filename": filename, "status": "✅", "size": len(yaml_content)})
            else:
                print(f"⚠️ 경고")
                results.append({"filename": filename, "status": "⚠️", "size": len(yaml_content), "details": validation})
        
        except Exception as e:
            print(f"❌ 오류")
            results.append({"filename": filename, "status": "오류", "error": str(e)})
    
    print("\n" + "-" * 80)
    print("📊 검증 결과 요약")
    print("-" * 80)
    
    for result in results:
        status = result["status"]
        size_info = f" ({result.get('size', 0)} bytes)" if 'size' in result else ""
        print(f"{status} {result['filename']}{size_info}")
    
    valid_count = sum(1 for r in results if r['status'] == "✅")
    warning_count = sum(1 for r in results if r['status'] == "⚠️")
    error_count = len(results) - valid_count - warning_count
    
    print(f"\n✅ 유효: {valid_count}개")
    print(f"⚠️ 경고: {warning_count}개")
    print(f"❌ 실패: {error_count}개")
    print("=" * 80)

def list_files():
    """파일 목록"""
    print_header("📂 생성된 YAML 파일 목록")
    
    yaml_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(('.yml', '.yaml'))])
    
    if not yaml_files:
        print("\n❌ YAML 파일이 없습니다.")
        return
    
    print(f"\n총 {len(yaml_files)}개의 파일:\n")
    
    for idx, filename in enumerate(yaml_files, 1):
        filepath = os.path.join(OUTPUT_DIR, filename)
        size = os.path.getsize(filepath)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{idx}] {filename}")
        print(f"    크기: {size} bytes | 수정: {mtime}")
    
    print(f"\n📂 경로: {OUTPUT_DIR}")
    print("=" * 80)

def main():
    """메인 루프"""
    print("\n" + "=" * 80)
    print("  🚀 YAML 관리 도구")
    print("=" * 80)
    
    while True:
        print_menu()
        choice = input("선택 (1-5): ").strip()
        
        if choice == "1":
            generate_single()
        elif choice == "2":
            generate_batch()
        elif choice == "3":
            validate_files()
        elif choice == "4":
            list_files()
        elif choice == "5":
            print("\n👋 종료합니다!")
            break
        else:
            print("❌ 잘못된 선택입니다. (1-5)")
        
        input("\n계속하려면 엔터를 누르세요...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류: {str(e)}")
