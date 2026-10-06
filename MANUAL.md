# Controle GWM — Dashboard: Manual

O dashboard é uma página web que **só lê** a planilha do Google Sheets e mostra os números.
Os vendedores continuam lançando na planilha; o dashboard nunca altera nada.

Este manual tem 3 partes:
- **Parte 1 — Instalação** (quem monta, uma única vez, ~30 minutos)
- **Parte 2 — Uso pela equipe** (também está dentro do dashboard, na aba "Como usar")
- **Parte 3 — Problemas comuns**

---

## Parte 1 — Instalação (uma única vez)

### Passo 1 — Criar o acesso do Google (conta de serviço)
É um "usuário robô" que só serve para o dashboard ler a planilha.

1. Entre em https://console.cloud.google.com e crie um projeto (ex.: "Controle GWM").
2. No menu, vá em **APIs e serviços → Biblioteca**, procure **Google Sheets API** e clique em **Ativar**.
3. Vá em **APIs e serviços → Credenciais → Criar credenciais → Conta de serviço**. Dê um nome (ex.: "dashboard") e conclua.
4. Clique na conta criada → aba **Chaves → Adicionar chave → Criar nova chave → JSON**.
   Um arquivo `.json` será baixado. **Guarde-o e não envie a ninguém.**
5. Anote o e-mail da conta de serviço (termina com `iam.gserviceaccount.com`).

### Passo 2 — Liberar a planilha para o robô
1. Abra a planilha Controle GWM → **Compartilhar**.
2. Cole o e-mail da conta de serviço e dê permissão de **Leitor**.

### Passo 3 — Pegar o ID da planilha
Na URL da planilha, o ID é o trecho entre `/d/` e `/edit`:
`https://docs.google.com/spreadsheets/d/`**`ESTE_TRECHO`**`/edit`

### Passo 4 — Colocar o código no GitHub
1. Crie uma conta em https://github.com e um repositório **privado** (ex.: `controle-gwm`).
2. Envie estes arquivos para o repositório: `app.py`, `dados.py`, `requirements.txt`, `.gitignore`.
   (Pode usar o botão **Add file → Upload files** no site.)
3. **Nunca** envie o arquivo `.json` da chave nem o `secrets.toml`.

### Passo 5 — Publicar no Streamlit Cloud (gratuito)
1. Entre em https://share.streamlit.io com a conta do GitHub.
2. Clique em **Create app** → escolha o repositório → **Main file path:** `app.py`.
3. Abra **Advanced settings → Secrets** (próximo passo) e clique em **Deploy**.

### Passo 6 — Preencher os "Secrets"
No campo Secrets cole o modelo abaixo, trocando pelos seus dados. Os campos da conta de serviço
vêm do arquivo `.json` baixado no Passo 1 (copie cada valor para o campo de mesmo nome).
O modelo também está no arquivo `.streamlit/secrets.toml.example`.

```toml
planilha_id = "ID_DO_PASSO_3"
senha = "escolha-uma-senha"      # opcional: apague a linha para não pedir senha

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Dica: no `private_key`, mantenha os `\n` exatamente como estão no arquivo.

### Passo 7 — Entregar o link para a equipe
O Streamlit gera um link do tipo `https://nome-do-app.streamlit.app`. Envie para as 5 pessoas.
- Com `senha` preenchida, o painel pede a senha ao abrir.
- Para restringir também por e-mail: no app, **Share** → *Only specific people can view this app*.

### Alternativa: rodar só no seu computador
1. Instale o Python (https://python.org).
2. Na pasta do projeto: `pip install -r requirements.txt`
3. Crie a pasta `.streamlit`, copie `secrets.toml.example` para `.streamlit/secrets.toml` e preencha.
4. Rode: `streamlit run app.py`

---

## Parte 2 — Uso pela equipe

1. **Período:** barra da esquerda. Vale para a **data de faturamento (DATA FAT)**. Padrão: do dia 1º do mês até hoje.
2. **Lojas e vendedores:** filtros opcionais. Vazio = todos.
3. **Abas:** Resumo, Lojas, Vendedores, Modelos, Dados (com botão de download) e Como usar.
4. **Atualizar:** botão **🔄 Atualizar dados agora**. Sozinho, atualiza a cada 5 minutos.

### Regras de preenchimento da planilha (para os números ficarem certos)
| Regra | Por quê |
|---|---|
| STATUS igual à lista: Aguardando faturamento, Faturado, Cancelado, Devolução | Cada status é contado separadamente |
| DATA FAT preenchida em *Faturado* e *Devolução* | Sem data, a venda não entra em nenhum período |
| DATA PEDIDO preenchida em todo pedido | Usada em cancelados e pedidos do período |
| VENDA, CUSTO e INCID só com números | Lucro bruto = VENDA − CUSTO − INCID |
| VEND escolhido na lista | Nome diferente vira outro vendedor |
| Aba Metas: mês no 1º dia (01/10/2026), loja com o mesmo nome da aba | Senão a meta não é encontrada |

### Como os números são calculados
- **Faturamento e quantidade:** status *Faturado* com DATA FAT no período.
- **Lucro bruto:** lucro dos faturados menos o das devoluções do período. Em devolução o lucro entra negativo.
- **Margem:** lucro bruto ÷ faturamento.
- **Meta:** soma das metas dos meses que o período toca (de 01/10 a 15/10 usa a meta de outubro inteira).
- **Aguardando faturamento:** todos os pedidos nesse status hoje, sem filtro de data.
- **Cancelados:** status *Cancelado* com DATA PEDIDO no período.

### Mudou algo na planilha?
- **Novo vendedor ou modelo:** só preencher na planilha; aparece sozinho no painel.
- **Nova loja:** avise quem mantém o painel (é preciso incluir a loja no arquivo `dados.py`, linha `LOJAS`).
- **Não mude os títulos das colunas** (linha 1) das abas das lojas. O painel encontra os dados pelo nome da coluna.

---

## Parte 3 — Problemas comuns

| O que aparece | O que fazer |
|---|---|
| "Não consegui ler a planilha" + `SpreadsheetNotFound` | A planilha não foi compartilhada com o e-mail da conta de serviço (Passo 2) ou o ID está errado (Passo 3) |
| "Faltam as configurações de acesso (secrets)" | O campo Secrets está vazio ou com erro de formato (Passo 6) |
| Erro citando `Google Sheets API has not been used` | Ativar a Google Sheets API no projeto (Passo 1, item 2) |
| Erro citando `Worksheet not found` | Alguma aba foi renomeada. Os nomes precisam ser: Loja 01, Loja 02, Loja 03, Loja 04 e Metas |
| Faturamento zerado | Verificar STATUS = Faturado e DATA FAT dentro do período escolhido |
| Meta zerada ou "—" | Conferir a aba Metas (mês no 1º dia, nome da loja igual). A meta some quando há vendedor filtrado, pois é por loja |
| Número não bate com a planilha | Clicar em **Atualizar dados agora** e conferir o período e as lojas marcadas |
| Vendedor aparece duas vezes | Nome escrito de formas diferentes na planilha; padronizar pela lista |
