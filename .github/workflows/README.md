# GitHub Automation Policy

This repository uses three GitHub Actions workflows.

## DevOps Policy

`devops-policy.yml` runs on feature branch pushes and pull requests into `main`, `master`, `devops`, or `feat/setup-project-structure`.

It checks:

- Python dependencies install successfully from `DevOps/requirements.txt`
- Installed Python packages have no dependency conflicts through `pip check`
- Tests pass with `pytest DevOps/tests/`
- YAML files pass `yamllint`
- Branch names follow the owner/work-item convention
- Commit subjects follow Conventional Commits

Branch name format:

```text
DevOps/<work-item>
AI/<work-item>
```

Use `DevOps/` for infrastructure and execution-environment work.
Use `AI/` for API, LLM, template generation, and validation logic work.
The `<work-item>` segment must be non-empty and must not contain spaces or another slash.

Commit message format:

```text
type(scope): subject
```

Allowed types:

```text
feat, fix, docs, style, refactor, test, chore
```

Type meanings:

```text
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅, 세미콜론 누락, 코드 변경이 없는 경우
refactor: 코드 리팩토링
test: 테스트 코드, 리팩토링 테스트 코드 추가
chore: 빌드 업무 수정, 패키지 매니저 수정
```

Examples:

```text
feat(sandbox): add isolated docker runner
fix(api): handle missing project description
docs(readme): update quickstart guide
```

## Auto Merge

`auto-merge.yml` runs after `DevOps Policy` succeeds for a pull request.

It attempts to:

- Auto-merge non-draft PRs targeting `main`, `master`, `devops`, or the repository default branch
- Only merge branches from the same repository
- Only merge branch names matching `DevOps/<work-item>` or `AI/<work-item>`
- Squash merge the PR
- Delete the source branch after merge

Repository settings still need to allow this automation:

- Enable `Allow auto-merge`
- Enable `Automatically delete head branches`
- Add branch protection requiring the `DevOps Policy` check before merge
- Allow GitHub Actions to create and approve pull requests if your organization restricts it

## Create Pull Request

`create-pr.yml` runs after `DevOps Policy` succeeds for a feature branch push.

It attempts to:

- Ignore pushes to `main` and `master`
- Only open PRs for `DevOps/<work-item>` or `AI/<work-item>` branches
- Skip PR creation when an open PR already exists
- Open the PR into the repository default branch
