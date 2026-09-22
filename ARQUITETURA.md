# ARQUITETURA — gta6-canais (BLOCO 1, executado pelo Fable 5.1 em 22/09/2026)

Saída do BLOCO 1 de `PROMPT.md`. Premissas registradas onde houve escolha. O
BLOCO 2 (Opus 5) executa a partir daqui; os itens I (fatos e frases) já estão
gravados em `conteudo/` como JSON validado, não só descritos.

## A. Árvore do repo

```
gta6-canais/
├── PLANO.md · VICESCALE.md · PROMPT.md · ARQUITETURA.md · RETOMAR.md
├── CREDENCIAIS.md              # nomes dos secrets, nunca valores
├── PENDENCIAS-DIEGO.md         # sai do item J
├── nucleo/                     # COPIADO de Palavra-Viva-3x/nucleo, podado
│   ├── tts.py                  # igual (edge-tts, WordBoundary obrigatório)
│   ├── legendas.py             # igual (ASS, estilo Gancho no frame zero)
│   ├── render.py               # igual: render_short, _zoompan(loop), -framerate 30
│   ├── fabrica.py              # PODADO: sai biblia/idiomas; entra montar_short_fato, montar_longo_fatos
│   ├── thumbnail.py            # igual, paleta trocada (item H)
│   ├── musica.py               # igual (pad procedural só no longo)
│   ├── youtube_api.py          # igual
│   ├── playlists.py            # igual
│   ├── cartao.py               # NOVO (item D)
│   └── cenas.py                # NOVO: corte por cena dos vídeos oficiais (scdet) + leitura de conteudo/cenas.json
├── publicador/
│   ├── publicar.py             # COPIADO: decidir(), gap_efetivo, state, cota; ganha formato G e regra pós-lançamento
│   ├── config.json             # 1 canal `gta` + bloco `instagram` + bloco `tiktok`
│   ├── state.json · playlists.json
│   └── instagram.py            # COPIADO de psicologia-fria/src/publicar.py: subir_asset (Release), publicar_reel, publicar_story, _esperar_e_publicar
├── produzir/
│   ├── reabastecer.py          # COPIADO e reescrito: monta fila/AAAA-MM-DD/pacote.json a partir de fatos + cenas + frases
│   ├── escalar.py              # NOVO (item C): cena × frase → fila do formato G
│   ├── ranquear_perfil.py      # NOVO (item E)
│   ├── colher_cc.py            # NOVO (item F): gameplay CC-BY pós-lançamento
│   ├── noticias.py             # NOVO (item G)
│   ├── baixar_oficial.py       # NOVO: trailers + Extended Look (yt-dlp) + galeria; regrava marca/oficial/
│   ├── medir_desempenho.py · medir_retencao.py · vigia.py · realinhar_publicados.py · aplicar_capas.py   # COPIADOS
│   └── autorizar.py            # COPIADO (OAuth local)
├── conteudo/
│   ├── fatos/*.json            # o poço (150 já gravados; loader concatena a pasta)
│   ├── frases.json             # 40 frases-base do cartão (gravado)
│   ├── cenas.json              # sai de produzir/baixar_oficial.py + nucleo/cenas.py
│   ├── ofertas.json            # sai do passo Shopee do BLOCO 2
│   ├── benchmark.json          # sai de ranquear_perfil.py
│   └── noticias/AAAA-MM-DD.json
├── fila/                       # pacotes por data (versionado, sem MP4)
├── marca/                      # avatar, banner, selo, fontes (repo); marca/oficial/ é gitignorado
├── fontes/PROVENIENCIA.md      # origem e licença de cada arquivo
├── testes/                     # test_agenda, test_cota, test_poco, test_vigia (copiados) + test_cartao, test_escalar (novos)
└── .github/workflows/          # publicar, reabastecer, medir, testes, vigia, realinhar, aplicar-capas (copiados) + colher-cc, benchmark
```

**Premissa**: o motor bíblico é podado, não adaptado por flags. `biblia.py`,
`idiomas.py` e `imagens.py` (Openverse) não entram: a imagem vem da galeria
oficial e das cenas do trailer.

Módulos novos, um parágrafo cada:

- `nucleo/cartao.py`: recebe cena (arquivo + inicio/fim), frase, layout 1/2/3 e
  identidade (avatar, nome, handle) e devolve MP4 1080×1920 sem narração. Item D.
- `nucleo/cenas.py`: roda `select='gt(scene,0.35)'` + `showinfo` do ffmpeg nos
  vídeos oficiais, junta cortes em cenas de 6 a 12 s, grava `cenas.json` com
  `video_origem`, `inicio`, `fim`, `descricao` (vazia até o Opus preencher com a
  legenda oficial e os timestamps do Engadget/keengamer), `tags`, `licenca`.
- `produzir/escalar.py`: gera a fila do formato G cruzando cenas × frases com as
  regras de repetição do item C. Idempotente: lê `usada_em` e `state.json`.
- `produzir/ranquear_perfil.py`: item E. Saída: `benchmark.json` + `benchmark/`
  com o 1º frame de cada vídeo (PNG, gitignorado).
- `produzir/colher_cc.py`: item F. Só roda com `hoje >= 2026-11-19`.
- `produzir/noticias.py`: item G. Grava `noticias/AAAA-MM-DD.json` e, se houver
  notícia com `nota >= 7`, um fato `formato: C` temporário no pacote do dia.
- `produzir/baixar_oficial.py`: yt-dlp dos três vídeos do canal Rockstar Games
  (ids em `fontes/PROVENIENCIA.md`), galeria `rockstargames.com/VI/media/
  screenshots` (zip) e artworks. Roda no runner a cada publicação (cache de
  Actions com chave pelo hash da lista), porque `marca/oficial/` não sobe no git.

## B. Esquemas

`conteudo/fatos/*.json` (lista; ids únicos no conjunto da pasta):

| campo | tipo | regra (test_poco) |
|---|---|---|
| `id` | `F###` | único |
| `formato` | `A` contagem · `B` "viu no trailer" · `C` notícia/oferta | obrigatório |
| `gancho` | str | ≤ 10 palavras, vai inteiro no frame zero |
| `narracao` | str | 35-55 palavras, sem "clique", sem "link na bio" (o CTA é do fabricante) |
| `fonte` | URL | obrigatória; `rockstargames.com` tem prioridade na ordenação |
| `cena` | `trailer1@m:ss` · `trailer2@m:ss` · `extended@m:ss` · `galeria: <rótulo>` | resolvida por `cenas.py`; rótulo de galeria casa por substring no nome do arquivo |
| `tags` | lista | ≥ 1 |
| `usado_em` | `{canal: data}` | preenchido pelo publicador |

`conteudo/cenas.json`: `{id, video_origem (trailer1|trailer2|extended|cc:<videoId>), inicio, fim, descricao, tags, licenca (rockstar_oficial|cc-by), credito}`. Duração 6-12 s; cena sem `descricao` não entra no formato G.

`conteudo/frases.json`: `{categoria: [frase]}` + `_regras`; `escalar.py` mantém `usada_em` num arquivo irmão `frases_uso.json` (não suja o poço).

`conteudo/ofertas.json`: lista de `{produto, loja, preco, comissao_pct, vendidos, nota, prioridade, vigencia: {de, ate}, links: {yt_short, yt_longo, ig_bio, ig_story, tt_bio}}`. Regra: todo link tem `src=`; `vigencia.ate` obrigatória (a pré-venda morre em 20/11).

`conteudo/benchmark.json`: `{rede, perfil, coletado_em, videos: [{id, url, views, likes, comentarios, duracao_s, publicado_em, legenda, frase_frame0 (OCR ou legenda), cena_reconhecida, licenca}]}`.

Pacote da fila (`fila/AAAA-MM-DD/pacote.json`): `{data, longo: {fatos: [ids], titulo, descricao}, shorts: [{fato, tipo: A|B|C}], cartoes: [{cena, frase, layout}], stories: [{oferta}]}`.

## C. Agendador

Config (`publicador/config.json`, canal `gta`):

```json
{"gta": {"ativo": true, "idioma": "pt", "hora_longo_utc": 21, "longos_por_dia": 1,
  "shorts_por_dia": 3, "gap_shorts_min": 300, "hora_short_utc": 10,
  "cartoes_por_dia": 5, "gap_cartoes_min": 150, "hora_cartao_utc": 11,
  "stories_por_dia": 1, "hora_story_utc": 23,
  "lancamento": "2026-11-19", "fase_pos_lancamento": {"shorts": ["E","E","C"], "longos": ["F"]},
  "max_short_s": 25.0, "regra_frase_dias": 7}}
```

