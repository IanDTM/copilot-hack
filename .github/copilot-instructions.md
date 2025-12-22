# GitHub Copilot Instructions for Dev Containers

## Overview
This file provides guidance for GitHub Copilot when creating and configuring development containers.

## Dev Container Configuration

### File Structure
When creating a dev container, always create the following structure:
```
.devcontainer/
├── devcontainer.json      # Main configuration file
├── Dockerfile             # Custom Dockerfile (if needed)
└── docker-compose.yml     # Docker Compose file (if multi-container)
```

### devcontainer.json Best Practices

1. **Always ask the user for the container name** before creating a dev container. Use this name for the `name` property in devcontainer.json.

2. **Always include these core properties:**
   - `name`: A descriptive name for the dev container (provided by user)
   - `image` or `build`: Specify the base image or build configuration
   - `features`: Use dev container features for common tools
   - `customizations`: Configure VS Code extensions and settings

2. **Use official base images when possible:**
   - `mcr.microsoft.com/devcontainers/base:ubuntu`
   - `mcr.microsoft.com/devcontainers/python:3`
   - `mcr.microsoft.com/devcontainers/javascript-node:20`
   - `mcr.microsoft.com/devcontainers/typescript-node:20`
   - `mcr.microsoft.com/devcontainers/dotnet:8.0`
   - `mcr.microsoft.com/devcontainers/go:1`
   - `mcr.microsoft.com/devcontainers/rust:1`

3. **Leverage Dev Container Features:**
   - Use `ghcr.io/devcontainers/features/` for common tools
   - Examples: `git`, `docker-in-docker`, `azure-cli`, `github-cli`, `node`

4. **Port Forwarding:**
   - Define `forwardPorts` for services that need external access
   - Use `portsAttributes` to configure port labels and visibility

5. **Post-create commands:**
   - Use `postCreateCommand` for dependency installation
   - Use `postStartCommand` for services that need to run on container start
   - Use `postAttachCommand` for user-specific setup

### Example devcontainer.json Template

```json
{
  "name": "Project Dev Container",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "GitHub.copilot",
        "GitHub.copilot-chat",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "editor.formatOnSave": true
      }
    }
  },
  "forwardPorts": [],
  "postCreateCommand": "echo 'Dev container ready!'",
  "remoteUser": "vscode"
}
```

### Security Considerations

1. **Never hardcode secrets** in devcontainer.json or Dockerfile
2. Use `remoteEnv` with `localEnv` references for secrets: `"${localEnv:MY_SECRET}"`
3. Use `.env` files with `.gitignore` for local development secrets
4. Prefer `remoteUser` as non-root user (typically `vscode`)

### Performance Optimization

1. **Use named volumes** for better I/O performance on dependencies:
   ```json
   "mounts": [
     "source=node_modules,target=${containerWorkspaceFolder}/node_modules,type=volume"
   ]
   ```

2. **Cache package manager directories:**
   - npm: `/home/vscode/.npm`
   - pip: `/home/vscode/.cache/pip`
   - Go: `/go/pkg`

3. **Use `.devcontainer/Dockerfile`** for complex builds to leverage Docker layer caching

### Multi-Container Setup

When the project requires multiple services (database, cache, etc.):

1. Create a `docker-compose.yml` in `.devcontainer/`
2. Reference it in `devcontainer.json`:
   ```json
   {
     "dockerComposeFile": "docker-compose.yml",
     "service": "app",
     "workspaceFolder": "/workspace"
   }
   ```

### Common Features Reference

| Feature | Purpose |
|---------|---------|
| `ghcr.io/devcontainers/features/docker-in-docker:2` | Run Docker inside container |
| `ghcr.io/devcontainers/features/azure-cli:1` | Azure CLI tools |
| `ghcr.io/devcontainers/features/github-cli:1` | GitHub CLI |
| `ghcr.io/devcontainers/features/python:1` | Python runtime |
| `ghcr.io/devcontainers/features/node:1` | Node.js runtime |
| `ghcr.io/devcontainers/features/dotnet:2` | .NET SDK |
| `ghcr.io/devcontainers/features/go:1` | Go runtime |
| `ghcr.io/devcontainers/features/rust:1` | Rust toolchain |
| `ghcr.io/devcontainers/features/kubectl-helm-minikube:1` | Kubernetes tools |
| `ghcr.io/devcontainers/features/terraform:1` | Terraform CLI |

### Troubleshooting

1. **Rebuild container** after changes to devcontainer.json or Dockerfile
2. Check container logs if startup fails
3. Verify volume mounts and file permissions
4. Ensure required ports are not already in use on host

## Language-Specific Guidelines

### Node.js Projects
- Use `mcr.microsoft.com/devcontainers/javascript-node` or `typescript-node`
- Mount `node_modules` as volume for performance
- Include ESLint and Prettier extensions

### Python Projects
- **Ask the user which Python version they want to use.** Available versions:
  - `python:3.13` - Latest (December 2024)
  - `python:3.12` - Recommended for most projects (best compatibility)
  - `python:3.11` - Stable
  - `python:3.10` - Stable
  - `python:3` - Floating tag, always latest 3.x
- Use `mcr.microsoft.com/devcontainers/python:<version>` with the user's chosen version
- Include Python and Pylance extensions
- **Always enable Python debugging** by including the `ms-python.debugpy` extension
- **Always use UV as the package manager** - install in `postCreateCommand`:
  ```json
  "postCreateCommand": "pip install uv && uv sync"
  ```
- **Always install Ruff** for linting and formatting:
  ```json
  "postCreateCommand": "pip install uv ruff && uv sync"
  ```
- Include a `.vscode/launch.json` with Python debug configurations:
  ```json
  {
    "version": "0.2.0",
    "configurations": [
      {
        "name": "Python: Current File",
        "type": "debugpy",
        "request": "launch",
        "program": "${file}",
        "console": "integratedTerminal"
      }
    ]
  }
  ```
- Required VS Code extensions for Python dev containers:
  ```json
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.debugpy",
        "charliermarsh.ruff"
      ]
    }
  }
  ```
- Configure Ruff as the default formatter and linter in VS Code settings:
  ```json
  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": ".venv/bin/python",
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.formatOnSave": true
        },
        "python.analysis.typeCheckingMode": "basic"
      }
    }
  }
  ```

### .NET Projects
- Use `mcr.microsoft.com/devcontainers/dotnet`
- Include C# Dev Kit extension
- Configure OmniSharp settings if needed

### Go Projects
- Use `mcr.microsoft.com/devcontainers/go`
- Include Go extension
- Mount Go module cache for performance
