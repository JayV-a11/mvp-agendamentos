# mvp-agendamentos

MVP web para uma trancista autônoma: catálogo público de serviços e solicitação
de horários, com administração de serviços, disponibilidade e agendamentos.
O atendimento solicitado permanece pendente até a aprovação da administradora.

O projeto utiliza arquitetura cliente-servidor em um monorepo. A interface é
mobile-first e os fluxos de negócio passam pela API.

A proposta se relaciona ao ODS 8, especialmente à meta 8.3, ao apoiar a organização
de um pequeno empreendimento autônomo. Essa contribuição é pretendida: redução de
tempo, aumento de renda e produtividade ainda não foram medidos. O sistema não
inclui indicadores financeiros ou painéis de impacto social.

## Estrutura

```text
frontend/   Aplicação Angular
backend/    API FastAPI
```

No frontend, `src/app/core/` concentra contratos, cliente HTTP e sessão; `shared/`
contém componentes, validações e formatação; `features/` reúne catálogo, solicitação,
login e administração. As rotas carregam os componentes sob demanda.

No backend, `app/api/` contém as rotas HTTP, `core/` as configurações e `schemas/`
os contratos de dados. `repositories/` consulta a persistência e `services/` aplica
as regras de autenticação, catálogo, disponibilidade, agendamentos e fotografias.
`db/` contém a base declarativa,
a construção do engine e o comando de verificação de conexão. `models/` define
administradores, serviços, horários e agendamentos. `alembic/` contém as migrações.

## Arquitetura e comunicação

| Camada | Responsabilidade | Estado atual |
| --- | --- | --- |
| Angular | Apresentação, navegação e formulários | Catálogo, solicitação, login, agenda e gerenciamento de serviços integrados |
| FastAPI | Contratos HTTP, validação e regras de negócio | Login, sessão, catálogo, horários, agendamentos e adaptador de fotos |
| SQLAlchemy e PostgreSQL | Persistência, transações e integridade | Quatro entidades de negócio e duas tabelas técnicas para sessão e limitação de tentativas |

Frontend e backend são processos independentes. HttpClient consome `/api`; no
desenvolvimento, `proxy.conf.json` encaminha essas requisições ao FastAPI em
127.0.0.1:8000, removendo o prefixo. Cookies e fotos ficam na mesma origem do
navegador. Credenciais de banco e Storage privilegiadas ficam somente no backend.

## Tecnologias

- Frontend: Angular 22, TypeScript, Router, HttpClient, Reactive Forms e CSS.
- Backend: Python 3.13, FastAPI, Pydantic, Uvicorn, SQLAlchemy 2.x, Psycopg e Alembic.
- Persistência: PostgreSQL no Supabase; Storage para fotografias quando configurado.
- Autenticação: PyJWT e pwdlib com Argon2, conforme a especificação.
- Testes: Vitest 5.0.5 com coverage V8 no frontend; Pytest e HTTPX2 no backend;
  Playwright 1.64.1 para integração real no navegador.

O frontend utiliza Angular e Angular CLI 22.2.3, com versões instaladas registradas
em `frontend/package-lock.json`.
O backend utiliza FastAPI 0.143.5, Pydantic 2.14.1, pydantic-settings 2.16.0 e
Uvicorn 0.54.0. `backend/requirements.txt` declara as dependências de execução e
`requirements-dev.txt` acrescenta Pytest 9.1.1. HTTPX2 2.13.1 atende ao Storage e aos
testes. Autenticação usa PyJWT 2.15.1 e pwdlib 0.3.1 com Argon2. Pillow 13.0.0 valida
e otimiza imagens, pois FastAPI não oferece decodificação de fotografias.
As versões transitivas
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

Inicie também o backend conforme as instruções abaixo. O frontend não usa segredos
nem exige `.env`. Com banco vazio, apresenta estados vazios; os serviços reais são
cadastrados pela administradora. Sem API, apresenta erro de conexão e permite tentar
novamente. Não há dados de catálogo ou respostas simuladas na aplicação.

Rotas: `/` (catálogo), `/agendar/:id` (solicitação), `/login`, `/admin/agenda` e
`/admin/servicos`. A administração permite criar/bloquear horários, decidir pedidos,
gerenciar serviços e fotografias. O primeiro acesso administrativo exige cadastrar
a administradora pelo comando de bootstrap documentado abaixo.

## Build e testes

Dentro de `frontend/`:

```powershell
npm.cmd run build
npm.cmd run test:run
npm.cmd run test:coverage
```

O build de produção é gerado em `frontend/dist/frontend/browser/`.
Os testes utilizam a integração nativa do Angular CLI com Vitest e jsdom.
O provedor `@vitest/coverage-v8` tem a mesma versão do Vitest. A suíte não precisa
de API, Supabase ou credenciais: utiliza HttpTestingController e fixtures apenas
nos testes unitários, sem substituir a integração real da aplicação.

### Coverage e captura do resultado dos testes Angular

`npm.cmd run test:run` executa uma vez e encerra. Para a captura do terminal,
mostre o comando e o resumo final **Test Files** e **Tests**, com os totais aprovados
e o código de saída zero. `npm.cmd run test:print` lista os nomes dos testes com
reporter verbose e também termina com esse resumo. Não é necessário iniciar
frontend/backend para executar esses comandos.

`npm.cmd run test:coverage` executa a mesma suíte e exibe percentuais de
Statements, Branches, Functions e Lines. Gera HTML, LCOV e JSON em
`frontend/coverage/frontend/`. Dentro de frontend/, abra o relatório HTML com:

```powershell
Invoke-Item .\coverage\frontend\index.html
```

A cobertura inclui todos os arquivos TypeScript de `src/app/`, inclusive rotas,
configuração, componentes e serviços; somente os próprios arquivos de teste são
excluídos. Tipos sem código executável não geram linhas instrumentadas. O bootstrap
`src/main.ts` é verificado pelo build e pelos testes de navegador. Limites mínimos:
95% de linhas, instruções e funções; 90% de ramificações. A execução falha se não
atingir esses limites. Os resultados medem execução de código e não substituem
as verificações de integração, acessibilidade ou avaliação com usuários.

Relatórios gerados, traces e capturas de teste são locais e ignorados pelo Git.
O projeto não possui ferramenta de lint semântico configurada.
Prettier 3.9.10 padroniza a formatação, sem substituir lint ou testes. Execute
`npm.cmd run format:check` para conferir e `npm.cmd run format` para formatar.

### Integração no navegador com banco isolado

O teste Playwright exercita o Angular compilado, FastAPI e PostgreSQL reais, sem
interceptar ou simular endpoints. O Pytest cria o banco temporário, uma senha
aleatória de teste e um servidor HTTP em loopback; encerra tudo ao terminar.
Serviços e contatos sintéticos existem somente nesse banco descartável. A aplicação
serve os mesmos arquivos do build; rotas internas retornam o index.html da SPA.

Pré-requisitos: build atualizado, dependências npm/Python instaladas, binários
PostgreSQL indicados anteriormente e Microsoft Edge instalado. Na raiz:

```powershell
cd frontend
npm.cmd run build
cd ..\backend
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -B -m pytest -c pyproject.toml tests/integration/test_frontend_e2e.py -q -s -W error -p no:cacheprovider --basetemp ..\.tools\pytest-e2e --postgres-bin ..\.tools\postgresql17\pgsql\bin --frontend-e2e
```

Esse comando não utiliza DATABASE_URL nem o banco Supabase. Para incluir upload e
remoção de fotos no Storage real, acrescente `--storage-external` após configurar
o bucket. Somente objetos com UUIDs exclusivos do teste são criados e removidos;
o banco continua local. Sem essa opção, o fluxo de fotos real não é executado.
O runner recusa execução direta sem a configuração de isolamento fornecida pelo
Pytest. Para usar Chrome instalado, defina `$env:E2E_BROWSER = 'chrome'` antes do
comando; o padrão é `msedge`.

