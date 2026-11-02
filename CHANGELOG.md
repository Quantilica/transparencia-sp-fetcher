# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Corrigido
- A série histórica usa os `id` numéricos publicados na página
  (`downloadhistorico?id=71&f=zip`), não `ano`/`mes` (404 em todos os meses).
- A descoberta sonda os cabeçalhos e ignora meses ainda não publicados (404)
  ou bloqueados (405), evitando alerta diário falso.

## [0.1.0] - 2026-11-01

### Adicionado
- Versão inicial do pacote `transparencia-sp-fetcher` (`quantilica transparencia-sp`).
- Suporte a `list`, `check`, `sync` e verificação de frescor via SDK `FetcherApp`.

- Conversor Universal Hive Parquet Lake com `DatasetSpec` em `lake.py`.