Regras, todas com caso de teste:

1. **Contagem**: `N = (lancamento - hoje_utc).days`; N ≤ 0 desliga o formato A e
   o placeholder `{N}` das frases. A narração do A é montada na hora:
   "Faltam N dias para GTA 6." + `narracao` do fato.
2. **Hora fixa por rede**: YouTube Short às 10, 15 e 20 UTC (7, 12 e 17 em
   Brasília); longo às 21 UTC (18 BRT, horário de TV); cartões IG das 11 às 23
   UTC a cada 150 min; story às 23 UTC (20 BRT) com a oferta do dia; TikTok
   espelha os cartões via Zernio com 30 min de atraso.
3. **Gap é alvo, não veto** (`gap_efetivo` do motor): encolhe até caber no dia,
   nunca abaixo de 60 min. O bloco do longo nunca cala o Short (defeito de
   03/09 já corrigido no código copiado).
4. **Dois crons** (`0 * * * *` e `30 * * * *`); execução em hora não devida sai
   antes de qualquer chamada de API.
5. **Alarme "publicou menos"**: o vigia compara os 3 dias UTC fechados com a
   config por rede e abre issue; silêncio > 12 h também.
6. **Troca pós-lançamento**: em `hoje >= lancamento`, `montar()` sorteia tipos
   de `fase_pos_lancamento`; se `colher_cc.py` ainda não entregou cena CC-BY, cai
   para B (trailer) e registra `fallback: sem_cc`.
7. **Repetição** (formato G): uma cena só volta com frase nova depois de 7 dias;
   nunca duas cenas do mesmo trecho de trailer (mesmo minuto) em posts
   consecutivos; `identidade` no máximo 1 a cada 4 cartões; `contagem` no
   máximo 2/dia.
8. **Cota YouTube**: 3 × 1.650 + 2.176 (longo com legenda, capa, playlist) +
   Realinhar 500 = **7.626/dia**, margem para 1 reenvio de Short (10.000). O
   `test_cota` copia a conta do motor e registra `SEM_MARGEM_DE_RETRY = []`.

## D. O cartão (`nucleo/cartao.py`)

Entradas: `cena.mp4` (1080p ou 4K do oficial), `inicio`, `fim`, `frase`,
`layout`, `identidade = {avatar.png 256², nome, handle, selo: bool}`,
`zoom=1.0, dx=0, dy=0`. Fonte: `marca/fontes/Inter-Bold.ttf` (repo). Saída
1080×1920, 30 fps, áudio original da cena (sem TTS), sem fade.

Filtergraph base (comum aos 3 layouts):

```
[0:v]trim=START:END,setpts=PTS-STARTPTS,fps=30[src];
[src]split=2[a][b];
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
   scale=108:192,boxblur=8:2,scale=1080:1920:flags=bicubic,eq=brightness=-0.28:saturation=1.15[bg];
[b]scale=iw*ZOOM:-2,crop=1080:ih:DX:0[fg];
[bg][fg]overlay=(W-w)/2:Y_VIDEO[v0];
[v0][1:v]overlay=X_AV:Y_AV[v1];              # avatar.png (input 1)
[v1]drawtext=fontfile=marca/fontes/Inter-Bold.ttf:text='NOME':x=X_NOME:y=Y_NOME:fontsize=40:fontcolor=white[v2];
[v2]drawtext=fontfile=...:textfile=frase.txt:x=(w-text_w)/2:y=Y_FRASE:fontsize=64:fontcolor=white:line_spacing=12:box=0[v3];
[v3][2:v]overlay=X_SELO:Y_SELO[vout]         # selo.png (input 2), só se selo=true
```

(`boxblur` em 108×192 e depois upscale: mesma névoa por 1/100 do custo, lição
do Reel cine.) `drawtext` não quebra linha sozinho: `cartao.py` quebra a frase
em ≤ 22 caracteres por linha antes de gravar `frase.txt`.

