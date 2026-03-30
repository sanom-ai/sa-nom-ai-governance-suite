# Kubernetes Support

SA-NOM now ships with a starter Helm chart and raw Kubernetes manifests for private-cluster deployment.

## Included Assets

- `helm/sa-nom-ai-governance-suite/`: Helm chart for private-server deployment.
- `k8s/`: raw manifests you can adapt directly.
- `examples/helm-values.production.example.yaml`: example values file.

## Recommended Deployment Model

- Start with one replica until runtime state is externalized safely.
- Mount `/app/_runtime` to persistent storage.
- Use Kubernetes Secrets for API tokens, trusted-registry keys, and provider credentials.
- Keep outbound egress limited to only approved model-provider endpoints.

## Helm Quick Start

```bash
helm upgrade --install sanom helm/sa-nom-ai-governance-suite   --namespace sanom   --create-namespace   -f examples/helm-values.production.example.yaml
```

## Raw Manifest Quick Start

1. Copy the example Secret and ConfigMap manifests in `k8s/`.
2. Replace every placeholder secret and URL.
3. Apply the namespace, secret, configmap, pvc, deployment, and service in that order.

## Probes

- Liveness probe: HTTP `GET /dashboard_index.html`
- Readiness probe: `python scripts/dashboard_server.py --check-only`

## Notes

- The starter chart is intentionally conservative and uses a single replica.
- If you enable PostgreSQL or Redis backends, set the related environment variables before scaling out.
