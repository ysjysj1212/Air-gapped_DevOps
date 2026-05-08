.PHONY: help copilot AutoCI install-autoci docker-up docker-down docker-logs

help:
	@echo "🚀 Air-gapped DevOps CI/CD 자동화 시스템"
	@echo ""
	@echo "명령어:"
	@echo "  make docker-up          - Docker 서비스 시작 (GitLab, Runner, App)"
	@echo "  make docker-ollama      - Ollama LLM 서비스 추가 시작"
	@echo "  make docker-down        - 모든 Docker 서비스 종료"
	@echo "  make docker-logs        - 실시간 로그 보기"
	@echo "  make install-autoci     - AutoCI 명령어를 PATH에 설치"
	@echo ""
	@echo "  make copilot \"질문\"     - LLM에 일반 질문"
	@echo "  make AutoCI \"요구사항\"  - GitLab CI YAML 자동 생성"
	@echo "  make AutoCI             - AutoCI 대화형 모드"
	@echo "  AutoCI                  - 전역 대화형 모드"
	@echo "  AutoCI \"요구사항\"       - 전역 명령처럼 바로 실행"
	@echo ""
	@echo "예제:"
	@echo "  make copilot \"Kubernetes가 뭐야?\""
	@echo "  make AutoCI \"Node.js 프로젝트, npm test 및 build 필요\""
	@echo "  AutoCI \"Python 프로젝트, pytest 필요\""

# Docker 관련 명령
docker-up:
	docker-compose up -d
	@echo "✅ 서비스 시작 완료"
	@echo "   - GitLab: http://localhost:8080"
	@echo "   - App: http://localhost:8000"
	@docker-compose ps

docker-ollama:
	docker-compose --profile ollama up -d ollama
	@echo "✅ Ollama 시작 완료"
	@echo "   - URL: http://localhost:11434"
	@sleep 30
	@curl -s http://localhost:11434/api/tags | jq . || echo "Ollama 시작 중..."

docker-down:
	docker-compose down
	@echo "✅ 서비스 종료 완료"

docker-logs:
	docker-compose logs -f

install-autoci:
	@./scripts/install-autoci.sh
	@echo "✅ AutoCI 설치 완료: $(HOME)/.local/bin/AutoCI"

# LLM CLI 명령
copilot:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "사용법: make copilot \"당신의 질문\""; \
		exit 1; \
	fi
	@python3 scripts/llm-cli.py copilot $(filter-out $@,$(MAKECMDGOALS))

AutoCI:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		python3 scripts/llm-cli.py AutoCI; \
	else \
		python3 scripts/llm-cli.py AutoCI $(filter-out $@,$(MAKECMDGOALS)); \
	fi

# 이 줄은 make가 나머지 인자를 타겟으로 해석하지 않도록 함
%:
	@:
