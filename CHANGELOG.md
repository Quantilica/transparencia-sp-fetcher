# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Corrigido

- Coleta do histórico: os meses de março (2024, 2025 e 2026) nunca eram coletados, sem nenhum aviso e com o `sync` saindo 0: a página escreve o mês com entidade HTML (`mar&#xE7;o`), o parser antigo não a decodificava e descartava a linha. O parser novo decodifica entidades. A URL de download de cada mês passa a ser o `href` da linha como a página o publica (`/Remuneracao/downloadhistorico?id=N&f=zip`), resolvido contra a URL da página, em vez de reconstruída a partir do id; o id continua sendo extraído do `href`, e um `href` sem `f=` é usado como veio. O nome do mês é lido com as entidades HTML decodificadas (`Mar&ccedil;o` é Março) e a sondagem lê só cabeçalhos (abaixo). Meses antigos que nunca tinham sido coletados (março de 2024, 2025 e 2026, que existem na fonte) passam a ser baixados.
- Descoberta do histórico: o mês deixa de receber o id de outro. A página era lida por uma expressão regular que atravessava linhas da tabela; um mês sem link de download herdava o id da linha seguinte (setembro ficava com o arquivo de outubro, e outubro sumia). O parser agora lê a tabela linha a linha (`html.parser`): cada linha tem o seu mês e, se houver, o seu id; mês sem link fica fora do catálogo, registrado em `warning`.
- Descoberta do histórico: falha na sondagem de um mês não o tira mais do catálogo em silêncio. Só `404` (listado e ainda não publicado) e `405` que persiste na sondagem (indisponível agora) deixam o mês de fora, com `warning`; nenhum dos dois conta como erro de download. Exceção, `403`, `429`, `5xx` ou HTML no lugar do arquivo fazem o mês entrar no catálogo assim mesmo; o download decide e conta o erro, e o `sync` sai com 3 (ou 1 se nada baixou). Depois de 5 falhas seguidas a sondagem para e os meses restantes entram sem sondar, em vez de esperar o retry de dezenas de meses. A sondagem lê só cabeçalhos (`Range: bytes=0-0`, e o HEAD recusado com 405 cai num GET com `Range` cujo corpo não é lido; aceita 200 e 206), com tempo limite de 20 s e 2 tentativas próprios (o download mantém os do host): o pior caso até a parada fica em cerca de 3,5 minutos.
- Descoberta do histórico: página ilegível (`403`, `5xx`, rede), sem nenhuma linha `AAAA - Mês`, com linhas mas nenhum link de download, ou com todos os meses em `404`, levanta `DiscoveryError` (o `sync` sai 1) em vez de devolver catálogo vazio com saída 0. A falha não fica em cache no processo. Atenção: o catálogo é montado antes do download, então a falha derruba a execução inteira; `sync corrente dicionario` segue possível.
- A sondagem usa o cliente padrão do host quando ele está instalado (respeita `QUANTILICA_HTTP_*`, `QUANTILICA_SSL_VERIFY` e o bundle de CA) e, sem o host, um cliente do core com a verificação TLS lida do ambiente. Antes era um `HttpClient()` sem nada disso.

### Alterado

- A sondagem dos meses listados segue um ritmo por host (uma requisição a cada 0,5 s, uma por vez, com pausa do host inteiro num `429`), para não parecer varredura ao firewall da fonte. O número de sondagens não muda (uma por mês com link); a descoberta passa a levar 0,5 s a mais por mês sondado.
- Testes: `list_historico` ganha cobertura com transporte simulado (parser com mês sem link, `<tr>` sem fechamento, recorte realista da página, 404, 403, 429, 500, exceção de rede, HTML no lugar do arquivo, parada após falhas seguidas, página ilegível ou sem linhas, todos os meses em 404 ou 405, `href` usado como publicado, sondagem por `Range` sem ler o corpo, 405 persistente, entidade no nome do mês).

### Removido

- `TransparenciaSpClient.download_corrente`, `download_historico` e `download_dicionario`: chamavam `download_with_manifest` sem `source_id`, `dataset_id` e `producer` (e com `manifest_path=`, que não existe), isto é, `TypeError` certo na chamada real; os testes mockavam o método. Nada as usava: o download é do `sync` do host.

