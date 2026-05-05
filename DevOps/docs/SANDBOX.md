# Docker Sandbox

This document covers the first PoC milestone: running untrusted validation commands in a disposable Docker container with network disabled by default.

## Goal

Prove that CI commands can be checked before GitLab CI execution in a constrained sandbox.

The sandbox uses:

- `docker run --rm`
- `--network none` by default
- `timeout`
- read-only container filesystem
- dropped Linux capabilities
- `no-new-privileges`
- CPU, memory, and process limits

## Prerequisites

```bash
docker version
docker info
docker pull node:20
docker pull python:3.10
```

On macOS, install GNU timeout if it is not already available:

```bash
brew install coreutils
```

The default pull policy is `never` so the sandbox does not unexpectedly access the network during validation.

## Success Cases

Run from the repository root:

```bash
cd DevOps
chmod +x sandbox.sh
./sandbox.sh node:20 node -v
./sandbox.sh python:3.10 python --version
./sandbox.sh --network none node:20 node -v
```

Expected result:

- The command prints the runtime version.
- The container is removed automatically after completion.

## Failure Case

Network access should fail with `--network none`:

```bash
cd DevOps
./sandbox.sh --network none node:20 node -e "require('dns').lookup('example.com', (err) => { if (err) { console.error(err.code); process.exit(1); } })"
```

Expected result:

- The command exits non-zero.
- The output includes a DNS/network failure such as `EAI_AGAIN` or `ENOTFOUND`.
- No container remains after execution.

## Command Reference

```bash
./sandbox.sh [options] <image> <command> [args...]
```

Options:

```text
--network <none|bridge>  Docker network mode. Default: none
--timeout <seconds>      Command timeout. Default: 30
--memory <limit>         Container memory limit. Default: 512m
--cpus <count>           Container CPU limit. Default: 1
--pids-limit <count>     Container process limit. Default: 128
--pull <never|missing|always>
                         Docker pull policy. Default: never
```

Allowed images default to:

```text
node:20 python:3.10
```

Override when needed:

```bash
SANDBOX_ALLOWED_IMAGES="node:20 python:3.10 alpine:3.20" ./sandbox.sh alpine:3.20 echo ok
```

## Troubleshooting

### Docker is not running

Error:

```text
sandbox error: Docker daemon is not running
```

Fix:

```bash
open -a Docker
docker info
```

### Image is missing

Error:

```text
docker: Error response from daemon: No such image
```

Fix before entering an air-gapped demo mode:

```bash
docker pull node:20
docker pull python:3.10
```

### Command times out

Increase the timeout only for the specific validation:

```bash
./sandbox.sh --timeout 60 node:20 node -v
```

### Image is blocked

Error:

```text
sandbox error: image '...' is not allowed
```

Fix:

```bash
SANDBOX_ALLOWED_IMAGES="node:20 python:3.10 <image>" ./sandbox.sh <image> <command>
```
