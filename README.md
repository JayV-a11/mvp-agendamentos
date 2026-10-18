# mvp-agendamentos

MVP web para uma trancista autônoma: catálogo público de serviços e solicitação
de horários, com administração de serviços, disponibilidade e agendamentos.
O atendimento solicitado permanece pendente até a aprovação da administradora.

O projeto utiliza arquitetura cliente-servidor em um monorepo. A interface será
mobile-first e os fluxos de negócio passarão pela API.

## Estrutura

```text
frontend/   Aplicação Angular
backend/    API FastAPI (a implementar)
```

No frontend, `src/app/core/` concentra infraestrutura, `shared/` recebe recursos
compartilhados e `features/` recebe os módulos funcionais conforme forem implementados.

## Tecnologias

- Frontend: Angular 22, TypeScript, Router, HttpClient, Reactive Forms e CSS.
- Backend: Python 3.13, FastAPI, Pydantic, SQLAlchemy 2.x e Alembic.
- Persistência: PostgreSQL no Supabase; Storage para fotografias quando configurado.
- Autenticação: PyJWT e pwdlib com Argon2, conforme a especificação.
- Testes: Vitest 5.0.5 no frontend; Pytest previsto para o backend.

O frontend utiliza Angular e Angular CLI 22.2.3, com versões instaladas registradas
em `frontend/package-lock.json`.
O backend e suas dependências ainda não foram inicializados.

## Pré-requisitos do frontend

- Node.js compatível com o Angular 22: `^22.22.3`, `^24.15.0` ou `>=26.0.0`.
- npm (distribuído com o Node.js).

Se `node` ou `npm` não forem reconhecidos no PowerShell e estiverem instalados no
caminho padrão do Windows, ajuste o PATH somente da sessão:

```powershell
$env:PATH = 'C:\Program Files\nodejs;' + $env:PATH
node --version
npm.cmd --version
```

## Instalação e execução local

Na raiz do repositório:

```powershell
cd frontend
npm.cmd ci
npm.cmd start
```

Acesse `http://localhost:4200`. Encerre o servidor com `Ctrl+C`.
O Angular CLI é uma dependência local; não é necessário instalá-lo globalmente.

Não são necessárias variáveis de ambiente para iniciar a base do frontend.
Não há conexão com API ou banco neste estágio. Não coloque segredos em arquivos
do frontend, pois o código distribuído ao navegador é público.

## Build e testes

Dentro de `frontend/`:

```powershell
npm.cmd run build
npm.cmd test -- --watch=false
```

O build de produção é gerado em `frontend/dist/frontend/browser/`.
Os testes utilizam a integração nativa do Angular CLI com Vitest e ambiente DOM
de testes. Ainda não há ferramenta de lint configurada.

Na raiz, verifique também a formatação do diff:

```powershell
git diff --check
```

## Escopo e estado atual

O MVP prevê uma única administradora e clientes sem conta. Pagamentos, notificações
automáticas, integração com WhatsApp e gestão de múltiplos profissionais estão fora
do escopo. A interface priorizará smartphones, incluindo telas de 320 px de largura.

O frontend contém somente a base técnica e um componente inicial. Não há telas de
catálogo, agendamento ou administração, dados simulados ou regras de negócio.
Backend, autenticação, persistência, integrações HTTP e configuração do Supabase
permanecem pendentes. Os comandos do backend serão documentados quando ele existir.