| layout | cabeçalho | vídeo | frase | rodapé |
|---|---|---|---|---|
| 1 "Twitter" | avatar 96 px + nome + selo + @handle, y 120 | 1080×1350 centrado, y 560 | 64 px, y 300, até 3 linhas | — |
| 2 "meme/notícia" | — | 1080×1350, y 420 | 72 px, y 150, até 3 linhas | avatar 80 px + nome, y 1800 |
| 3 "dividido" | — | vídeo 1080×960 em y 0; screenshot oficial 1080×760 em y 1160 | faixa 200 px em y 960, 60 px, 2 linhas | crédito 28 px, y 1880 |

Todos: rodapé fixo `Material oficial © Rockstar Games` (ou `Gameplay: <canal>
· CC BY`) em 26 px, canto inferior. Custo medido no motor atual: clipe de 10 s
com blur em miniatura e dois `drawtext` renderiza em **~6-9 s** no runner de 2
núcleos (`libx264 -preset veryfast -crf 23`); 5 cartões/dia = menos de 1 min.
Short narrado (formato A/B): ~40 s. Longo de 20 min com fundo estático: ~8 min.

## E. O ranqueador (`produzir/ranquear_perfil.py`)

`python produzir/ranquear_perfil.py --rede ig --perfil gta6club --top 30`

| rede | como | o que sai |
|---|---|---|
| Instagram | GraphQL replay pelo Chrome (memória `varrer-instagram-pelo-chrome`): abre o perfil, captura a resposta `xdt_api__v1__feed__user_timeline_graphql_connection`, pagina até `top`; roda **local** (workflow não tem Chrome logado) | views (`play_count`), likes, comentários, duração, legenda, `video_url` (não baixado), thumbnail |
| YouTube | Data API: `search.list(q, type=video, videoDuration=short, order=viewCount, publishedAfter=hoje-30d)` + `videos.list(part=statistics,contentDetails,status)` — 100 + 1 unidades por 50 vídeos; roda no Actions | views, likes, duração, título, `status.license` (`creativeCommon` marca `licenca`) |
| TikTok | página pública `tiktok.com/@perfil` → JSON `__UNIVERSAL_DATA_FOR_REHYDRATION__`; best-effort, quebra quando o TikTok muda | views, likes, duração, descrição |

Para cada vídeo: baixa **só a thumbnail** (1º frame) para `benchmark/`, OCR com
`rapidocr-onnxruntime` (pip puro, sem binário de sistema) para ler a frase do
cartão, e reconhece a cena comparando um hash perceptual (`imagehash`) com os
frames de `cenas.json`. Download do MP4 **só** se `licenca == cc-by`.
Rotina semanal (domingo 06 UTC, workflow `benchmark`): roda no YouTube contra
`"gta 6"` e contra o **nosso** canal; a rodada de Instagram é manual, local.
Relatório: `benchmark.json` + 10 linhas em `benchmark/RESUMO.md` (mediana de
views por faixa de duração, frases mais repetidas, cenas mais usadas).

## F. Pipeline E/F (pós 19/11)

1. `search.list(q="GTA 6 gameplay", videoLicense=creativeCommon, type=video,
   order=viewCount, publishedAfter=2026-11-19, videoDefinition=high)`, 50 por
   rodada; `videos.list` para duração (1-20 min) e `status.license` (confirmar).
2. yt-dlp `-f "bv*[height<=1080]+ba"` para `marca/cc/<videoId>.mp4` (gitignorado).
3. `nucleo/cenas.py` corta em cenas de 6-12 s; cena entra em `cenas.json` com
   `licenca: cc-by`, `credito: "<título do canal>"`, `video_origem: cc:<id>`.
4. Formato E = cena CC + narração de fato (`fatos` com tag `gameplay`, que o
   Opus escreve depois do lançamento a partir do que o vídeo mostra) + rodapé
   `Gameplay: <canal> · CC BY` + linha na descrição com o link do original.
5. Formato F = 8-12 cenas CC do mesmo tema + narração encadeada (guia), 15-20
   min, capítulos na descrição, crédito de cada canal.
6. Registro: `fontes/PROVENIENCIA.md` ganha uma linha por `videoId` (data,
   canal, licença lida da API). Se a API deixar de reportar `creativeCommon`
   para um id já usado, o vigia abre issue "licença mudou".

## G. Notícias (formato C)

