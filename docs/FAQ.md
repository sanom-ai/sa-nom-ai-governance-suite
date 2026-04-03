# FAQ

## Is SA-NOM AI Governance Suite really open source?

Yes. The community baseline in this repository is published under AGPL-3.0-only.
See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Can I self-host it inside my own infrastructure?

Yes. The project is designed for self-managed private deployment.
You can run it locally, in Docker, or on Kubernetes.
Start with [DEPLOYMENT.md](DEPLOYMENT.md) and [KUBERNETES.md](KUBERNETES.md).

## Can I use OpenAI, Claude, or Ollama with the community baseline?

Yes. The public repository includes provider configuration paths and probe support for OpenAI, Anthropic Claude, and Ollama.
You bring your own credentials, endpoint policy, and model selection.

## Why is there a commercial license if the code is AGPL?

The open-source repository is the community baseline.
Commercial engagement is for organizations that want rollout support, quote-specific packaging, compliance tailoring, on-site enablement, dedicated support, or other non-community services and delivery scope.
See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md).

## Do I have to publish my whole company codebase if I use SA-NOM internally?

Not automatically.
AGPL obligations apply to the covered software and modifications to it, especially when a modified networked version is provided to users over a network.
If your organization is considering a modified hosted deployment, review AGPL obligations carefully with counsel.

## Can I run SA-NOM in an air-gapped or regulated environment?

Yes. The project is designed for private infrastructure, and the repository includes Helm, Kubernetes, and regulated-deployment starting points.
Use the templates in [templates/compliance/README.md](templates/compliance/README.md) and the checklist in [SECURITY_AUDIT_CHECKLIST.md](SECURITY_AUDIT_CHECKLIST.md).

## Does the community baseline include support?

Community support is documentation-first.
For commercial support, rollout help, or regulated delivery assistance, contact `sanomaiarch@gmail.com`.

## What is the fastest way to evaluate the project?

Use [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md).
It gives a short path for owner registration, delegated access setup, readiness checks, provider probing, and runtime smoke testing.

## Where should I start if startup validation fails?

Start with [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
It covers the most common owner registration, access-profile, trusted-registry, and provider configuration failures.
