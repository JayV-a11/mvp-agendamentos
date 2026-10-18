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
receberão persistência e regras de negócio. `db/` já contém a base declarativa,
a construção do engine e o comando de verificação de conexão; ainda não há modelos.

## Arquitetura e comunicação

| Camada | Responsabilidade | Estado atual |
| --- | --- | --- |
| Angular | Apresentação, navegação e formulários | Componente inicial, Router e HttpClient configurados |
| FastAPI | Contratos HTTP, validação e regras de negócio | Factory, configuração de ambiente e endpoint de saúde |
| SQLAlchemy e PostgreSQL | Persistência, transações e integridade | Conexão validada e Alembic preparado; modelos e tabelas pendentes |

Frontend e backend são processos independentes. Não há chamadas entre eles neste
estágio. Na implementação dos fluxos de negócio, o Angular consumirá a API por
HttpClient; o FastAPI aplicará as regras e acessará o PostgreSQL por SQLAlchemy.
Credenciais de banco e de armazenamento privilegiadas ficarão somente no backend.

## Tecnologias

- Frontend: Angular 22, TypeScript, Router, HttpClient, Reactive Forms e CSS.
- Backend: Python 3.13, FastAPI, Pydantic, Uvicorn, SQLAlchemy 2.x, Psycopg e Alembic.
- Persistência: PostgreSQL no Supabase; Storage para fotografias quando configurado.
- Autenticação: PyJWT e pwdlib com Argon2, conforme a especificação.
- Testes: Vitest 5.0.5 no frontend; Pytest e HTTPX2 no backend.

O frontend utiliza Angular e Angular CLI 22.2.3, com versões instaladas registradas
em `frontend/package-lock.json`.
O backend utiliza FastAPI 0.143.5, Pydantic 2.14.1, pydantic-settings 2.16.0 e
Uvicorn 0.54.0. `backend/requirements.txt` declara as dependências de execução e
`requirements-dev.txt` acrescenta Pytest 9.1.1 e HTTPX2 2.13.1. As versões transitivas
estão fixadas em `backend/requirements.lock`, utilizado como arquivo de constraints.
Persistência preparada com SQLAlchemy 2.1.5, Alembic 1.20.0 e Psycopg 3.3.6
(distribuição binária para dispensar compilação local do driver).

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

`DATABASE_URL` é opcional enquanto não houver operações de banco: vazio significa
que o PostgreSQL ainda não foi configurado. Quando preenchido, deve usar o driver
`postgresql+psycopg`, com host, banco, usuário e senha. A configuração oculta o
valor em representações e mensagens de validação. O engine exige conexão SSL
(`require` por padrão; também aceita `verify-ca` ou `verify-full`) e timeout de
conexão de dez segundos. `require` criptografa o tráfego, mas não equivale à
validação da identidade do servidor por `verify-full`.

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

## Verificação manual da base

Com as dependências instaladas, abra dois terminais na raiz do repositório.
No primeiro, inicie o frontend:

```powershell
cd frontend
npm.cmd start
```

No segundo, inicie o backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

| Verificação | Resultado esperado |
| --- | --- |
| Abrir `http://localhost:4200` | Exibir o título “Agendamentos” |
| Consultar `http://127.0.0.1:8000/health` | HTTP 200 com `{"status":"ok"}` |
| Abrir `http://127.0.0.1:8000/docs` | Documentação com a operação GET /health |
| Executar os testes do frontend | Um teste de inicialização aprovado |
| Executar os testes do backend | Suíte de saúde, OpenAPI, CORS e infraestrutura aprovada, sem depender de banco |
| Executar `pip check` no ambiente virtual | Nenhuma dependência quebrada |

Os resultados da tabela são critérios para a sua execução. A resposta de saúde e
o teste do componente não demonstram que catálogo ou agendamento já funcionam.
Encerre cada servidor no respectivo terminal com `Ctrl+C`.

## Solução de problemas locais