### Adicionado

- `lake`: o conversor passa a expor `inventory(input_dir)`, que diz à auditoria de cobertura o que cada bruto é. Os contêineres e CSVs mensais vigentes (`rar`, `historico`, `corrente`) seguem esperando Parquet; o dicionário de dados (XLSX) e o que o conversor não abre são `nao_tabular`; versão anterior de um bruto é `superado`; e os 145 Parquets de `derivados/remuneracao_AAAA-MM@...` (acervo da coleta antiga, de 2012-06 a 2024-06) são `gemeo` do contêiner do mesmo mês, que é o que o conversor lê (a contagem de linhas bate em 144 dos 145 meses; em 2018-03 o derivado vem de outra versão do contêiner, 1.085.144 linhas contra 1.078.798 do vigente, e como o lake vale só pela versão vigente ele não entra: fica no bruto como acervo). Um derivado cujo mês não tem contêiner vigente no bruto continua esperando Parquet, e a auditoria o acusa: o inventário nunca esconde um mês que só existe como derivado. Antes, a auditoria local reprovava a fonte com 146 `sem_parquet` (145 derivados e o dicionário).

## [0.2.6] - 2026-11-19

### Adicionado

- Testes: identidade do registro conferida.

### Alterado

- Piso de `quantilica-analytics` do extra `analysis` sobe para 0.15.0 (`origin_outputs`, `LakeWriter.origin_complete`).
- CI e infraestrutura alinhados ao template (fetcher-template v0.2.1).

### Corrigido

- `lake`: o build sem mudança não lê mais o bruto. Antes de qualquer acesso ao arquivo (assinatura, diretório central do ZIP, listagem do RAR), o conversor confere `origin_complete`: cada Parquet declara a lista de todas as saídas do arquivo (`origin_outputs`, os membros, listados antes da primeira gravação) e o arquivo só é pulado, sem ser aberto, quando todas existem com o sha256 atual (do sidecar, sem ler o arquivo). Uma conversão interrompida ou um membro que falha deixa a declaração incompleta e o arquivo é reaberto e o erro contado a cada build, como antes. Membro só com cabeçalho (que não gera Parquet) é conferido antes da primeira gravação, só quando é pequeno, e fica fora da lista; um membro grande sem dado só custa reabrir o arquivo. Lake gravado sem a declaração reconverte uma vez e depois pula. Os sidecars `.manifest.json` deixam de ser abertos. As contagens de `converted`/`skipped`, `force` e o bruto novo ou alterado seguem como antes.
- CI: o pyproject declara o PyPI antes do índice Quantilica (`[[tool.uv.index]]`), e o workflow perde `--index` e `--index-strategy`. Com a estratégia padrão `first-index`, o `uv sync` só consulta o índice para o que não está no PyPI (`quantilica-analytics`) e deixa de receber o 503 intermitente que o GitHub Pages devolve a caminhos inexistentes.

## [0.2.5] - 2026-11-14

### Corrigido
- Série antiga (RAR) do `remuneracao` volta a ser lida onde não há `libarchive` (como no Windows): sem ela, a conversão recorre ao executável do 7-Zip (`7z`/`7z.exe` no PATH, `%ProgramFiles%\7-Zip\7z.exe` ou o caminho de `QUANTILICA_7Z`), listando os membros com `7z l -slt -ba` e lendo cada um em streaming com `7z e -so`. A `libarchive` continua sendo a primeira opção. Código de saída diferente de zero vira erro com o stderr do 7z; o 7z sem codec RAR (o do Fedora) e a falta de ambos dão `RarUnavailableError` citando as duas saídas.

## [0.2.4] - 2026-11-14

### Corrigido
- `remuneracao`: CSV sem linha de cabeçalho (`remuneracao_2026-05`, o portal publicou os membros sem ela) não vira mais colunas com nome de dado (`a_ucena_rosa...`, `1_400_00`, `''`, `duplicated_N`). Sem cabeçalho (a primeira linha traz valores monetários ou datas), a linha é registro e as 18 colunas ganham os nomes atuais (`nome`, `cargo`, ..., `data_de_nomeacao_no_cargo`); com outra largura o membro dá erro. Arquivos com cabeçalho não mudam.

