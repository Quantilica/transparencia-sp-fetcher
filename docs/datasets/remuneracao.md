---
dataset:
  id: remuneracao
  fonte: transparencia-sp
  titulo: Remuneração dos servidores públicos do Estado de São Paulo
  resumo: Relação nominal e remuneração mensal dos servidores, aposentados e pensionistas do Estado de São Paulo, uma linha por pessoa e mês, com as parcelas da remuneração.
  orgao: Portal da Transparência do Estado de São Paulo (Controladoria Geral do Estado)
  pagina_oficial: https://www.transparencia.sp.gov.br/Remuneracao
  licenca: "O rodapé do portal mostra 'Todos os direitos reservados' e um link para a Licença Creative Commons 4.0 (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/deed.pt-br); a página de remuneração não detalha termos de uso (conferido em 2026-11-09)"
  periodicidade: mensal (a página não informa calendário de atualização)
  cobertura: {inicio: 2012-06, fim: em-curso}
  unidade: um servidor, aposentado ou pensionista em um mês
  granularidade: {espacial: órgão/entidade de lotação (texto livre), temporal: mês}
  formato_bruto: "três formas: RAR por mês (2012-06 a 2023-03; CSV Latin-1, ponto e vírgula, vírgula decimal, textos entre aspas), ZIP por mês (2023-04 em diante; CSV, ponto e vírgula, milhar com ponto e vírgula decimal) e CSV consolidado corrente (UTF-8 com BOM)"
  lake: {estado: convertido, particoes: [ano, mes], chave: [], colunas: 32}
  unidades_de_medida:
    totdomes: R$
    totbruto: R$
    totliq: R$
    remuneracao_do_mes: R$
    ferias_e_13o_salario: R$
    pagamentos_eventuais: R$
    licenca_premio_indenizada: R$
    abono_permanencia_outras_indenizacoes: R$
    redutor_salarial: R$
    total_liquido_r: R$
    remuneracao: R$
    ferias_13o: R$
    licenca_premio: R$
    abono_permanencia: R$
    redutor: R$
    rendimento_liquido: R$
  dados_pessoais:
    - {coluna: nome, categoria: "nome completo do servidor"}
    - {coluna: cpf, categoria: "CPF, parcialmente mascarado pela fonte (só no arquivo corrente)"}
    - {coluna: data_de_ingresso, categoria: "data de ingresso no serviço público, associada ao nome"}
    - {coluna: data_de_nomeacao_no_cargo, categoria: "data de nomeação, associada ao nome"}
    - {coluna: ingresso, categoria: "data de ingresso no serviço público, associada ao nome"}
    - {coluna: nomeacao, categoria: "data de nomeação, associada ao nome"}
    - {coluna: remuneracao_do_mes, categoria: "remuneração nominal (e demais colunas de valores por servidor)"}
  eras:
    - {desde: 2012-06, mudanca: "Série antiga (RAR): seis colunas, sem grupo; valores TOTDOMES, TOTBRUTO e TOTLIQ"}
    - {desde: 2023-04, mudanca: "ZIP mensal do histórico: onze colunas (remuneração do mês, férias e 13º, pagamentos eventuais, licença prêmio, abono e outras indenizações, redutor, total líquido e grupo), sem CPF"}
    - {desde: 2025-07, mudanca: "ZIP mensal com dezoito colunas e nomes de cabeçalho novos (REMUNERAÇÃO, FÉRIAS/13º, RENDIMENTO LÍQUIDO...), com situação funcional, regime, jornada, referência, grau e datas; ZIP traz o mesmo arquivo em CSV e TXT"}
    - {desde: 2026-10, mudanca: "Arquivo corrente (consolidado): dezenove colunas, com CPF parcial e cabeçalhos próprios (SITUAÇÃO DE DESLIGAMENTO, JORNADA, INGRESSO, NOMEAÇÃO)"}
  revisado_em: 2026-11-09
  versao_fetcher: 0.2.2
---

# Remuneração dos servidores públicos do Estado de São Paulo

## Resumo

