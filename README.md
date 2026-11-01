# transparencia-sp-fetcher

[![CI](https://github.com/Quantilica/transparencia-sp-fetcher/actions/workflows/test.yml/badge.svg)](https://github.com/Quantilica/transparencia-sp-fetcher/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Coletor e conversor Lake Hive para dados abertos de **Portal da Transparência do Estado de São Paulo** (`transparencia-sp`), parte do ecossistema [Quantilica](https://quantilica.com).

## Instalação

### Via CLI Quantilica (recomendado)

```bash
quantilica install transparencia-sp
```

Para instalar com suporte à conversão Parquet Lake:

```bash
quantilica install transparencia-sp --extra analysis
```

### Como biblioteca Python

```bash
uv add transparencia-sp-fetcher --index https://index.quantilica.com/simple/
```

Com o extra de análise analítica:

```bash
uv add 'transparencia-sp-fetcher[analysis]' --index https://index.quantilica.com/simple/
```

## Uso via CLI

```bash
# Listar conjuntos disponíveis
quantilica transparencia-sp list

# Verificar novos arquivos e frescor
quantilica transparencia-sp check

# Sincronizar arquivos para o diretório local bruto
quantilica transparencia-sp sync -o /data/transparencia-sp

# Converter acervo bruto para o Universal Hive Parquet Lake
quantilica transparencia-sp convert /data/transparencia-sp /data/lake
```

## Licença

Distribuído sob licença MIT. Consulte [LICENSE](LICENSE) para mais detalhes.
