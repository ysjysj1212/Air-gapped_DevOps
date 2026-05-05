#!/usr/bin/env bash
set -euo pipefail

DEFAULT_TIMEOUT_SECONDS=30
DEFAULT_NETWORK_MODE="none"
DEFAULT_MEMORY_LIMIT="512m"
DEFAULT_CPU_LIMIT="1"
DEFAULT_PIDS_LIMIT="128"
DEFAULT_PULL_POLICY="never"
ALLOWED_IMAGES="${SANDBOX_ALLOWED_IMAGES:-node:20 python:3.10}"

usage() {
  cat <<'EOF'
Usage:
  ./sandbox.sh [options] <image> <command> [args...]

Options:
  --network <none|bridge>  Docker network mode. Default: none
  --timeout <seconds>      Command timeout. Default: 30
  --memory <limit>         Container memory limit. Default: 512m
  --cpus <count>           Container CPU limit. Default: 1
  --pids-limit <count>     Container process limit. Default: 128
  --pull <never|missing|always>
                           Docker pull policy. Default: never
  -h, --help               Show help

Examples:
  ./sandbox.sh node:20 node -v
  ./sandbox.sh python:3.10 python --version
  ./sandbox.sh --network none node:20 node -e "require('dns').lookup('example.com', console.log)"

Notes:
  - Allowed images default to: node:20 python:3.10
  - Override allowed images with SANDBOX_ALLOWED_IMAGES="node:20 python:3.10 alpine:3.20"
EOF
}

fail() {
  echo "sandbox error: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed or not in PATH"
}

find_timeout_command() {
  if command -v timeout >/dev/null 2>&1; then
    echo "timeout"
    return 0
  fi

  if command -v gtimeout >/dev/null 2>&1; then
    echo "gtimeout"
    return 0
  fi

  return 1
}

is_allowed_image() {
  local image="$1"
  local allowed_image

  for allowed_image in $ALLOWED_IMAGES; do
    if [[ "$image" == "$allowed_image" ]]; then
      return 0
    fi
  done

  return 1
}

validate_network_mode() {
  case "$1" in
    none|bridge) ;;
    *) fail "unsupported network mode: $1" ;;
  esac
}

validate_pull_policy() {
  case "$1" in
    never|missing|always) ;;
    *) fail "unsupported pull policy: $1" ;;
  esac
}

network_mode="$DEFAULT_NETWORK_MODE"
timeout_seconds="$DEFAULT_TIMEOUT_SECONDS"
memory_limit="$DEFAULT_MEMORY_LIMIT"
cpu_limit="$DEFAULT_CPU_LIMIT"
pids_limit="$DEFAULT_PIDS_LIMIT"
pull_policy="$DEFAULT_PULL_POLICY"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --network)
      [[ $# -ge 2 ]] || fail "--network requires a value"
      network_mode="$2"
      shift 2
      ;;
    --timeout)
      [[ $# -ge 2 ]] || fail "--timeout requires a value"
      timeout_seconds="$2"
      shift 2
      ;;
    --memory)
      [[ $# -ge 2 ]] || fail "--memory requires a value"
      memory_limit="$2"
      shift 2
      ;;
    --cpus)
      [[ $# -ge 2 ]] || fail "--cpus requires a value"
      cpu_limit="$2"
      shift 2
      ;;
    --pids-limit)
      [[ $# -ge 2 ]] || fail "--pids-limit requires a value"
      pids_limit="$2"
      shift 2
      ;;
    --pull)
      [[ $# -ge 2 ]] || fail "--pull requires a value"
      pull_policy="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      fail "unknown option: $1"
      ;;
    *)
      break
      ;;
  esac
done

[[ $# -ge 2 ]] || {
  usage
  exit 2
}

image="$1"
shift

require_command docker
docker info >/dev/null 2>&1 || fail "Docker daemon is not running"
timeout_command="$(find_timeout_command)" || fail "timeout is not installed. On macOS, install it with: brew install coreutils"
validate_network_mode "$network_mode"
validate_pull_policy "$pull_policy"

[[ "$timeout_seconds" =~ ^[1-9][0-9]*$ ]] || fail "--timeout must be a positive integer"
[[ "$pids_limit" =~ ^[1-9][0-9]*$ ]] || fail "--pids-limit must be a positive integer"

if ! is_allowed_image "$image"; then
  fail "image '$image' is not allowed. Allowed images: $ALLOWED_IMAGES"
fi

echo "[sandbox] image=$image network=$network_mode timeout=${timeout_seconds}s pull=$pull_policy"

"$timeout_command" --preserve-status "${timeout_seconds}s" \
  docker run \
    --rm \
    --network "$network_mode" \
    --pull "$pull_policy" \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --memory "$memory_limit" \
    --cpus "$cpu_limit" \
    --pids-limit "$pids_limit" \
    "$image" \
    "$@"
