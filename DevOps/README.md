# Air-gapped DevOps PoC

폐쇄망(air-gapped)을 가정한 환경에서 GitLab CI와 Docker sandbox를 사용해 CI 명령을 안전하게 검증하는 DevOps PoC입니다.

## 목표

```text
git push
→ GitLab pipeline 자동 생성
→ GitLab Runner job 실행
→ Docker sandbox 검증
→ 성공/실패 결과 기록
```

## 구성 요소

- `docker-compose.yml`: 로컬 GitLab CE와 GitLab Runner 실행
- `sandbox.sh`: `--rm`, `--network none` 기반 Docker sandbox 실행 스크립트
- `ci-samples/`: 성공/실패 검증용 GitLab CI 샘플
- `docs/`: Runner 등록, sandbox 사용법, 검증 결과 문서

## 실행

```bash
docker compose -f DevOps/docker-compose.yml up -d
docker compose -f DevOps/docker-compose.yml ps
```

```bash
bash DevOps/sandbox.sh node:20 node -v
bash DevOps/sandbox.sh python:3.10 python --version
```

## GitLab CI 샘플

성공 검증:

```bash
cp DevOps/ci-samples/.gitlab-ci.yml /tmp/poc-ci-demo/.gitlab-ci.yml
```

네트워크 차단 실패 검증:

```bash
cp DevOps/ci-samples/failure-network-blocked.gitlab-ci.yml /tmp/poc-ci-demo/.gitlab-ci.yml
```

## 문서

- `DevOps/docs/SANDBOX.md`
- `DevOps/docs/register-runner.md`
- `DevOps/docs/VERIFICATION_SUMMARY.md`