Relação nominal e remuneração mensal dos servidores e empregados públicos do Estado de São Paulo, incluindo aposentados e pensionistas, como o Portal da Transparência do Estado a publica. Para cada pessoa e mês traz o nome, o cargo, o órgão e as parcelas da remuneração (remuneração do mês, férias e 13º, pagamentos eventuais, licença prêmio indenizada, abono de permanência e outras indenizações, redutor salarial) e o total líquido. Os arquivos mais recentes trazem também situação funcional, regime de contratação e datas.

## Ficha técnica

<!-- gerado:ficha -->

| Campo | Valor |
|---|---|
| Dataset | `transparencia-sp/remuneracao` |
| Órgão | Portal da Transparência do Estado de São Paulo (Controladoria Geral do Estado) |
| Página oficial | https://www.transparencia.sp.gov.br/Remuneracao |
| Licença | O rodapé do portal mostra 'Todos os direitos reservados' e um link para a Licença Creative Commons 4.0 (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/deed.pt-br); a página de remuneração não detalha termos de uso (conferido em 2026-11-09) |
| Periodicidade | mensal (a página não informa calendário de atualização) |
| Cobertura | 2012-06 a em-curso |
| Unidade (uma linha) | um servidor, aposentado ou pensionista em um mês |
| Granularidade | espacial: órgão/entidade de lotação (texto livre); temporal: mês |
| Formato bruto | três formas: RAR por mês (2012-06 a 2023-03; CSV Latin-1, ponto e vírgula, vírgula decimal, textos entre aspas), ZIP por mês (2023-04 em diante; CSV, ponto e vírgula, milhar com ponto e vírgula decimal) e CSV consolidado corrente (UTF-8 com BOM) |
| Estado no lake | convertido |
| Partições | `ano`, `mes` |
| Chave | — |
| Colunas | 32 |
| Unidades de medida | `totdomes`: R$; `totbruto`: R$; `totliq`: R$; `remuneracao_do_mes`: R$; `ferias_e_13o_salario`: R$; `pagamentos_eventuais`: R$; `licenca_premio_indenizada`: R$; `abono_permanencia_outras_indenizacoes`: R$; `redutor_salarial`: R$; `total_liquido_r`: R$; `remuneracao`: R$; `ferias_13o`: R$; `licenca_premio`: R$; `abono_permanencia`: R$; `redutor`: R$; `rendimento_liquido`: R$ |
| Dados pessoais | `nome` (nome completo do servidor); `cpf` (CPF, parcialmente mascarado pela fonte (só no arquivo corrente)); `data_de_ingresso` (data de ingresso no serviço público, associada ao nome); `data_de_nomeacao_no_cargo` (data de nomeação, associada ao nome); `ingresso` (data de ingresso no serviço público, associada ao nome); `nomeacao` (data de nomeação, associada ao nome); `remuneracao_do_mes` (remuneração nominal (e demais colunas de valores por servidor)) |
| Eras | 2012-06: Série antiga (RAR): seis colunas, sem grupo; valores TOTDOMES, TOTBRUTO e TOTLIQ; 2023-04: ZIP mensal do histórico: onze colunas (remuneração do mês, férias e 13º, pagamentos eventuais, licença prêmio, abono e outras indenizações, redutor, total líquido e grupo), sem CPF; 2025-07: ZIP mensal com dezoito colunas e nomes de cabeçalho novos (REMUNERAÇÃO, FÉRIAS/13º, RENDIMENTO LÍQUIDO...), com situação funcional, regime, jornada, referência, grau e datas; ZIP traz o mesmo arquivo em CSV e TXT; 2026-10: Arquivo corrente (consolidado): dezenove colunas, com CPF parcial e cabeçalhos próprios (SITUAÇÃO DE DESLIGAMENTO, JORNADA, INGRESSO, NOMEAÇÃO) |
| Revisado em | 2026-11-09 |
| Versão do fetcher | 0.2.2 |

## Origem e coleta

