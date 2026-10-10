# Diário de estudo – Caixinha DevOps

Registro de cada sessão. Regras:

- **Daily** (5 min, no início): o que fiz, o que farei, o que me trava.
- **Fechamento** (10 min, no fim): o que aprendi, por que escolhi assim, o que quebrou, uma pergunta de entrevista.
- **Sábado**: Sprint Review (o que demonstrei, custo da semana) e Retrospectiva (1 coisa a manter, 1 a mudar).
- Nunca escrever senhas, chaves ou dados reais aqui.

## Modelo de entrada

```markdown
### AAAA-MM-DD – Sprint N

**Daily**
- Fiz:
- Farei:
- Me trava:

**Fechamento**
- Aprendi:
- Por que escolhi assim:
- O que quebrou (e como resolvi):
- Pergunta de entrevista que consigo responder agora:
- Recursos AWS desligados? Custo do dia: 
```

---

## Sprint 0 – Fundação (9 a 11/out)

**Objetivo:** deixar a base pronta e segura para a Sprint 1.

### 2026-10-09 – Sprint 0

**Daily**
- Fiz: montei o plano Scrum e o ajustei para cobrir tudo que a vaga de DevOps pede (v2, 9 sprints).
- Farei: contas protegidas (2FA/MFA e AWS Budgets), quadro no GitHub Projects, repositório limpo, gitleaks no pre-commit, `seed_demo` com dados fictícios, primeiro push.
- Me trava: nada até agora.

**Fechamento**
- Aprendi:
  - Git local x GitHub: o repositório local é privado; publicar é o ponto sem volta, então as proteções vêm antes.
  - `.gitignore` com exceção (`!.env.example`) e como testar com um `.env` falso.
  - gitleaks na mão (`gitleaks detect`) e automático no commit via pre-commit.
  - E-mail noreply do GitHub nos commits, para não expor o e-mail pessoal num repositório público.
  - Na AWS, instância EC2 "interrompida" não cobra computação, mas RDS ligado cobra por hora mesmo sem uso; RDS parado volta sozinho em 7 dias.
  - Proteção contra exclusão do RDS deixa "Excluir" desabilitado até ser desligada.
- Por que escolhi assim:
  - Git local primeiro, GitHub depois de gitleaks limpo, para nunca publicar segredo.
  - Copiei só `caixinha_project/`, `core/`, `manage.py` e `requirements.txt` (sem `.env`, `dados.txt`, Dockerfile e compose antigos) para escrever o Dockerfile do zero na Sprint 1.
  - Excluí o RDS e a EC2 de estudos antigos em vez de só parar, porque parar não elimina o custo.
- O que quebrou (e como resolvi):
  - `.gitignore` saiu com a palavra `gitignore` solta na linha 1 (sobra de copiar o bloco); apaguei a linha.
  - `gitleaks` não era reconhecido logo após instalar; abri um PowerShell novo.
  - `robocopy` deixou pastas `app/app` duplicadas; removi antes do commit.
  - Achei um `dados.txt` com usuário e senha em texto puro no projeto original; não copiei. **Pendência:** apagar o arquivo original e trocar a senha, se ainda for usada.
  - Fiz o push antes de ativar o 2FA; o gitleaks no histórico passou, mas a ordem correta é proteger a conta antes.
- Pergunta de entrevista que consigo responder agora:
  - Por que não publicar o repositório antes de rodar o gitleaks? Porque o histórico do Git guarda tudo; apagar o arquivo depois não remove o segredo do histórico.
- Recursos AWS desligados? Custo do dia:
  - Excluídos em Ohio (us-east-2): RDS `meu-database-1` e EC2 `servidor-01`; sem volumes, snapshots, IPs elásticos, chaves KMS próprias ou buckets S3 restantes. Glue não confirmado.
  - Gasto antes da limpeza: US$ 4,11 no mês (1 a 9/out), previsão US$ 14,64; fatura em US$ 0,00 (créditos). Conferir o Cost Explorer em 1 ou 2 dias.

**Concluído na Sprint 0**
- [x] 2FA no GitHub; MFA no root e no IAM da AWS (informado); orçamento de US$ 10 no AWS Budgets
- [x] Repositório local com `.gitignore`, `.env.example`, pre-commit com gitleaks
- [x] Código do Caixinha copiado sem dados reais e publicado em github.com/dejansantos/caixinha-devops
- [ ] Quadro no GitHub Projects com uma issue por história do backlog
- [ ] Comando `seed_demo` com Faker
- [ ] Conferir Glue e o Cost Explorer; apagar o `dados.txt` original e trocar a senha

---

## Sprint 1 – Contêiner seguro e Linux (12 a 17/out)

_Sem entradas ainda._

## Sprint Review e Retrospectiva

| Sprint | Demonstrei | Custo da semana | Manter | Mudar |
|---|---|---|---|---|
| 0 |  |  |  |  |
| 1 |  |  |  |  |