### Adicionado
- O fetcher declara os fatos da fonte (`FetcherInfo`: id canônico, apelidos, órgão, licença, página e cadência) para o registro de fetchers da Quantilica.

### Alterado
- Requer `quantilica-core>=0.19.0` (e `quantilica-cli>=0.17.0` como host).
- `FetcherInfo.licenca` passa a declarar a licença da fonte: Sem licença declarada; dados públicos pela Lei 12.527/2011 (LAI) e Decreto 8.777/2016.

## [0.2.3] - 2026-11-09

### Adicionado
- Documentação dos dados em `docs/`: página da fonte, página do dataset `remuneracao` com dicionário de todas as variáveis (por era) e esquema de referência do lake, verificados por `tests/test_docs.py`.

## [0.2.2] - 2026-11-06

### Corrigido
- A sondagem dos arquivos históricos registra em `warning` o mês e o motivo quando um arquivo está indisponível, em vez de descartá-lo sem rastro.
- CI: instala a biblioteca `libarchive` do sistema e sincroniza com o extra `rar`, para que os testes de leitura de RAR deixem de ser pulados.

## [0.2.1] - 2026-11-04

### Corrigido
- `lake`: `dicionario_remuneracao@*.xlsx` (e `leia-me`) é arquivo auxiliar, não série mensal: deixa de ser erro de período e não vira partição `ano/mes` (conta como ignorado).
- `lake`: linha com mais campos que o cabeçalho (`RemuneracaoAtivos.txt`) não derruba mais o membro: os campos excedentes são unidos, com `;`, à última coluna, sem perder nem truncar linhas, com aviso no log.

## [0.2.0] - 2026-11-04

### Adicionado
- Série antiga em RAR (jun/2012–mar/2023, 130 meses) como grupo `rar` (aliases
  `serie_antiga`, `historico_rar`): `rar_url` monta o nome com o mês por extenso
  (`Março` até 2016, `Marco` de 2017 em diante). O lake lê o RAR em streaming por
  membro via `libarchive-c` (extra `rar`), com erro claro (`RarUnavailableError`) se a
  libarchive faltar. Substitui a constante morta `DOWNLOAD_RAR_URL`.

### Corrigido
- Lake: cada membro (ZIP, RAR ou CSV solto) é um arquivo de origem próprio, com chave
  composta `arquivo__membro`; antes só o primeiro membro chegava ao lake. Leitura em
  streaming com decodificação estrita (`latin-1` no RAR; `utf-8-sig` e depois `cp1252`
  no resto), sem `errors="replace"`: byte inválido vira erro contado.
- Lake: fim do default silencioso `2024-01`. O período vem do nome; só o arquivo
  corrente (sem mês de referência no conteúdo) usa o mês do carimbo `@AAAAMMDD`. Sem
  nenhum dos dois, o arquivo não é convertido e o erro é contado. Colunas monetárias
  das eras antigas (`TOTMES_FINAL`, `TOTBRUTO`, `TOTLIQ`...) também são numéricas.
- Política de frescor volta a F2 (`HEAD_FALLBACK_GET`): `REMOTE_ONLY` (F3, para fontes sem validadores) causava re-download diário de fontes com Last-Modified/ETag, porque descartava o Last-Modified e o nome do arquivo caía em `@hoje`.
- A série histórica usa os `id` numéricos publicados na página
  (`downloadhistorico?id=71&f=zip`), não `ano`/`mes` (404 em todos os meses).
- A descoberta sonda os cabeçalhos e ignora meses ainda não publicados (404)
  ou bloqueados (405), evitando alerta diário falso.
- Sem o extra `analysis`, o comando `convert` termina com código 1 e a instrução de instalação (`quantilica install transparencia-sp --extra analysis`), sem traceback.

## [0.1.0] - 2026-11-01

### Adicionado
- Versão inicial do pacote `transparencia-sp-fetcher` (`quantilica transparencia-sp`).
- Suporte a `list`, `check`, `sync` e verificação de frescor via SDK `FetcherApp`.

- Conversor Universal Hive Parquet Lake com `DatasetSpec` em `lake.py`.