- **Série antiga:** `https://www.transparencia.sp.gov.br/PortalTransparencia-Report/historico/remuneracao_<Mês>_<AAAA>.rar`, um RAR por mês de 2012-06 a 2023-03. No bruto: `remuneracao_rar_<AAAA-MM>@<AAAAMMDD>.rar`. Ler RAR exige o extra `rar` do pacote e a biblioteca `libarchive` do sistema.
- **Histórico:** ZIP mensal baixado de `https://www.transparencia.sp.gov.br/Remuneracao/downloadhistorico`. No bruto: `remuneracao_<AAAA-MM>@<AAAAMMDD>.zip`.
- **Corrente:** `https://www.transparencia.sp.gov.br/Remuneracao/Download?arquivo=Remuneracao.csv`. No bruto: `remuneracao_corrente@<AAAAMMDD>.csv`; o arquivo não traz coluna de mês de referência, por isso o fetcher usa o mês da data de coleta (`Last-Modified`) como partição.
- **Dicionário:** planilha Excel do portal, guardada no bruto como `dicionario_remuneracao@<AAAAMMDD>.xlsx` e não convertida; o conversor ignora esse arquivo e arquivos "leia-me".
- Cada ZIP ou RAR pode conter mais de um arquivo; o conversor lê os `.csv` e `.txt` e identifica o tipo de contêiner pela assinatura do arquivo, não pela extensão.

## Conteúdo

- Uma linha por pessoa e mês. Nas amostras conferidas há de 1,04 a 1,07 milhão de linhas por mês (2012-06: 1.054.395; 2023-04: 1.071.441; 2025-06: 1.037.234; 2025-07: 1.036.618).
- Cobertura conferida em 2026-11-09 pela listagem do bruto: série antiga de 2012-06 a 2023-03 (130 meses, sem lacuna); histórico de 2023-04 a 2026-06 (36 meses), faltando 2024-03, 2025-03 e 2026-03; e um arquivo corrente com data de coleta 2026-10-24. A página do portal listava ZIPs até agosto de 2026 em 2026-11-09; os de 2026-07 e 2026-08 não constavam do bruto nessa data.
- Eras (as mudanças de colunas estão no dicionário):
  1. **2012-06 (RAR):** `NOME;CARGO;ORGAO;TOTDOMES;TOTBRUTO;TOTLIQ`, textos entre aspas, decimal com vírgula e sem separador de milhar. Conferido no RAR de 2012-06. O código do conversor menciona também cabeçalhos `TOT*_FINAL` entre 2013 e 2016; não conferi esses anos.
  2. **2023-04 (ZIP):** onze colunas, sem CPF; decimal com vírgula e sem separador de milhar em 2023-04 (conferido em 2023-04 e 2025-06 quanto às colunas).
  3. **2025-07 (ZIP):** dezoito colunas com cabeçalhos renomeados e milhar com ponto (`1.400,00`). O ZIP traz `Remuneracao.csv` e `Remuneracao.txt` idênticos byte a byte (conferido em 2025-07).
  4. **Corrente:** dezenove colunas, com CPF parcial.
- O dicionário oficial do portal (planilha Excel) descreve, por denominação: Nome, CPF, Situação Funcional, Grupo Funcional, Cargo/Função, Regime de Contratação, Data de Ingresso, Data de Nomeação do Cargo, Jornada de Trabalho, Referência, Grau, Lotação, Cargo/Função Origem, Regime de Contratação Origem, Referência Origem, Grau Origem, Órgão/Entidade, Órgão Origem, Motivo do Desligamento, Data de Desligamento, Data de Início da Pensão, Data de Ingresso do Servidor Principal, Férias e 13º Salário, Pagamentos Eventuais, Licença Prêmio Indenizada, Abono Permanência & Outras Indenizações, Redutor Salarial, Remuneração Bruta e Remuneração Líquida. Nem toda denominação aparece nos arquivos que o fetcher converte (por exemplo, Lotação e os campos "Origem").

## Variáveis

As descrições vêm do dicionário de dados oficial do portal (planilha Excel, coletada em 2026-10-30). Onde o dicionário não traz o campo, a coluna diz "não informado pela fonte". Como os nomes de coluna mudam entre as eras, o mesmo conteúdo pode estar em colunas diferentes do lake; uma coluna fica nula (ou ausente) nos arquivos de eras que não a têm.