Fontes, nesta ordem: Newswire da Rockstar (página `/newswire` filtrada por
"Grand Theft Auto VI"; sem RSS confiável, é scrape de HTML com cache do último
id), IGN, GameSpot (RSS público). `produzir/noticias.py` roda no reabastecer
(6 h): título + 2 primeiros parágrafos → resumo de 40 palavras em pt-BR por
Haiku 4.5, com `nota` 1-10 de "é fato ou rumor" e `rotulo` (`oficial` se a
fonte é Rockstar/Sony/Take-Two, `rumor` caso contrário). **Teto: 8 chamadas/dia**
(`NOTICIAS_TETO`), custo abaixo de US$ 0,05/dia. Regra: `rumor` só entra se a
fonte for grande e o gancho começar com "Rumor:"; `oficial` vira Short do dia
com prioridade sobre o A/B. Ao implementar, o Opus carrega a skill `claude-api`
para o cliente e o id do modelo.

## H. Marca

Nome e handle (conferidos por `curl -o /dev/null -w %{http_code}
youtube.com/@handle` em 22/09/2026; `search.list` confirma na fundação):

| opção | handle | YouTube | leitura |
|---|---|---|---|
| **Rumo a Vice City** (recomendado) | `@rumoavicecity` | livre (404) | funciona antes e depois do lançamento; "GTA 6" entra nas keywords, nos títulos e na bio, não no nome (menos risco de marca) |
| GTA 6 em Dia | `@gta6emdia` | livre | melhor para busca, pior para marca registrada |
| Diário de Leonida | `@leonidadiario` | livre | mais autoral, menos busca |

`@vicecitybr` e `@diariodeleonida` já existem. Instagram e TikTok: conferir no
cadastro (curl devolve 200 para tudo). Título do canal: "Rumo a Vice City ·
GTA 6". Bio: "Tudo sobre GTA 6, todo dia, até 19/11. Pré-venda e controle
oficial no link." + link único da vitrine.

Voz TTS: `pt-BR-ThalitaMultilingualNeural` (edge-tts; a casa usa Antonio e
Francisca). O Opus confirma com `edge-tts --list-voices | grep pt-BR`; se não
existir no runner, `pt-BR-AntonioNeural` com `rate=+6%` e `pitch=-2Hz` (não é
a mesma assinatura do psicologia-fria).

Paleta (`marca/paleta.json`): fundo `#0B0716`, rosa `#FF3EA5`, ciano `#35E0FF`,
laranja de pôr do sol `#FF8A3D` só em capa, texto `#FFFFFF`. Avatar: palmeira
em silhueta rosa sobre gradiente noturno, sem logo da Rockstar (marca de
terceiro no avatar é motivo de derrubada de perfil). Selo do cartão: círculo
ciano com check branco (não é o selo azul do Instagram, que é da Meta). Banner:
horizonte de Vice City em gradiente + "Rumo a Vice City" + contagem ("19/11").
Capa do longo: `thumbnail.py` com a screenshot oficial em gradação de noite +
título até 210 px + selo "TUDO SOBRE GTA 6".

## I. Poço e frases — GRAVADOS

- `conteudo/fatos/01-lancamento-trailers.json` (F001-F030), `02-personagens-lugares.json`
  (F031-F060), `03-mecanicas.json` (F061-F100), `04-edicoes-contagem.json`
  (F101-F150). 150 fatos, cada um com fonte, gancho ≤ 10 palavras, narração
  35-55 palavras, cena e tags. Validado por script em 22/09 (ver RETOMAR).
- `conteudo/frases.json`: 40 frases em 4 categorias (identidade, fato,
  pergunta, contagem), com `{N}` para a contagem.
- Premissas: as descrições oficiais de personagens vêm da galeria/site via
  GTABase (transcrição); as de lugares estão em palavras próprias porque a
  página oficial não pôde ser lida por script (o Opus confere ao baixar a
  galeria e troca para a citação literal se houver). Rumor não entrou em
  nenhum fato. Spoiler: nada além do que os três vídeos mostram.
- ⚠ Um fato leva número de terceiro que precisa de checagem antes de ir ao ar:
  F110 (470 mi da franquia / 230 mi de GTA 5, fonte Sportskeeda). Marcar
  `revisar: true` até o Opus achar a fonte primária (relatório da Take-Two).

## J. O que só o Diego pode fazer (em ordem, com tempo)

