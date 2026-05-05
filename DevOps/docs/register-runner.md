# GitLab Runner Registration

This PoC uses GitLab CE and GitLab Runner with the Docker executor.

## 1. Start GitLab

```bash
cd DevOps
docker compose up -d gitlab
docker compose ps
```

GitLab can take several minutes to become ready.

Open:

```text
http://localhost:8080
```

Get the initial root password:

```bash
docker compose exec gitlab grep 'Password:' /etc/gitlab/initial_root_password
```

Login:

```text
user: root
password: <initial password>
```

## 2. Create a Runner Token

In GitLab UI:

```text
Admin Area -> CI/CD -> Runners -> New instance runner
```

Recommended runner settings:

```text
Tags: docker,sandbox
Run untagged jobs: enabled
```

Copy the runner authentication token.

## 3. Register Safe Runner

This runner proves that GitLab Runner with the Docker executor works.

It does not mount the host Docker socket, so CI jobs cannot run `docker run`.
Use it for `ci-samples/basic-success.gitlab-ci.yml`.

Start the runner container:

```bash
docker compose up -d gitlab-runner
```

Register with Docker executor:

```bash
docker compose run --rm gitlab-runner register \
  --non-interactive \
  --url "http://gitlab" \
  --token "<RUNNER_TOKEN>" \
  --executor "docker" \
  --description "poc-docker-runner-safe" \
  --docker-image "alpine:3.20" \
  --tag-list "docker,sandbox" \
  --run-untagged="true" \
  --locked="false"
```

Restart the runner:

```bash
docker compose restart gitlab-runner
docker compose logs -f gitlab-runner
```

If GitLab advertises repository URLs as `http://localhost:8080/...`, set the GitLab clone root to the internal Compose service name:

```bash
docker compose exec -T gitlab gitlab-rails runner \
  'ApplicationSetting.current_without_cache.update!(custom_http_clone_url_root: "http://gitlab")'
```

Then set the runner clone URL and Docker network so CI job containers can resolve `gitlab`:

```bash
docker compose exec gitlab-runner sh -c \
  "awk '
    /\[runners.docker\]/ { print; in_docker=1; next }
    in_docker && /^\s*network_mode = / { next }
    in_docker && /^\s*tls_verify = / { print \"    network_mode = \\\"devops_default\\\"\"; print; in_docker=0; next }
    /url = \"http:\\/\\/gitlab\"/ { print; print \"  clone_url = \\\"http://gitlab\\\"\"; next }
    { print }
  ' /etc/gitlab-runner/config.toml > /tmp/config.toml && cp /tmp/config.toml /etc/gitlab-runner/config.toml"
docker compose restart gitlab-runner
```

## 4. Optional: Register Docker Socket Runner

This is required only for the Docker-in-CI sample that runs:

```bash
docker run --rm node:20 node -v
docker run --rm --network none node:20 node -v
```

Security boundary:

```text
Mounting /var/run/docker.sock gives CI jobs control over the host Docker daemon.
Use it only for the local PoC demo, never as a production default.
```

Register a socket-enabled runner only when that risk is explicitly accepted:

```bash
docker compose run --rm gitlab-runner register \
  --non-interactive \
  --url "http://gitlab" \
  --token "<RUNNER_TOKEN>" \
  --executor "docker" \
  --description "poc-docker-runner-socket" \
  --docker-image "docker:27-cli" \
  --docker-volumes "/var/run/docker.sock:/var/run/docker.sock"
```

After registration, apply the same `custom_http_clone_url_root`, `clone_url`, and `network_mode = "devops_default"` settings so Docker-in-CI jobs can clone the repository over the internal Compose network.

The runner metadata (tags, locked state, and `run_untagged`) is managed by GitLab when you register with a runner authentication token. Configure those values when you create the runner in GitLab, not in the `gitlab-runner register` command.
Use:

```text
Description: poc-docker-runner-socket
Tags: docker-socket
Run untagged jobs: disabled
Locked: disabled
```

## 5. Run a Pipeline

Create a GitLab project and add this file as `.gitlab-ci.yml`:

```bash
cp ci-samples/basic-success.gitlab-ci.yml /path/to/project/.gitlab-ci.yml
```

This safe sample proves:

- GitLab Runner is registered.
- Docker executor jobs run.
- `node:20` and `python:3.10` runtime commands succeed.

For the socket-enabled Docker sandbox sample:

```bash
cp ci-samples/.gitlab-ci.yml /path/to/project/.gitlab-ci.yml
```

That pipeline proves:

- Docker is available inside the CI job.
- `node:20` and `python:3.10` commands can run.
- `--network none` jobs still execute local runtime commands.

Store screenshots for the PoC under:

```text
DevOps/docs/screenshots/
```

Verified local PoC results:

```text
basic-success pipeline:
- node:version -> v20.20.2
- python:version -> Python 3.10.20

docker-in-ci pipeline:
- docker run --rm node:20 node -v -> v20.20.2
- docker run --rm --network none node:20 node -v -> v20.20.2
- docker run --rm python:3.10 python --version -> Python 3.10.20
- docker run --rm --network none python:3.10 python --version -> Python 3.10.20

failure-network-blocked pipeline:
- docker run --rm --network none node:20 ... dns.lookup('example.com')
- expected evidence observed: EAI_AGAIN
```

## Troubleshooting

### GitLab is not ready

Symptoms:

```text
502
connection refused
```

Check logs:

```bash
docker compose logs -f gitlab
```

Wait until GitLab finishes bootstrapping.

### Runner cannot reach GitLab

Use the service name from the Compose network:

```text
http://gitlab
```

Do not use `localhost` inside the runner container because that points to the runner container itself.

If repository cloning still points to `http://localhost:8080/...`, confirm:

```bash
docker compose exec -T gitlab gitlab-rails runner \
  'puts ApplicationSetting.current_without_cache.custom_http_clone_url_root'
docker compose exec -T gitlab-runner grep -nE 'clone_url|network_mode' /etc/gitlab-runner/config.toml
```

Expected values:

```text
custom_http_clone_url_root = http://gitlab
clone_url = "http://gitlab"
network_mode = "devops_default"
```

### Docker command fails inside CI

If running `ci-samples/.gitlab-ci.yml`, check runner registration includes:

```text
--docker-volumes "/var/run/docker.sock:/var/run/docker.sock"
```

Then restart:

```bash
docker compose restart gitlab-runner
```

### Image pull is slow or blocked

Pre-pull demo images on the Docker host:

```bash
docker pull node:20
docker pull python:3.10
docker pull docker:27-cli
```