| Problema | Procedimento |
| --- | --- |
| `node` ou `npm` não reconhecido | Use o ajuste de PATH da seção de pré-requisitos e confirme as versões |
| `py -3.13` não encontra o Python | Use o executável local indicado na instalação do backend ou instale Python 3.13 na máquina |
| PowerShell impede ativar o ambiente virtual | Execute diretamente `.venv\Scripts\python.exe`, como nos exemplos; ativação não é necessária |
| API não inicia após editar `.env` | Confira a lista JSON de `CORS_ORIGINS`, sem coringas, caminhos ou barra final; o exemplo contém as chaves aceitas |
| Frontend usa outra origem ou porta | Cadastre a origem exata em `CORS_ORIGINS` e reinicie o backend; `localhost` e `127.0.0.1` são origens diferentes |
| Porta ocupada | Encerre o servidor que você iniciou ou selecione outra porta com `--port`; atualize o CORS se mudar a origem do frontend |

CORS controla o uso da resposta pelo navegador; não autentica usuários nem bloqueia
clientes HTTP externos. A API ainda não oferece operações administrativas.

## Preparação do PostgreSQL no Supabase

Para configurar o banco em um novo ambiente, crie um projeto exclusivo deste MVP no
[Supabase Dashboard](https://supabase.com/dashboard), selecione sua organização,
informe nome, região e uma senha forte para o banco e aguarde o provisionamento.
Guarde a senha em local seguro.

Abra **Connect** no projeto e copie a URI de conexão PostgreSQL. Para a primeira
verificação em uma rede IPv4, utilize **Session pooler**, porta 5432. Conexão direta
é outra opção quando a rede alcançar o endpoint disponibilizado pelo projeto.
Copie host e usuário do painel; não deduza esses dados pela região. Consulte a
[documentação oficial de conexões](https://supabase.com/docs/guides/database/connecting-to-postgres).

Preencha somente `DATABASE_URL` em `backend/.env`. Preserve `CORS_ORIGINS` e não
sobrescreva outras configurações existentes. Troque o prefixo da URI por
`postgresql+psycopg://`, substitua o marcador de senha pela senha do banco e
codifique caracteres reservados da senha com percent-encoding. Não use API keys
no lugar da conexão PostgreSQL. O formato abaixo contém apenas marcadores:

```dotenv
DATABASE_URL='postgresql+psycopg://USUARIO:SENHA_CODIFICADA@HOST:5432/postgres'
```

Depois de configurar, na pasta `backend/`, execute:

```powershell
.\.venv\Scripts\python.exe -m app.db.check
```

Esse comando usa SQLAlchemy e Psycopg reais para executar somente `SELECT 1`.
Sucesso retorna código zero e a mensagem de conexão validada. Falhas retornam
código um com mensagem sem credenciais ou detalhes internos. A verificação não
cria tabelas, não aplica migrações e não comprova ainda as regras do agendamento.

O ambiente Alembic está em `backend/alembic/`; a conexão vem de Settings, sem URL
ou senha no `alembic.ini`. O engine não mantém pool local (`NullPool`); o ciclo
de conexão é explícito e pode usar o pooler de sessão do Supabase. Para inspecionar
o histórico sem conexão:

```powershell
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m alembic history
```

Ambos devem terminar sem revisões listadas. Ainda não há tabelas, revisões de
negócio ou SQL a executar no SQL Editor. A migração inicial será entregue em outro
incremento, após a conexão real ser validada. Testes locais da configuração e do
template Alembic não equivalem a testes de integração PostgreSQL.

## Escopo e estado atual

O MVP prevê uma única administradora e clientes sem conta. Pagamentos, notificações
automáticas, integração com WhatsApp e gestão de múltiplos profissionais estão fora
do escopo. A interface priorizará smartphones, incluindo telas de 320 px de largura.

O frontend contém somente a base técnica e um componente inicial. Não há telas de
catálogo, agendamento ou administração, dados simulados ou regras de negócio.
O backend contém configuração, estrutura em camadas, o endpoint técnico
`GET /health` e a infraestrutura inicial de conexão/migração. A conexão PostgreSQL
foi validada com `SELECT 1`, sem alterar tabelas. Modelos, tabelas, autenticação,
funcionalidades de negócio e integração do frontend com a API permanecem pendentes.
