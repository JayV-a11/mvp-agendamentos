# mvp-agendamentos

MVP web para uma trancista autônoma: catálogo público de serviços e solicitação
de horários, com administração de serviços, disponibilidade e agendamentos.
O atendimento solicitado permanece pendente até a aprovação da administradora.

O projeto utiliza arquitetura cliente-servidor em um monorepo. A interface será
mobile-first e os fluxos de negócio passarão pela API.

## Estrutura

```text
frontend/   Aplicação Angular
backend/    API FastAPI
```

No frontend, `src/app/core/` concentra infraestrutura, `shared/` recebe recursos
compartilhados e `features/` recebe os módulos funcionais conforme forem implementados.

No backend, `app/api/` contém as rotas HTTP, `core/` as configurações e `schemas/`
os contratos de dados. As pastas `models/`, `repositories/`, `services/` e `db/`
estão reservadas para persistência e regras de negócio futuras.

## Tecnologias

- Frontend: Angular 22, TypeScript, Router, HttpClient, Reactive Forms e CSS.
- Backend: Python 3.13, FastAPI, Pydantic e Uvicorn; SQLAlchemy 2.x e Alembic previstos.
- Persistência: PostgreSQL no Supabase; Storage para fotografias quando configurado.
- Autenticação: PyJWT e pwdlib com Argon2, conforme a especificação.
- Testes: Vitest 5.0.5 no frontend; Pytest e HTTPX2 no backend.

O frontend utiliza Angular e Angular CLI 22.2.3, com versões instaladas registradas
em `frontend/package-lock.json`.
O backend utiliza FastAPI 0.143.5, Pydantic 2.14.1, pydantic-settings 2.16.0 e
Uvicorn 0.54.0. `backend/requirements.txt` declara as dependências de execução e
`requirements-dev.txt` acrescenta Pytest 9.1.1 e HTTPX2 2.13.1. As versões transitivas
estão fixadas em `backend/requirements.lock`, utilizado como arquivo de constraints.

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

## Instalação e execução do frontend

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

## Instalação e execução do backend

Pré-requisito: Python 3.13, com suporte a `venv` e pip. No Windows, verifique com
`py -3.13 --version`. A instalação local deste ambiente utiliza Python 3.13.16 em
`.tools/python313/`, que não é versionado. Em outra máquina, instale o Python 3.13
pelo [site oficial](https://www.python.org/downloads/release/python-31316/).

Na raiz do repositório, em PowerShell:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c requirements.lock
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Se o launcher `py` não encontrar a instalação local deste ambiente, substitua
somente o comando de criação do ambiente virtual por:

```powershell
..\.tools\python313\python.exe -m venv .venv
```

Não é necessário ativar o ambiente virtual. Encerre o servidor com `Ctrl+C`.
Copie `.env.example` apenas na primeira configuração; preserve um `.env` já existente.
Para instalar apenas as dependências de execução, use `requirements.txt` no lugar
de `requirements-dev.txt`.

O `.env` é lido a partir da pasta `backend/`; variáveis de ambiente têm prioridade.
`CORS_ORIGINS` recebe uma lista JSON de origens explícitas, por exemplo
`["http://localhost:4200"]`. Não use coringa, barra final, caminhos ou credenciais.
O padrão permite somente essa origem, o método GET e requisições sem cookies.
A autenticação e a política de cookies serão implementadas em etapa própria.
O arquivo `.env` é local e não deve conter valores sensíveis versionados.

Verifique a API em outro terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

O resultado esperado é `{"status":"ok"}`. Esse endpoint indica somente que a
aplicação HTTP está respondendo; não verifica banco ou serviços externos.
A documentação local da API está em `http://127.0.0.1:8000/docs`.

Para testar, dentro de `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Os testes usam a aplicação ASGI real via TestClient, sem banco ou serviços
simulados. Cobrem saúde da API, contrato OpenAPI, CORS e validação de configuração.
HTTPX2 atende à integração atual do
[TestClient do Starlette](https://www.starlette.io/testclient/).
Não há ferramenta de lint configurada no backend.

## Escopo e estado atual

O MVP prevê uma única administradora e clientes sem conta. Pagamentos, notificações
automáticas, integração com WhatsApp e gestão de múltiplos profissionais estão fora
do escopo. A interface priorizará smartphones, incluindo telas de 320 px de largura.

O frontend contém somente a base técnica e um componente inicial. Não há telas de
catálogo, agendamento ou administração, dados simulados ou regras de negócio.
O backend contém apenas configuração, estrutura em camadas e o endpoint técnico
`GET /health`. Autenticação, persistência, funcionalidades de negócio, integração
do frontend com a API e configuração do Supabase permanecem pendentes.