| Coluna no lake | Na fonte | Tipo | Descrição | Unidade / códigos | Período |
|---|---|---|---|---|---|
| `nome` | `NOME` | texto | Nome completo do servidor conforme registro funcional. Nas eras 2025-07 em diante o texto vem com espaços à direita | — | todo |
| `cpf` | `CPF` | texto | CPF do servidor, exibido parcialmente por motivos de segurança (formato `***.999.999-**` na amostra) | — | só no arquivo corrente |
| `cargo` | `CARGO` | texto | Cargo ou função atual do servidor conforme cadastro funcional | — | todo |
| `orgao` | `ORGAO` / `ORGÃO` | texto | Órgão ao qual o servidor está atualmente vinculado | — | todo |
| `totdomes` | `TOTDOMES` | decimal | Não informado pela fonte (o dicionário não traz o campo; o nome sugere um total do mês) | R$ | 2012-06 (série antiga) |
| `totbruto` | `TOTBRUTO` | decimal | Não informado pela fonte; o dicionário define "Remuneração Bruta" como a soma das parcelas do cargo efetivo, função ou cargo comissionado, gratificações e vantagens de caráter temporário ou permanente | R$ | 2012-06 (série antiga) |
| `totliq` | `TOTLIQ` | decimal | Não informado pela fonte; o dicionário define "Remuneração Líquida" como o valor após deduções obrigatórias e demais descontos do mês | R$ | 2012-06 (série antiga) |
| `remuneracao_do_mes` | `REMUNERAÇÃO DO MÊS` | decimal | Remuneração do mês. O dicionário define "Remuneração Bruta" como a soma das parcelas remuneratórias do cargo efetivo, função ou cargo comissionado, gratificações e vantagens pecuniárias temporárias ou permanentes; ele não diz expressamente que esta coluna é a bruta | R$ | 2023-04 a 2025-06 e corrente |
| `ferias_e_13o_salario` | `FÉRIAS E 13º SALÁRIO` | decimal | Parcelas relativas a férias, inclusive acréscimos e abono, e 13º salário, inclusive antecipações | R$ | 2023-04 a 2025-06 e corrente |
| `pagamentos_eventuais` | `PAGAMENTOS EVENTUAIS` | decimal | Bonificação por resultados, participação nos resultados, pagamentos atrasados por benefícios com vigência retroativa, correção monetária, reposições em geral, entre outros | R$ | 2023-04 em diante |
| `licenca_premio_indenizada` | `LICENÇA PRÊMIO INDENIZADA` | decimal | Parcelas remuneratórias relativas à licença prêmio indenizada | R$ | 2023-04 a 2025-06 e corrente |
| `abono_permanencia_outras_indenizacoes` | `ABONO PERMANÊNCIA & OUTRAS INDENIZAÇÕES` | decimal | Parcelas relativas a abono de permanência e de caráter indenizatório (adicional de transporte, auxílio transporte, ajuda de custo, auxílio ou diária alimentação, entre outras) | R$ | 2023-04 a 2025-06 e corrente |
| `redutor_salarial` | `REDUTOR SALARIAL` | decimal | Valor de eventual redutor salarial, para cumprimento do teto salarial | R$ | 2023-04 a 2025-06 e corrente |
| `total_liquido_r` | `TOTAL LIQUÍDO (R$)` | decimal | Remuneração líquida: valor após deduções obrigatórias e demais descontos do mês | R$ | 2023-04 a 2025-06 e corrente |
| `grupo` | `GRUPO` | texto | Grupo funcional (ativo, aposentado, pensionista). Valores conferidos: `ATIVOS`, `APOSENTADOS`, `PENSIONISTAS` (2023-04); `ATIVOS`, `APOSENTADO`, `PENSIONISTA` (2025-07 e corrente) | texto | 2023-04 em diante |
| `remuneracao` | `REMUNERAÇÃO` | decimal | Mesma finalidade de `remuneracao_do_mes`, com o cabeçalho renomeado | R$ | 2025-07 em diante (histórico) |
| `ferias_13o` | `FÉRIAS/13º` | decimal | Mesma finalidade de `ferias_e_13o_salario` | R$ | 2025-07 em diante (histórico) |
| `licenca_premio` | `LICENÇA PRÊMIO` | decimal | Mesma finalidade de `licenca_premio_indenizada` | R$ | 2025-07 em diante (histórico) |
| `abono_permanencia` | `ABONO PERMANÊNCIA` | decimal | Mesma finalidade de `abono_permanencia_outras_indenizacoes` | R$ | 2025-07 em diante (histórico) |
| `redutor` | `REDUTOR` | decimal | Mesma finalidade de `redutor_salarial` | R$ | 2025-07 em diante (histórico) |
| `rendimento_liquido` | `RENDIMENTO LÍQUIDO` | decimal | Mesma finalidade de `total_liquido_r` | R$ | 2025-07 em diante (histórico) |
| `situacao_funcional` | `SITUAÇÃO FUNCIONAL` | texto | Situação funcional atual do servidor no órgão (ex.: `EM EXERCICIO NORMAL DE TRABALHO`, `APOSENTADORIA`, `AFASTAMENTO SEM PREJ VCTO`); nulo para parte das linhas | texto | 2025-07 em diante (histórico) |
| `situacao_de_desligamento` | `SITUAÇÃO DE DESLIGAMENTO` | texto | Cabeçalho do arquivo corrente; os valores na amostra são os mesmos de `situacao_funcional`. O dicionário tem "Situação Funcional" e "Motivo do Desligamento"; a fonte não diz a qual dos dois este campo corresponde | texto | corrente |
| `regime_de_contratacao` | `REGIME DE CONTRATAÇÃO` | texto | Regime jurídico ao qual o servidor está vinculado (ex.: `TITULAR DE CARGO EFETIVO`, `ADMITIDO C.L.T.`); nulo para parte das linhas | texto | 2025-07 em diante |
| `jornada_de_trabalho` | `JORNADA DE TRABALHO` | texto | Carga horária do servidor informada pelo órgão (texto com zeros à esquerda, ex.: `40`, `08`, `00`) | horas, conforme o órgão | 2025-07 em diante (histórico) |
| `jornada` | `JORNADA` | texto | Mesma finalidade de `jornada_de_trabalho`, com o cabeçalho do arquivo corrente | horas, conforme o órgão | corrente |
| `referencia` | `REFERENCIA` / `REFERÊNCIA` | texto | Referência salarial do cargo atual do servidor (texto com zeros à esquerda, ex.: `0000000001`); nulo para a maior parte das linhas | — | 2025-07 em diante |
| `grau` | `GRAU` | texto | Grau do cargo atual do servidor (ex.: `C`, `M`, `1`); nulo para a maior parte das linhas | — | 2025-07 em diante |
| `data_de_ingresso` | `DATA DE INGRESSO` | texto | Data em que o servidor ingressou no serviço público estadual, em `DD/MM/AAAA`, sem conversão para data | — | 2025-07 em diante (histórico) |
| `ingresso` | `INGRESSO` | texto | Mesma finalidade de `data_de_ingresso`, com o cabeçalho do arquivo corrente | — | corrente |
| `data_de_nomeacao_no_cargo` | `DATA DE NOMEAÇÃO NO CARGO` | texto | Data de nomeação do servidor no cargo atual, em `DD/MM/AAAA`, sem conversão para data | — | 2025-07 em diante (histórico) |
| `nomeacao` | `NOMEAÇÃO` | texto | Mesma finalidade de `data_de_nomeacao_no_cargo`, com o cabeçalho do arquivo corrente | — | corrente |
| `ano` | nome do arquivo | inteiro | Ano do mês de referência; é a partição | — | todo |
| `mes` | nome do arquivo | inteiro | Mês de referência; é a partição | 1 a 12 | todo |

