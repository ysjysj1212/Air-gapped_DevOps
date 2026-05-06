# Verification Summary

This document records the current PoC verification state for the DevOps-owned GitLab and Docker sandbox work.

## GitHub Verification

GitHub PR and Actions validation completed:

```text
PR #5: DevOps/docker-sandbox-poc
Status: merged
Merge commit: ef9e9a9

PR #8: DevOps/gitlab-verify
Status: merged
Merged at: 2026-05-06T03:37:27Z
```

Both PRs passed the `DevOps Policy` workflow before merge.

## GitLab Runtime

GitLab CE and GitLab Runner are running through Docker Compose:

```bash
docker compose -f DevOps/docker-compose.yml ps
```

Verified services:

```text
poc-gitlab: healthy, http://localhost:8080
poc-gitlab-runner: running
```

GitLab web readiness check:

```bash
curl -I http://localhost:8080/users/sign_in
```

Expected result:

```text
HTTP/1.1 200 OK
```

## Runner Fixes

The safe Docker executor runner is registered:

```text
description: poc-docker-runner-safe
tags: docker,sandbox
executor: docker
```

The socket-enabled Docker runner is registered for Docker-in-CI jobs:

```text
description: poc-docker-runner-socket
tag: docker-socket
image: docker:27-cli
volume: /var/run/docker.sock:/var/run/docker.sock
```

Required clone/network fixes:

```text
GitLab custom clone root: http://gitlab
runner clone_url: http://gitlab
runner network_mode: devops_default
```

## Pipeline Results

Project:

```text
root/poc-ci-demo
```

The final `.gitlab-ci.yml` state was restored to:

```text
DevOps/ci-samples/.gitlab-ci.yml
```

Final verified pipeline:

```text
pipeline: #4
status: success
commit: 1b70bbf5b416b70a4c771fc0eb466c74720a2fa5
jobs:
  sandbox:node=success
  sandbox:python=success
```

Verified Docker-in-CI commands:

```bash
docker run --rm node:20 node -v
docker run --rm --network none node:20 node -v
docker run --rm python:3.10 python --version
docker run --rm --network none python:3.10 python --version
```

Observed versions:

```text
node: v20.20.2
python: Python 3.10.20
```

## Failure Evidence

The network-blocked sample was executed before restoring the final CI state:

```text
DevOps/ci-samples/failure-network-blocked.gitlab-ci.yml
```

Expected failure evidence was observed:

```text
docker run --rm --network none node:20 ...
dns.lookup('example.com')
output: EAI_AGAIN
```

The failure job is allowed to fail in the sample so the pipeline can complete while still preserving the blocked-network evidence.

## Screenshot Checklist

Store screenshots under:

```text
DevOps/docs/screenshots/
```

Recommended captures:

```text
GitLab root/poc-ci-demo pipeline #4 success
sandbox:node job trace
sandbox:python job trace
sandbox:network-blocked job trace showing EAI_AGAIN
GitHub PR #5 merged
GitHub PR #8 merged
```