| # | tarefa | tempo | onde |
|---|---|---|---|
| 1 | Criar conta Google nova (nome do canal, senha no gerenciador), 2FA | 10 min | accounts.google.com |
| 2 | Criar o canal no YouTube nessa conta, handle `@rumoavicecity` | 5 min | youtube.com |
| 3 | Projeto Google Cloud próprio → ativar YouTube Data API v3 + Analytics API → tela de consentimento **em produção** → credencial OAuth "app de desktop" → baixar JSON | 20 min | console.cloud.google.com |
| 4 | Rodar `python produzir/autorizar.py --canal gta` no PC (abre o navegador) → token; colar `YT_CLIENT_SECRET_GTA` e `YT_TOKEN_GTA` nos secrets do repo | 10 min | terminal + github.com/settings |
| 5 | Verificação do canal por telefone (libera capa personalizada e Shorts > 60 s) | 5 min | youtube.com/verify |
| 6 | Conta Instagram nova → converter em Profissional → vincular a uma Página do Facebook nova; contato confirmado por alias do Gmail (armadilha paga) | 20 min | app do Instagram + facebook.com |
| 7 | Token de longa duração da Graph API (app da Meta já existente do psicologia-fria pode ser reutilizado: adicionar a conta nova) → `IG_TOKEN_GTA`, `IG_USER_ID_GTA` | 15 min | developers.facebook.com |
| 8 | Conta TikTok nova (business, para link na bio sem mínimo de seguidores) → conectar no Zernio → `ZERNIO_KEY_GTA` | 15 min | tiktok.com + zernio |
| 9 | Shopee Afiliados: gerar links dos produtos de `ofertas.json` com `src=` (o Opus deixa a lista pronta) e criar a vitrine | 15 min | affiliate.shopee.com.br |
| 10 | Colar a bio e o link único nas três redes; avatar e banner o script aplica | 5 min | apps |

Total: ~2 h, uma vez. Depois disso o Diego não participa.

## K. Suíte de testes mínima (sem rede)

| arquivo | casos |
|---|---|
| `test_agenda.py` (copiado) | gap alvo, cron :30, gap do longo não cala Short, **novo**: N ≤ 0 desliga A, troca A/B → E/F na data, fallback sem CC |
| `test_cota.py` (copiado) | 7.626/dia + 1 reenvio < 10.000; `SEM_MARGEM_DE_RETRY` vazio |
| `test_poco.py` (copiado e ampliado) | ids únicos, gancho ≤ 10, narração 35-55, fonte http, cena resolvível, `revisar: true` bloqueia publicação |
| `test_cartao.py` (novo) | quebra de linha ≤ 22 chars, 3 layouts geram filtergraph válido (`ffmpeg -filter_complex ... -f null`), rodapé de crédito presente, duração de saída = fim − inicio |
| `test_escalar.py` (novo) | mesma cena não repete em 7 dias, sem duas cenas do mesmo minuto seguidas, identidade ≤ 1 em 4, contagem ≤ 2/dia, toda frase da fila existe em `frases.json` |
| `test_config.py` (novo) | todo link de `ofertas.json` tem `src=` e `vigencia.ate`; cena sem `licenca` reprovada; `licenca: cc-by` exige `credito` |
| `test_vigia.py` (copiado) | "publicou menos" por rede |

## L. Réguas (de `PLANO.md` §6) e o que se desliga

| data | régua | se falhar |
|---|---|---|
| 30/09 | render local OK em A, B, D, G; 1º post no ar | não abre a fase 1 até fechar; nada mais muda |
| 15/10 | YT: mediana 7 d ≥ 1.000 views/Short · IG: ≥ 2.000/Reel | trocar UMA variável por vez, nesta ordem: gancho → layout do cartão → voz. Uma por semana |
| 01/11 | ≥ 300 inscritos no YT | desliga o longo (formato D), fica só Short; cartões do IG continuam |
| 05/12 | 1º clique/venda no `src=` da Shopee | troca a oferta principal (jogo → DualSense → camiseta), nunca a bio inteira |
| 31/12 | sem venda | 1 post/dia por rede, ativo dormente; nada de horas humanas |
| 2027 | 1.000 inscritos + 10 mi views/90 d | submete ao YPP; até lá o afiliado é a única receita |