O navegador usa viewport de 390 px e fuso Asia/Tokyo para verificar datas e horas
de Brasília. O fluxo cobre login inválido/válido, criação de serviços e blocos,
solicitação pendente, decisões, bloqueio, ativação, edição e logout. Também confere
rótulos, contraste, áreas de toque e viewport de 320 px. A ampliação por CSS de 200%
é uma verificação complementar, sem equivaler a teste de zoom nativo ou smartphone
físico. A avaliação com leitor de tela e a validação presencial permanecem pendentes.

Capturas reais ficam em `frontend/test-results/`, relatório em
`frontend/playwright-report/index.html` e traces são preservados em caso de falha.
Todos são ignorados pelo Git. Para abrir o relatório após a execução, use em frontend/:

```powershell
npx.cmd playwright show-report
```

O coverage do Vitest é independente desse teste: seus percentuais não incluem a
execução Playwright. O teste de navegador comprova integração funcional, enquanto
o coverage identifica os caminhos exercitados pela suíte Angular.

### Execução em produção

Publique `frontend/dist/frontend/browser/` como SPA, com fallback das rotas internas
para index.html. Encaminhe `/api/*` ao backend, removendo `/api` e preservando os
cookies e o cabeçalho Origin. `proxy.conf.json` é usado apenas por ng serve; não é
embutido no build. Configure HTTPS, CORS e cookies de produção no backend. Nenhuma
credencial privilegiada deve ser incluída no bundle Angular.

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
O padrão permite somente essa origem, credenciais, métodos utilizados pela API e
os cabeçalhos Content-Type e X-CSRF-Token. Origem desconhecida não recebe permissão.
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

