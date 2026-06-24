# CCM & NFSe Automation

Automação para consulta de Cadastro Municipal (CCM) e download de documentos fiscais (NFS-e) a partir de uma planilha de fornecedores.

## Objetivo

A solução realiza a leitura de uma planilha Excel contendo fornecedores, consulta o Cadastro Municipal (CCM) nos portais das prefeituras e realiza o download dos documentos disponíveis.

Atualmente o sistema suporta:

* Cadastro Municipal (CCM)
* Download de NFS-e via Portal Nacional da NFS-e
* Resolução automática de hCaptcha e reCAPTCHA v2 utilizando 2Captcha
* Atualização automática da planilha com os CCMs encontrados

---

# Municípios Suportados

| Município      | Estratégia                       |
| -------------- | -------------------------------- |
| Belo Horizonte | Consulta por CNPJ                |
| Rio de Janeiro | Consulta por CNPJ                |
| Barueri        | Consulta por CNPJ                |
| Porto Alegre   | Consulta por CNPJ + reCAPTCHA v2 |
| Nova Lima      | Consulta por CNPJ                |

---

# Estrutura do Projeto

```text
ccm-nfse-automation/
│
├── base/
│   ├── config.py
│   └── scraper.py
│
├── scrapers/
│   ├── belo_horizonte.py
│   ├── rio_de_janeiro.py
│   ├── barueri.py
│   ├── porto_alegre.py
│   └── nova_lima.py
│
├── outputs/
│
├── logs/
│
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

# Arquitetura

Todos os scrapers herdam de `BaseScraper`.

Fluxo padrão:

```text
start()
│
├── before_scrape()
├── scrape()
├── download_ccm()
├── download_nfse()
├── after_scrape()
│
close()
```

A classe base centraliza:

* Inicialização do Playwright
* Controle do navegador
* Solução de captchas
* Download e armazenamento de documentos
* Logging
* Tratamento de erros

Cada município implementa apenas sua regra específica de consulta.

---

# Instalação

## Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate
```

## Instalar dependências

```bash
pip install -r requirements.txt
```

## Instalar navegador do Playwright

```bash
playwright install chromium
```

---

# Configuração

Criar arquivo `.env`:

```env
CCM_BELO_HORIZONTE=https://mobiliarioonline.pbh.gov.br/mobiliario-cadastro-publico/f/t/emiteficwebsel

CCM_RIO_DE_JANEIRO=https://certec.apps.rio.gov.br/

CCM_BARUERI=

CCM_PORTO_ALEGRE=https://siat.procempa.com.br/siat/CpsEmitirComprovanteInscricao_Internet.do

CCM_NOVA_LIMA=

NFSE_URL=https://www.nfse.gov.br/consultapublica

CAPTCHA_API_KEY=YOUR_2CAPTCHA_API_KEY
```

---

# Formato da Planilha

Colunas obrigatórias:

| Coluna          | Descrição                                  |
| --------------- | ------------------------------------------ |
| CNPJ            | CNPJ do fornecedor                         |
| CCM             | CCM existente (caso vazio será consultado) |
| MUNICIPIO       | Município do fornecedor                    |
| COD.VERIFICACAO | Código de verificação da NFS-e             |

Exemplo:

```text
CNPJ,CCM,MUNICIPIO,COD.VERIFICACAO
28203865000174,,belohorizonte,31062002228203865000174000000000002426013942565090
12977432000136,,riodejaneiro,33045572212977400000000000000000000000000000000000
15486022000180,,portoalegre,43149022215486022000180000000000012325128774827539
```

---

# Execução

Processar todos os municípios:

```bash
python main.py --input janabril2026_amostra_5x5.xlsx
```

Processar apenas um município:

```bash
python main.py \
    --input janabril2026_amostra_5x5.xlsx \
    --city belohorizonte
```

Exemplos:

```bash
python main.py --input fornecedores.xlsx --city riodejaneiro

python main.py --input fornecedores.xlsx --city portoalegre
```

---

# Saída dos Arquivos

Os documentos são organizados automaticamente por município e CNPJ.

Estrutura:

```text
outputs/

├── belohorizonte/
│   └── 28203865000174/
│       ├── CADASTRO_MUNICIPAL.pdf
│       └── Nota.pdf
│
├── riodejaneiro/
│   └── 12977432000136/
│       ├── CADASTRO_MUNICIPAL.pdf
│       └── Nota.pdf
│
└── portoalegre/
    └── 15486022000180/
        ├── CADASTRO_MUNICIPAL.pdf
        └── Nota.pdf
```

---

# Atualização da Planilha

Ao final da execução é gerada uma nova planilha contendo os CCMs encontrados.

Exemplo:

```text
outputs/
└── janabril2026_amostra_5x5_20260624_101530.xlsx
```

A coluna `CCM` é preenchida automaticamente quando encontrada.

---

# Captchas

O sistema suporta:

### hCaptcha

Utilizado pelo Portal Nacional da NFS-e.

Método:

* Captura automática do sitekey
* Resolução via 2Captcha
* Injeção automática do token

### reCAPTCHA v2

Utilizado por alguns municípios, como Porto Alegre.

Método:

* Captura automática do sitekey via iframe
* Resolução via 2Captcha
* Integração com Playwright

---

# Logs

Logs são gravados em:

```text
logs/
└── scrapper.log
```

Exemplo:

```text
START scraper=BeloHorizonteScraper cnpj=28203865000174

Saved file:
outputs/belohorizonte/28203865000174/CADASTRO_MUNICIPAL.pdf

FINISHED scraper=BeloHorizonteScraper cnpj=28203865000174 ccm=1234567
```

---

# Tratamento de Falhas

Situações tratadas:

* CNPJ não encontrado
* CCM não encontrado
* NFS-e inexistente
* Timeout de elementos
* Falha na resolução de captcha
* Erros de navegação Playwright
* Portais indisponíveis

Exemplo:

```text
NFS-e not found |
cnpj=28203865000174 |
access_key=31062002228203865000174000000000002426013942565090
```

---

# Tecnologias

* Python 3.12+
* Playwright
* Pandas
* 2Captcha
* playwright-captcha
* OpenPyXL
