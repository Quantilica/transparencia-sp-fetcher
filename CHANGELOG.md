# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

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

