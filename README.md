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

### Série antiga (RAR, jun/2012–mar/2023)

O grupo `rar` baixa um RAR v4 por mês (`remuneracao_<Mês>_<AAAA>.rar`, 130 meses). Ler o
RAR na conversão exige **uma** destas opções:

1. o extra `rar` (`libarchive-c`, wheel puro) **e** a biblioteca `libarchive` do sistema
   (Fedora: `libarchive`; Debian/Ubuntu: `libarchive13`); é a primeira opção tentada;
2. o 7-Zip oficial com codec RAR (`7z`/`7z.exe` no PATH ou em `%ProgramFiles%\7-Zip`; a
   variável `QUANTILICA_7Z` aponta outro executável). Útil no Windows, onde não há
   libarchive. O `7zip` do Fedora não tem codec RAR.

Sem nenhuma das duas o `convert` não falha em silêncio: cada RAR vira um erro contado com
a instrução de instalação.

```bash
uv add 'transparencia-sp-fetcher[analysis,rar]' --index https://index.quantilica.com/simple/
```

Limitações: o servidor responde 405 a HEAD e ignora Range; a leitura é em streaming por
membro, mas o download do RAR é inteiro (~18 MB por mês em média). A libarchive não acusa RAR
com dado corrompido de forma confiável (só truncamento); confira o sha256 do manifesto.

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

## Documentação dos dados

O que o dataset contém, de onde vem, como chega ao lake e os cuidados de uso: [docs/README.md](docs/README.md).

## Licença

Distribuído sob licença MIT. Consulte [LICENSE](LICENSE) para mais detalhes.
