import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

# 생성된 YAML을 저장할 디렉토리
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_yamls")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 여러 요구사항들
requirements = [
    {
        "name": "Node.js 마이크로서비스",
        "requirements": "Node.js microservice with Jest testing, Docker build, and production deployment",
        "ci_type": "github_actions"
    },
    {
        "name": "Java Spring Boot",
        "requirements": "Java Spring Boot application with Maven, SonarQube scanning, and Kubernetes deployment",
        "ci_type": "gitlab_ci"
    },
    {
        "name": "Go CLI 애플리케이션",
        "requirements": "Go CLI application with unit tests, Docker containerization, and binary release",
        "ci_type": "github_actions"
    },
    {
        "name": "Python FastAPI",
        "requirements": "Python FastAPI with async tests, PostgreSQL database, Redis caching, and AWS Lambda deployment",
        "ci_type": "github_actions"
    },
    {
        "name": "Rust 시스템 프로그램",
        "requirements": "Rust system program with cargo tests, cross-platform builds for Linux and Windows, and security audit",
        "ci_type": "gitlab_ci"
    }
]

print("=" * 80)
print("🚀 YAML 자동 생성 및 검증 시작!")
print("=" * 80)

results = []

for idx, req_info in enumerate(requirements, 1):
    print(f"\n[{idx}/{len(requirements)}] {req_info['name']} 생성 중...")
    
    try:
        # YAML 생성
        r = requests.post(
            f'{BASE_URL}/generate-yaml',
            json={
                'requirements': req_info['requirements'],
                'ci_type': req_info['ci_type'],
                'use_llm': True
            },
            timeout=120
        )
        
        if r.status_code != 200:
            print(f"❌ 생성 실패: {r.status_code}")
            print(f"   응답: {r.text}")
            continue
        
        yaml_content = json.loads(r.text)['yaml']
        
        print(f"✅ YAML 생성 완료!")
        print(f"\n--- {req_info['name']} YAML ---")
        print(yaml_content)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{req_info['name'].replace(' ', '_')}.yml"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"\n💾 저장 완료: {filepath}")
        
        # YAML 검증
        print(f"\n🔍 검증 중...")
        v = requests.post(
            f'{BASE_URL}/validate-yaml',
            json={'yaml': yaml_content, 'ci_type': 'auto'},
            timeout=30
        )
        
        if v.status_code == 200:
            validation = json.loads(v.text)
            if validation.get('valid'):
                print(f"✅ 검증 성공!")
                results.append({
                    "name": req_info['name'],
                    "status": "성공",
                    "yaml": yaml_content,
                    "validation": validation,
                    "filepath": filepath
                })
            else:
                print(f"⚠️ 검증 경고:")
                print(f"   {validation.get('errors', [])}")
                results.append({
                    "name": req_info['name'],
                    "status": "경고",
                    "yaml": yaml_content,
                    "validation": validation,
                    "filepath": filepath
                })
        else:
            print(f"❌ 검증 실패: {v.status_code}")
            results.append({
                "name": req_info['name'],
                "status": "검증 실패",
                "yaml": yaml_content,
                "filepath": filepath
            })
        
        print("\n" + "-" * 80)
        
    except requests.exceptions.Timeout:
        print(f"❌ 타임아웃 (120초 초과)")
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

# 최종 요약
print("\n" + "=" * 80)
print("📊 최종 요약")
print("=" * 80)

for result in results:
    status_icon = "✅" if result['status'] == "성공" else "⚠️" if result['status'] == "경고" else "❌"
    print(f"{status_icon} {result['name']}: {result['status']}")
    if 'filepath' in result:
        print(f"   📁 {result['filepath']}")

print(f"\n✨ 총 {len(requirements)}개 중 {len([r for r in results if r['status'] in ['성공', '경고']])}개 생성 완료!")
print(f"📂 저장 경로: {os.path.abspath(OUTPUT_DIR)}")
print("=" * 80)