## No lake

- Dataset `transparencia-sp/remuneracao`, particionado por `ano` e `mes`; um Parquet por arquivo bruto e membro.
- `ano` e `mes` vêm do nome do arquivo bruto (`..._2024-05@...`). Só o arquivo corrente, que não traz mês no conteúdo, usa o mês da data de coleta. Arquivo sem período no nome e que não é o corrente conta como erro e não é convertido.
- Todo o conteúdo é lido como texto. Só as colunas de valores (nomes que começam com `tot` ou contêm `remuneracao`, `ferias`, `pagamentos`, `licenca`, `abono`, `redutor`, `liquido`, `bruto` e similares) viram decimal: o conversor tira os pontos de milhar, troca a vírgula decimal por ponto e converte; um valor que não converte vira nulo.
- Os nomes de coluna são normalizados (minúsculas, sem acento, `_` no lugar de símbolos). O conversor **não** harmoniza os nomes entre as eras: cada era grava suas colunas com os nomes que o arquivo trouxe, e o dataset reúne a união delas (32 colunas, mais as partições).
- Datas (`ingresso`, `nomeacao`, `data_de_*`), `referencia`, `grau` e `jornada*` ficam como texto.
- Decodificação: RAR em Latin-1; ZIP e CSV em UTF-8 (com BOM), com recurso a cp1252.
- Linhas com campos a mais que o cabeçalho (texto com `;` embutido) têm os campos excedentes unidos à última coluna; nenhuma linha é descartada.
- Arquivo só com cabeçalho não gera Parquet.

