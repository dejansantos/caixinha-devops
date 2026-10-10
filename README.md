# Caixinha DevOps

Laboratório de DevOps em que uma cópia do **Caixinha** (aplicação Django com PostgreSQL) é empacotada, testada, provisionada e operada de ponta a ponta na AWS, com foco em **aprendizado** e **segurança**.

> **Aviso:** este repositório usa uma cópia do código com **dados fictícios**. Nenhum dado real de membros, dump de banco ou `.env` de produção faz parte do projeto.

## Objetivo

Em 9 semanas, fazer o Caixinha rodar em Kubernetes na AWS com:

- Contêiner enxuto e seguro (Docker, multi-stage, usuário não-root)
- Pipeline de CI com GitHub Actions (lint, testes, build, scans de segurança)
- Infraestrutura como código com Terraform (e um exercício em CloudFormation)
- Kubernetes (k3s) com migração a partir de uma EC2 com Docker
- Automação com Ansible, scripts em Bash e Python
- GitOps com ArgoCD
- Observabilidade: métricas (Prometheus, Grafana) e logs (Loki)

## Arquitetura

> Diagrama será adicionado na Sprint 9 (`docs/arquitetura.png`).

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `app/` | Código do Caixinha (cópia com dados fictícios) e Dockerfile |
| `infra/` | Terraform (e o exemplo em CloudFormation) |
| `k8s/` | Manifests do Kubernetes sincronizados pelo ArgoCD |
| `ansible/` | Playbooks e roles de preparação e hardening da EC2 |
| `scripts/` | Scripts Bash e Python (backup, healthcheck, controle de custo) |
| `docs/` | Diário de estudo, decisões e runbooks de troubleshooting |

## Roteiro das sprints

Sprints de 1 semana, cerca de 12h cada. As datas são de 2026.

| Sprint | Período | Tema |
|---|---|---|
| 0 | 9 a 11/out | Fundação: contas, quadro Scrum, repositório limpo, proteção de segredos, dados fictícios |
| 1 | 12 a 17/out | Contêiner seguro e Linux |
| 2 | 19 a 24/out | CI com GitHub Actions |
| 3 | 26 a 31/out | Terraform e AWS (rede, EC2, RDS) |
| 4 | 2 a 7/nov | EC2 com Docker, Bash, CloudFormation e k3s |
| 5 | 9 a 14/nov | Migração de EC2 para Kubernetes, domínio e TLS |
| 6 | 16 a 21/nov | Ansible e GitOps com ArgoCD |
| 7 | 23 a 28/nov | Observabilidade: métricas e logs |
| 8 | 30/nov a 5/dez | Automação em Python e troubleshooting |
| 9 | 7 a 12/dez | Portfólio e simulados |

O acompanhamento diário está em [`docs/diario.md`](docs/diario.md).

## Segurança

Princípios aplicados em todo o projeto:

- Segredos nunca no código, na imagem ou no Git (gitleaks no pre-commit e no CI)
- Menor privilégio: sem chaves de acesso de longa duração; GitHub Actions acessa a AWS por OIDC
- Rede fechada por padrão: banco, API do Kubernetes, ArgoCD e Grafana nunca ficam públicos
- Criptografia em repouso (EBS, RDS, S3) e em trânsito (HTTPS)
- Scans: Trivy (imagens), Checkov (Terraform), pip-audit e Hadolint
- Toda mudança passa pelo Git

A seção completa de controles será detalhada na Sprint 9.

## Como rodar

> Será preenchido na Sprint 1, quando o `docker compose up` estiver funcionando.

```bash
cp .env.example .env   # preencher com valores locais, sem versionar
docker compose up
```

## Custos

O laboratório roda na AWS e é desligado ao fim de cada sessão (`terraform destroy` ou desligamento manual). O custo é conferido semanalmente no Cost Explorer. Os números finais entram no README na Sprint 9.

## Status

- [ ] Sprint 0 em andamento
