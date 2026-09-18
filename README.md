# Carteira Cripto — app web

Substitui a planilha Excel. Mesma lógica (custo médio ponderado, gatilhos de
recompra/realização, painel consolidado), agora num app web com banco de
dados real em vez de abas de planilha.

## Estrutura

```
app.py                  → Painel (dashboard principal)
pages/1_💼_Posições.py   → tabela detalhada por ativo/exchange
pages/2_✍️_Lançamentos.py → formulário de entrada + histórico
pages/3_⚙️_Config.py      → parâmetros (câmbio, gatilhos, aportes)
lib/db.py               → conexão com o Supabase
lib/precos.py           → cotações ao vivo (Binance + KuCoin)
lib/calculos.py         → toda a lógica de custo médio e P/L
```

## Configuração (uma vez só)

1. **Banco de dados**: rode `01_criar_tabelas.sql` no SQL Editor do Supabase.
2. **Dados históricos**: no Supabase, vá em Table Editor → tabela `lancamentos`
   → botão "Insert" → "Import data via spreadsheet" → suba o arquivo
   `lancamentos_migracao.csv`. Repita para `config` com `config_migracao.csv`.
3. **Segredos**: copie `.streamlit/secrets.toml.example` para
   `.streamlit/secrets.toml` e preencha com a URL e a chave `anon public` do
   seu projeto Supabase (Project Settings → API). Esse arquivo nunca vai pro
   GitHub (está no `.gitignore`).

## Rodando localmente (opcional)

```
pip install -r requirements.txt
streamlit run app.py
```

## Publicando no Streamlit Community Cloud

1. Suba esta pasta inteira para um repositório no GitHub (menos o
   `secrets.toml` real — o `.gitignore` já cuida disso).
2. Em share.streamlit.io → "New app" → aponte para o repositório, branch
   `main`, arquivo principal `app.py`.
3. Em "Advanced settings" → "Secrets", cole o conteúdo do seu
   `secrets.toml` (com os valores reais).
4. Deploy.

## Nota sobre o plano gratuito do Supabase

Projetos gratuitos pausam sozinhos depois de 7 dias sem uso. Se o app
mostrar erro de conexão, entre no painel do Supabase e clique em
"Restore project" — leva menos de um minuto e os dados continuam intactos.