Os testes sem banco cobrem a aplicação ASGI real via TestClient, configuração,
CORS, contrato OpenAPI e validação/normalização do conteúdo das fotos. Os fluxos
de negócio usam servidor Uvicorn, HTTP e PostgreSQL reais no ambiente isolado.
HTTPX2 atende à integração atual do
[TestClient do Starlette](https://www.starlette.io/testclient/).
Não há ferramenta de lint configurada no backend.

### Testes de integração PostgreSQL

Os testes em `backend/tests/integration/` criam um cluster PostgreSQL temporário,
com senha aleatória, banco exclusivo `mvp_integracao` e escuta em loopback. Aplicam
migrações reais e encerram o servidor ao terminar. Não leem `DATABASE_URL` nem
usam o projeto Supabase. O SSL desativado nesse cluster é restrito aos testes
locais; a conexão da aplicação continua exigindo SSL.

É necessário disponibilizar os executáveis `initdb` e `pg_ctl`. Os binários Windows
17.11 utilizados na validação estão em `.tools/postgresql17/pgsql/bin/`, ignorados
pelo Git e obtidos pela [página oficial de distribuição](https://www.postgresql.org/download/windows/).
Em outra máquina, informe o diretório equivalente da sua instalação PostgreSQL 17.

Dentro de `backend/`, neste ambiente Windows:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -c pyproject.toml tests -q -W error -p no:cacheprovider --basetemp ..\.tools\pytest-local --postgres-bin ..\.tools\postgresql17\pgsql\bin
```

O diretório `--basetemp` é exclusivo e descartável para testes. Sem `--postgres-bin`,
os casos de integração são explicitamente ignorados; a aprovação dos demais testes
não comprova as restrições do PostgreSQL. Para executar apenas a suíte sem banco:

```powershell
.\.venv\Scripts\python.exe -m pytest -c pyproject.toml tests -q -m "not integration"
```

A integração verifica chaves e CHECKs, campos obrigatórios, defaults, dinheiro com
Decimal, timezone, ausência de sobreposição, disputa de reservas em transações
independentes, histórico de preço/duração, duração dentro do bloco, RLS e grants.
Também compara modelos com a migração e testa upgrade/downgrade somente no cluster
temporário. Também exercita login, logout, CSRF, autorização por endpoint, IDs
alterados, tokens inválidos, catálogo, reserva, aprovação, recusa, cancelamento e
bloqueio. Concorrência por HTTP deve produzir uma reserva criada e um conflito 409.
As fotografias não são enviadas ao Supabase pela suíte isolada: a verificação
externa do Storage é independente e exige configuração explícita.

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
| Abrir `http://localhost:4200` | Exibir o catálogo real ou o estado vazio, com identidade creme/vinho |
| Consultar `http://127.0.0.1:8000/health` | HTTP 200 com `{"status":"ok"}` |
| Abrir `http://127.0.0.1:8000/docs` | Documentação das operações públicas e administrativas |
| Executar os testes do frontend | Componentes, formulários, contratos HTTP, sessão, rotas e erros aprovados |
| Executar os testes sem banco do backend | Saúde, OpenAPI, CORS e configuração aprovados |
| Executar a suíte com `--postgres-bin` | Incluir a validação de migrações e integridade no PostgreSQL temporário |
| Executar `pip check` no ambiente virtual | Nenhuma dependência quebrada |

Os resultados da tabela são critérios para a sua execução. A resposta de saúde
isolada não demonstra que catálogo ou agendamento funcionam; utilize também os
fluxos nas telas e os testes de integração descritos abaixo.
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

CORS controla o uso da resposta pelo navegador; a autenticação e a autorização
continuam sendo verificadas pelo backend em cada operação administrativa.

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

`heads` deve listar `0002_sessoes_e_limites`; `history` deve mostrar as duas revisões.
Esses comandos inspecionam os arquivos, sem consultar a versão aplicada no banco.

## Modelo de dados e migração inicial

| Tabela | Conteúdo e integridade |
| --- | --- |
| administradores | UUID, nome, email único, hash e data com timezone |
| servicos | Administradora, nome, descrição/imagem opcionais, preço e duração positivos, ativo |
| horarios_disponiveis | Administradora, início/fim com timezone, bloqueio e exclusão de sobreposição |
| agendamentos | Serviço, horário, contato, status e cópias imutáveis do preço e duração solicitados |

Cada solicitação ocupa todo o bloco do horário. A duração precisa caber no bloco;
reduzir o intervalo não pode invalidar uma reserva ativa. Edições posteriores no
serviço preservam `preco_solicitado` e `duracao_minutos_solicitada`. A API preenche
essas cópias com os valores do servidor e rejeita valores históricos no payload.

A restrição GiST usa intervalos `[início, fim)`: horários adjacentes são permitidos,
mas sobreposições da mesma administradora são rejeitadas, inclusive em transações
concorrentes. A extensão PostgreSQL `btree_gist` fornece suporte à comparação do
UUID. Um índice único parcial impede duas reservas pendentes/aprovadas no mesmo
horário. Recusa e cancelamento liberam essa unicidade, sem apagar o histórico ou
alterar automaticamente o campo de bloqueio.

A migração ativa RLS sem políticas públicas e revoga privilégios das tabelas do MVP
para PUBLIC e para as roles Supabase `anon`, `authenticated` e `service_role`, quando
existentes. A aplicação acessa os dados pelo backend; a Data API não oferece acesso
direto a essas tabelas. A API oferece filtros públicos e autorização administrativa.
O Alembic restringe autogenerate às tabelas do MVP.

O [SQL completo da revisão inicial](backend/sql/0001_modelo_inicial.sql) permite
revisar os efeitos antes de executar. Ele cria as quatro tabelas, índices,
restrições, duas funções de integridade e respectivos triggers, além de registrar
a versão Alembic. Não contém credenciais nem dados de demonstração.

Para aplicar em banco configurado e sem objetos conflitantes, dentro de `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Utilize o Alembic para aplicação; não execute também o SQL gerado sobre o mesmo
banco. Não é necessário executar SQL manualmente no painel do Supabase. Downgrade
remove tabelas e seus dados e exige autorização antes de uso fora dos testes
temporários; a extensão compartilhável `btree_gist` é preservada.

## Escopo e estado atual

O MVP prevê uma única administradora e clientes sem conta. Pagamentos, notificações
automáticas, integração com WhatsApp e gestão de múltiplos profissionais estão fora
do escopo. A interface priorizará smartphones, incluindo telas de 320 px de largura.

O frontend implementa os fluxos público e administrativo com a identidade visual
do protótipo, navegação, estados de carregamento/vazio/erro/sucesso, formulários
reativos e dados da API. Não inclui registros fictícios para demonstração.
O backend oferece autenticação e as operações obrigatórias de serviços, horários
e agendamentos. O adaptador de fotografias exige a configuração do Storage
descrita abaixo. Reagendamento (RF07) é desejável e permanece pendente.
A integração das telas foi exercitada em navegador real com banco isolado. A
avaliação presencial, a revisão em smartphone físico, a medição de desempenho
RNF03 e a implantação externa permanecem pendentes.

## Autenticação e ambiente

Dentro de `backend/`, após preencher DATABASE_URL e aplicar as migrações:

```powershell
.\.venv\Scripts\python.exe -m app.core.bootstrap segredo
.\.venv\Scripts\python.exe -m app.core.bootstrap administradora
```

O primeiro comando gera JWT_SECRET aleatório somente no `.env` e preserva um valor
já existente. O segundo solicita nome, e-mail e senha no terminal, com senha oculta
e confirmação. Exige 12 a 128 caracteres e impede criar uma segunda administradora.
Não há cadastro público, senha padrão nem dados de negócio pré-carregados.

| Variável | Uso |
| --- | --- |
| JWT_SECRET | Segredo aleatório com pelo menos 32 bytes; não versionar |
| ENVIRONMENT | development ou production |
| COOKIE_SECURE | false somente no desenvolvimento HTTP; true em produção |
| COOKIE_SAMESITE | lax por padrão; none somente com Secure e quando a topologia exigir |
| BUSINESS_TIMEZONE | America/Sao_Paulo; a API recebe datas com offset e persiste instantes |
| SUPABASE_URL | Origem HTTPS do projeto, para Storage |
| SUPABASE_SERVICE_KEY | Chave service_role somente no backend |
| STORAGE_BUCKET | fotos-servicos por padrão |

Login recebe JSON com `email` e `senha`. Retorna nome, expiração e token CSRF;
o JWT fica exclusivamente no cookie HttpOnly `agendamento_sessao`, com duração de
30 minutos. GET /auth/sessao recupera o token CSRF após recarregar a interface.
Mutações autenticadas exigem `X-CSRF-Token`; origens não autorizadas são rejeitadas.
Logout remove a sessão persistida, impedindo reutilizar o cookie encerrado.

O limite de login é de 5 tentativas por e-mail e 30 por IP em 15 minutos, incluindo
tentativas bem-sucedidas. Solicitações públicas têm limite de 20 por IP em 10
minutos. Contadores atômicos persistem no PostgreSQL entre processos; a chave é
HMAC e não armazena e-mails/IPs em texto puro. Respostas 429 incluem Retry-After.
Contadores antigos e sessões expiradas são limpos durante as operações respectivas.

A revisão [0002_sessoes_e_limites.sql](backend/sql/0002_sessoes_e_limites.sql) cria
somente as duas tabelas técnicas, índices e proteção RLS/grants. Não altera dados
das quatro entidades de negócio. Aplique com `alembic upgrade head`, sem executar
também o SQL exportado. Sessões são invalidadas se JWT_SECRET for substituído.

No frontend local, navegue em `http://localhost:4200`. HttpClient usa credenciais
somente para `/api/`; o proxy encaminha ao backend em 127.0.0.1:8000. O JWT continua
HttpOnly, enquanto os dados de sessão/CSRF ficam somente em memória, sem localStorage.
O guard restaura a sessão por cookie; o interceptor trata expiração e envia CSRF nas
mutações. Guards não substituem autorização no servidor. Logout depende da confirmação
da API; uma falha não é apresentada como sessão encerrada.
Produção exige JWT_SECRET, banco, cookie Secure e origens HTTPS explícitas.
Disponibilize a API por HTTPS no proxy da hospedagem e configure a confiança em
forwarded headers apenas para esse proxy. SameSite=None exige HTTPS e ainda está
sujeito às regras de cookies de terceiros do navegador; prefira domínios do mesmo site.

## Operações HTTP do backend

Listagens usam `limite` (1 a 100, padrão 100) e `inicio` (offset, padrão 0).
Consultas da agenda aceitam `de` inclusivo e `ate` exclusivo, com offset de timezone.
GET /publico/configuracao informa o fuso do negócio para a interface. Datas de
calendário são exibidas sem conversão de fuso; instantes usam Intl com o fuso do
servidor. O cadastro de horários converte datetime-local explicitamente nesse fuso,
sem usar o fuso do dispositivo como autoridade.

| Método e rota | Acesso e comportamento |
| --- | --- |
| POST /auth/login | Público; autentica por JSON |
| GET /auth/sessao | Sessão válida; retorna nome, expiração e CSRF |
| POST /auth/logout | Sessão + CSRF; revoga a sessão |
| GET /publico/servicos | Apenas serviços ativos |
| GET /publico/servicos/{id} | Serviço ativo selecionado |
| GET /publico/servicos/{id}/horarios | Futuros, desbloqueados, livres e com duração suficiente |
| POST /publico/agendamentos | Cria solicitação pendente; somente serviço, horário, nome e telefone |
| GET, POST /admin/servicos | Lista todos os próprios serviços ou cria um serviço |
| PUT /admin/servicos/{id} | Substitui nome, descrição, preço, duração e ativo; preserva foto e histórico |
| PUT, DELETE /admin/servicos/{id}/foto | Cadastra/substitui ou remove a foto |
| GET /admin/servicos/{id}/foto | Recupera foto própria, inclusive de serviço inativo |
| GET /publico/servicos/{id}/foto | Recupera foto otimizada de serviço ativo |
| GET, POST /admin/horarios | Consulta ou cria blocos futuros |
| PATCH /admin/horarios/{id}/bloqueio | Recebe bloqueado true/false |
| GET /admin/agendamentos | Dados de contato e agenda; filtro adicional status |
| PATCH /admin/agendamentos/{id}/status | Aprova, recusa ou cancela |

Operações administrativas exigem sessão; toda mutação exige também CSRF. IDs de
outra administradora não autorizam acesso, mesmo que sejam alterados manualmente.
O bootstrap operacional limita o MVP a uma única administradora.

Transições: pendente → aprovado, recusado ou cancelado; aprovado → cancelado.
Recusado e cancelado são finais. Repetir uma decisão retorna 409. Cancelar ou
recusar libera a reserva, preservando eventual bloqueio explícito do horário.
Bloquear um horário já ocupado preserva o atendimento existente e impede novas
solicitações. Os endpoints não alteram início/fim de um bloco já cadastrado.

Entradas inválidas retornam 422; ausência de sessão retorna 401; CSRF/origem
inválidos retornam 403; registro inexistente ou de outro proprietário retorna 404;
indisponibilidade/transição conflitante retorna 409; excesso de corpo retorna 413.
Falhas de infraestrutura retornam 503 sem SQL, conexão ou stack trace na resposta.
Não há endpoint público de consulta de contatos ou de cancelamento.

### Verificação manual de um fluxo

1. Crie a administradora pelos comandos acima e inicie a API.
2. Abra `/docs`, execute POST /auth/login e copie o `csrf_token` retornado.
3. Em operações administrativas que alteram dados, preencha o parâmetro de header
   `X-CSRF-Token` com o valor retornado. O navegador conserva o cookie definido
   pelo login; não é um bearer token para colar no campo Authorize. Alternativamente,
   use um cliente HTTP com cookie jar e esse cabeçalho.
4. Crie um serviço e um bloco futuro com duração suficiente. Confirme ambos pela API.
5. Consulte o catálogo e a disponibilidade públicos; envie nome e telefone de contato.
6. Confirme resposta pendente e ausência do bloco na disponibilidade.
7. Consulte `/admin/agendamentos`, aprove e confirme o estado atualizado.
8. Cancele; confirme liberação. Bloqueie o bloco e confirme conflito na nova solicitação.
9. Desative o serviço via PUT e confirme sua ausência no catálogo público.

Use registros de teste somente no ambiente PostgreSQL isolado. Para reproduzir o
fluxo automaticamente, execute a suíte de integração documentada acima, ou selecione
`tests/integration/test_api.py::test_fluxo_http_completo_catalogo_reserva_aprovacao_recusa_cancelamento`
com os mesmos argumentos de PostgreSQL. Ela não precisa da senha operacional.

## Fotografias no Supabase Storage

Preencha SUPABASE_URL com o Project URL de **Settings > API** e
SUPABASE_SERVICE_KEY com a chave **service_role**, na aba de chaves legadas de
**Settings > API Keys**. Use exclusivamente o `.env` do backend, sem transmitir a
chave ao frontend. A credencial é privilegiada no Storage: restrinja acesso ao
ambiente de execução. As tabelas de negócio continuam sem grants para service_role.

O comando abaixo cria o bucket **fotos-servicos** privado, com limite de 5 MB e
tipo WebP; caso exista, apenas verifica a configuração, sem alterá-lo:

```powershell
.\.venv\Scripts\python.exe -m app.services.storage_setup
```

Para aplicar esses dois limites a um bucket existente que já seja privado,
acrescente `--configure-existing`. A opção preserva os arquivos e não converte
bucket público em privado. A restrição do bucket é WebP porque os arquivos JPEG,
PNG e WebP recebidos pela API são convertidos antes de serem armazenados.

Não crie políticas para acesso anon/authenticated a esse bucket. O backend faz o
upload e recupera arquivos privados usando a chave, conforme o
[controle de acesso do Storage](https://supabase.com/docs/guides/storage/security/access-control).
Fotografias de serviços ativos são disponibilizadas pela API pública, sem revelar
essa chave. Sem configuração, upload retorna 503 e nenhuma foto é simulada.

PUT /admin/servicos/{id}/foto recebe os bytes do arquivo no corpo e Content-Type
image/jpeg, image/png ou image/webp, além de cookie e X-CSRF-Token. Não usa multipart.
Limites de entrada: 5 MB e 20 milhões de pixels. O conteúdo deve corresponder ao
MIME; SVG, executáveis e arquivos corrompidos são rejeitados. A imagem é decodificada,
orientada e regravada em WebP de até 1600×1600, sem metadados EXIF. Nomes e caminhos
do usuário não são utilizados. A resposta fornece `imagem_url` relativa à API.

Objetos recebem UUID por versão. A referência é alterada transacionalmente no
PostgreSQL; a remoção da foto anterior ocorre depois do commit. Em rollback, o
backend tenta remover o objeto novo. PostgreSQL e Storage não compartilham uma
transação distribuída: uma falha de limpeza ou interrupção do processo pode deixar
um objeto privado sem referência. O aviso operacional não contém nomes ou chaves;
nessa situação, remova o objeto sem referência pelo painel após comparar com
servicos.imagem_url. Não remova arquivos ainda referenciados. O cache público da
foto pode durar até 60 segundos após substituição ou desativação.

### Verificação externa opcional do Storage

Após configurar o bucket, dentro de `backend/`:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -c pyproject.toml tests/integration/test_storage_external.py -q -W error -p no:cacheprovider --basetemp ..\.tools\pytest-storage --postgres-bin ..\.tools\postgresql17\pgsql\bin --storage-external
```

Esse teste é explicitamente autorizado pela opção `--storage-external`. O banco
continua sendo local e temporário. Somente o Storage usa a configuração real:
arquivos sintéticos ficam em nomes UUID exclusivos e são removidos ao terminar.
O teste verifica upload, substituição, leitura, serviço inativo, remoção e bloqueio
de leitura anônima pela URL pública do Storage. A suíte padrão ignora esse teste.