## Cuidados de uso

- **Os nomes de coluna mudam entre eras.** Para uma série contínua é preciso unir colunas equivalentes (por exemplo `total_liquido_r`, `rendimento_liquido` e `totliq`; `remuneracao_do_mes` e `remuneracao`). As equivalências desta página são pelo conteúdo dos cabeçalhos; a fonte não publica uma tabela de equivalência.
- **Coluna de valor e significado.** Na série antiga, `totdomes`, `totbruto` e `totliq` não têm definição na fonte. Na amostra de 2012-06, `totliq` é maior que `totbruto` em 189 linhas; não trate `totbruto` como teto de `totliq` sem checar.
- **Valores negativos e extremos.** No arquivo corrente (primeiros 60 MB, amostra) há `total_liquido_r` de −35.112,20 e máximos de 202.136,83 em `remuneracao_do_mes`. A conversão não corrige valores.
- **Linhas repetidas.** Há linhas inteiramente idênticas dentro do mesmo mês nas amostras conferidas (223 em 2012-06, 241 em 2023-04, 138 em 2025-07). Os arquivos não trazem identificador de pessoa e o CPF só vem no arquivo corrente; por isso o dataset não tem chave única declarada. Não conte linhas como pessoas distintas sem tratar duplicatas e homônimos.
- **Nome com espaços à direita.** Em 2025-07 e no arquivo corrente o nome vem com espaços à direita (908.152 de 1.036.618 linhas em 2025-07; 231.871 de 262.663 na amostra do corrente). Aplique `strip` antes de juntar ou agrupar por nome.
- **Valores do grupo mudam de grafia.** `APOSENTADOS` e `PENSIONISTAS` (plural) em 2023-04; `APOSENTADO` e `PENSIONISTA` (singular) em 2025-07 e no corrente. A passagem exata entre os meses de 2023-04 e 2025-07 não foi conferida.
- **Mês do arquivo corrente.** O arquivo corrente não traz mês de referência; o lake usa o mês da data de coleta. Não conferi que o conteúdo corresponda a esse mês. Quando o mês fechado sai no histórico, prefira o histórico.
- **Lacunas na cobertura.** Faltam no bruto os meses 2024-03, 2025-03 e 2026-03 do histórico, e 2026-07 e 2026-08 (listados pela página do portal em 2026-11-09). A fonte não explica as lacunas.
- **Dado pessoal.** Os arquivos trazem nome e remuneração por servidor, publicados pelo próprio portal; o CPF vem parcialmente mascarado. Use conforme a legislação de proteção de dados.
- Conferências feitas em 2026-11-09, com o fetcher 0.2.2, sobre amostras de 2012-06, 2023-04, 2025-06, 2025-07 e dos primeiros 60 MB do arquivo corrente de 2026-10-24.

## Exemplos

Remuneração líquida média e quantidade de linhas por grupo em abril de 2023, sobre a série do histórico:

```python
import polars as pl

rem = pl.scan_parquet("lake/transparencia-sp/remuneracao/**/*.parquet", hive_partitioning=True)
por_grupo = (
    rem.filter((pl.col("ano") == 2023) & (pl.col("mes") == 4))
    .unique()  # descarta linhas inteiramente repetidas
    .group_by("grupo")
    .agg(
        pl.len().alias("linhas"),
        pl.col("total_liquido_r").mean().alias("liquido_medio"),
    )
    .sort("linhas", descending=True)
    .collect()
)
```

## Referências

- Página de remuneração do portal: https://www.transparencia.sp.gov.br/Remuneracao
- Dicionário de dados do portal: https://www.transparencia.sp.gov.br/Dicionarios/Dicionario%20de%20dados%20-%20Remuneracao.xlsx
- Licença Creative Commons 4.0 (CC BY 4.0), linkada no rodapé do portal: https://creativecommons.org/licenses/by/4.0/deed.pt-br
