# mvp-agendamentos

MVP web para uma trancista autônoma: catálogo público de serviços e solicitação
de horários, com administração de serviços, disponibilidade e agendamentos.
O atendimento solicitado permanece pendente até a aprovação da administradora.

O desenvolvimento é incremental. Este repositório ainda não contém uma aplicação
executável; o primeiro incremento prepara somente a estrutura e as regras do projeto.

## Estrutura

```text
frontend/   Aplicação Angular (a inicializar no próximo incremento autorizado)
backend/    API FastAPI (a inicializar em incremento próprio)
docs/       Requisitos, protocolo e documentação técnica
```

Os arquivos `.gitkeep` mantêm os diretórios vazios no Git até a criação dos projetos.

## Stack prevista

- Frontend: Angular 22, TypeScript, Router, HttpClient, Reactive Forms e CSS.
- Backend: Python 3.13, FastAPI, Pydantic, SQLAlchemy 2.x e Alembic.
- Persistência: PostgreSQL no Supabase; Storage para fotografias quando configurado.
- Autenticação: PyJWT e pwdlib com Argon2, conforme a especificação.
- Testes: Pytest e Vitest 5.0, com compatibilidade a confirmar antes da instalação.

As versões efetivas das dependências serão registradas nos respectivos incrementos.
Não há dependências instaladas ou arquivos de ambiente necessários nesta entrega.

## Requisitos e protocolo

- [Especificação mestra](docs/PROJECT_SPEC.md).
- [Protocolo incremental e padrão de commits em pt-BR](docs/DEVELOPMENT_PROTOCOL.md).
- [Análise inicial do ambiente](docs/ENVIRONMENT.md).

O protocolo e a padronização em pt-BR substituem as instruções anteriores sobre
commits automáticos e os exemplos de mensagens em inglês da especificação.
O usuário revisa, testa e realiza cada commit antes de autorizar outro incremento.

## Escopo e estado atual

O MVP prevê uma única administradora e clientes sem conta. Pagamentos, notificações
automáticas, integração com WhatsApp e gestão de múltiplos profissionais estão fora
do escopo. A interface será mobile-first, conforme a referência Figma da especificação.

Concluído neste incremento: diretórios, regras de arquivos ignorados, configuração
de edição e registro das instruções fornecidas. Angular, FastAPI, banco,
autenticação, funcionalidades de negócio e testes de aplicação estão pendentes.

Os procedimentos de instalação, execução local e testes de cada aplicação serão
adicionados quando os respectivos projetos existirem. O Supabase não será
configurado na Etapa 1. Não inserir credenciais no código ou na documentação.

## Verificação desta entrega

Na raiz do repositório, em PowerShell:

```powershell
git diff --check
git status --short
git diff -- README.md
git ls-files --others --exclude-standard
git check-ignore --no-index frontend/node_modules/exemplo backend/.venv/exemplo backend/.env frontend/.env.local
git check-ignore --no-index backend/.env.example frontend/.env.example
```

O primeiro comando não deve emitir erros. A consulta de ignorados deve listar
dependências e ambientes locais. A última consulta não deve listar os arquivos
`.env.example` e deve retornar código 1, pois esses exemplos precisam ser versionáveis.
Não há build, servidor ou suíte de testes de aplicação neste incremento.
