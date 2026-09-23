# CREDENCIAIS — nomes dos secrets, NUNCA os valores

Nada aqui é segredo. Este arquivo existe para dizer **onde cada segredo mora** e
**o que para de funcionar sem ele**. Valor de token não entra em repo, em chat
nem em print — a pasta `credenciais/` é gitignorada e o runner a monta a partir
dos Secrets do GitHub, apagando-a no fim de cada execução (`rm -rf credenciais`).

## Secrets do repositório (Settings → Secrets and variables → Actions)

| secret | o que é | sem ele |
|---|---|---|
| `YT_CLIENT_SECRET_GTA` | JSON da credencial OAuth "App para computador" do projeto Cloud do canal | o YouTube inteiro fica parado |
| `YT_TOKEN_GTA` | `credenciais/gta/token.json` gerado por `produzir/autorizar.py --canal gta` | idem |
| `YT_TOKEN_ANALYTICS_GTA` | token só-leitura de Analytics (`autorizar.py --canal gta --analytics`) | não há hora contável nem retenção medida; o resto roda |
| `IG_USER_ID_GTA` | id de `graph.instagram.com/me` (NÃO o número que aparece no painel) | o Instagram para depois do render |
| `IG_TOKEN_GTA` | token longo com `instagram_business_content_publish` | idem |
| `ZERNIO_KEY_GTA` | chave da conta do Zernio (espelho no TikTok) | o TikTok não espelha; `tiktok.ativo` fica `false` |
| `ANTHROPIC_API_KEY` | resumo das notícias (formato C), modelo `claude-haiku-4-5` | `noticias.py` usa o resumo de emergência e grava nota 6 — abaixo do corte de 7, ou seja, a notícia não vira Short sozinha |

`GITHUB_TOKEN` é do próprio Actions (não se cria): é ele que sobe o MP4 como
asset de Release para a Graph API do Instagram poder baixar.

## Como o token do YouTube é gerado

```bash
python produzir/autorizar.py --canal gta
```

Abre a tela de consentimento do Google, confere de qual canal é o token e
**recusa gravar** se não bater com o `channel_id` de `publicador/config.json`
(token do canal errado publica vídeo no canal errado — já aconteceu nesta casa).
Grava `credenciais/gta/token.json`. Depois:

```bash
gh secret set YT_TOKEN_GTA < credenciais/gta/token.json
gh secret set YT_CLIENT_SECRET_GTA < credenciais/gta/client_secret.json
```

⚠ O app OAuth tem de estar **EM PRODUÇÃO** na tela de consentimento. Em modo de
teste o refresh token morre em 7 dias e o canal emudece sem avisar.

**Resolvido em 22/09/2026 — o app está EM PRODUÇÃO.** O console só libera
"Publicar app" depois que a página de *Branding* tem página inicial, política de
privacidade e termos de serviço, e só aceita URLs de um domínio **pré-registrado**
em "Domínios autorizados". A saída, sem depender de servidor nem de DNS, foi o
**GitHub Pages do próprio repo**: as três páginas estão em `docs/`, no ar em
`https://diegohenriquemoraes-eng.github.io/gta6-canais/`, e o domínio autorizado
é `diegohenriquemoraes-eng.github.io`.

Dados do projeto: Cloud `ageless-fire-509501-r8` (nome "My Project 63358"), conta
`gta6diegomoraes@gmail.com` — que neste Chrome é **authuser=4**; sem esse
parâmetro os links do console e do Studio caem na conta dos outros canais da casa.

## Onde mais existe segredo

- `marca/oficial/` e `marca/cc/` são gitignorados por TAMANHO (432 MB de
  galeria oficial), não por sigilo. O runner os reconstrói com
  `produzir/baixar_oficial.py` e cache de Actions.
- `saida/` é gitignorado: é onde o render trabalha.
- **Os dois repos de mídia, e por que são dois papéis diferentes.** O asset de
  Release tem de ser **público**: privado exige token para baixar e o Instagram
  devolve `status: ERROR` sem explicar. Só que o `GITHUB_TOKEN` do Actions
  **escreve apenas no repositório que o executa** — em 23/09/2026 o cartão
  renderizou no runner e morreu em `gh release create -R .../gta6-media` com
  exit 1. Daí a divisão:
  - **ler** de `gta6-media`, tag `acervo`: é o acervo oficial de 110 MB que eu
    subo do PC (`produzir/subir_acervo.py`) e o runner só baixa. Download
    público não pede token nenhum.
  - **escrever** em `gta6-canais` (este repo), tag `cartoes`: é o MP4 do dia
    que a Graph API precisa alcançar. Vai no próprio repo porque é o único em
    que o token do runner tem escrita — e asset de Release não entra no clone,
    então não incha o Git. Um PAT guardado como secret resolveria também, e
    seria segredo a mais por nada.
