# Portal da Transparência do Estado de São Paulo — remuneração dos servidores (`transparencia-sp`)

O `transparencia-sp-fetcher` coleta a relação nominal e a remuneração mensal dos servidores e empregados públicos do Estado de São Paulo, publicadas no Portal da Transparência do Estado de São Paulo (operado pela Controladoria Geral do Estado, segundo o rodapé do portal), e as converte para o lake em Parquet particionado por ano e mês.

| Dataset | O que é | Origem | Período | Página |
|---|---|---|---|---|
| `remuneracao` | Uma linha por servidor, aposentado ou pensionista e mês, com as parcelas da remuneração e o total líquido | Série antiga em RAR, ZIPs mensais do histórico e arquivo consolidado corrente do portal | 2012-06 em diante | [remuneracao](datasets/remuneracao.md) |

## Como o portal publica

- **Série antiga (RAR):** um arquivo RAR por mês, de 2012-06 a 2023-03, fora da página atual do portal.
- **Histórico (ZIP):** a página [Remuneração](https://www.transparencia.sp.gov.br/Remuneracao) oferece um ZIP por mês, com filtro "Mês / Ano da Pesquisa". Em 2026-11-09 a página listava ZIPs de abril de 2023 a agosto de 2026.
- **Arquivo corrente (CSV):** o portal oferece em "Arquivos Abertos" arquivos atuais de ativos, aposentados e pensionistas e um consolidado de todos os servidores, em TXT ou CSV. O fetcher baixa o consolidado.
- **Dicionário de dados:** o portal publica uma planilha Excel, "Dicionário de dados - Remuneração", que o fetcher guarda no bruto, mas não converte (não é dado mensal).
- A página não informa um calendário de atualização.
- O CPF é exibido parcialmente por motivos de segurança, segundo o portal.

O fetcher guarda cada versão baixada com a data de coleta no nome (`<arquivo>@AAAAMMDD`). O lake converte a versão mais recente de cada arquivo.

## Quebras que valem para o conjunto

O layout das colunas mudou várias vezes e os nomes de colunas no lake mudam junto; veja as eras e o dicionário de variáveis da página do [remuneracao](datasets/remuneracao.md).
