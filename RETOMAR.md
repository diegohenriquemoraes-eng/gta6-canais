# RETOMAR — gta6-canais

## O que é

Canais automáticos sobre GTA 6 — YouTube (3 Shorts + 1 longo/dia), Instagram
(5 cartões + 1 story/dia) e TikTok (espelho) — monetizando por link de afiliado
da Shopee na bio. Custo zero, 100 % na nuvem, sem assinar ferramenta.
Lançamento do jogo: **19/11/2026**.

Plano em `PLANO.md`; engenharia reversa do ViceScale (a ferramenta que
replicamos, sem assinar) em `VICESCALE.md`; especificação em `ARQUITETURA.md`;
prompts em `PROMPT.md`. O BLOCO 1 (Fable 5.1) e o **BLOCO 2 (Opus 5, 22/09/2026)
já foram executados** — não repetir nenhum dos dois.

## O que está pronto e testado (22/09/2026)

**O motor inteiro roda local, ponta a ponta.** `python -m unittest discover -s
testes` → **84 casos verdes**, sem rede, em ~4 s.

| peça | estado |
|---|---|
| `nucleo/` (tts, legendas, render, thumbnail, música, playlists, youtube_api) | copiado do `Palavra-Viva-3x` e podado (sai bíblia/idiomas/Openverse) |
| `nucleo/canal.py` | identidade do canal: voz, tags, CTA, rodapé, data do lançamento |
| `nucleo/fabrica.py` | `montar_short` (A/B/C/E) e `montar_longo` (D/F) sobre o poço de FATOS |
| `nucleo/cartao.py` | formato G, 3 layouts, com clipe **ou** foto da galeria |
| `nucleo/cenas.py` + `produzir/marcar_cenas.py` | 31 cenas dos trailers (28 descritas à mão) |
| `produzir/cenas_da_galeria.py` | +162 fotos oficiais viram cena → **190 cenas aptas** |
| `produzir/escalar.py` | cena × frase → fila, com as 5 regras de repetição |
| `produzir/reabastecer.py` | pacotes de hoje+2, longo temático rotativo |
| `conteudo/fatos/` | **218 fatos** com fonte, gancho e cena — 6 arquivos; cobre até ~01/12 a 3 Shorts/dia |
| `produzir/noticias.py` | formato C (Newswire + IGN + GameSpot), teto de 8 chamadas/dia |
| `produzir/ranquear_perfil.py` | o "Vice Scrap": YouTube, Instagram (Chrome) e TikTok |
| `produzir/colher_cc.py` | gameplay CC BY, com trava de data em 19/11 |
| `produzir/vigia.py` | 6 alarmes, incluindo "publicou menos que a config" |
| `produzir/medir_desempenho.py` · `realinhar_publicados.py` · `aplicar_marca.py` | prontos, esperando token |
| `produzir/conferir_instalacao.py` | confere repo, secrets, config, token, ofertas, cenas e fila; diz o comando de cada pendência |
| `marca/` | avatar, banner, selo, paleta — procedurais, sem nada da Rockstar |
| 7 workflows | publicar (2 crons/h), reabastecer (6 h), testes (todo push), vigia (2×/dia), medir, realinhar, colher-cc |

**Renderizado e conferido no olho:**

| formato | resultado |
|---|---|
| A (Short de contagem) | 19,9 s, 1080×1920, áudio = vídeo, gancho no frame zero, rodapé de crédito, fundo de screenshot oficial |
| D (longo "tudo o que sabemos") | **16,5 min (990 s), 55,9 MB**, 44 fatos, capa com selo, legenda `.srt` gerada, áudio = vídeo (990,27 / 990,25) |
| G (cartão) | os 3 layouts, com clipe do trailer; e o cartão de foto da galeria com zoom lento + trilha procedural |

Render no PC do Diego: Short ~40 s, cartão 28-40 s, longo ~15 min. O runner do
Actions tem 2 núcleos e o job do Publicar tem teto de 110 min — cabe.

## 🟢 NO AR desde 23/09/2026 — as DUAS redes publicam sozinhas

**YouTube `@rumoavicecity` (`UCUJdsMoY_H4hLlvckVjCcEg`).** Primeiro vídeo:
https://youtu.be/evMAZGzD5fY — renderizado e publicado inteiramente no runner
do GitHub, sem PC ligado.

**Instagram `@rumoavicecity`.** Primeiro Reel:
https://www.instagram.com/reel/18209930776368705/ — cartão do formato G,
layout 1, renderizado no runner a partir do acervo oficial e publicado pela
Graph API. Ponta a ponta: render → asset de Release → container → publicação →
estado commitado.

- Conta Google **`gta6diegomoraes@gmail.com`** — ⚠ neste Chrome ela é
  **`authuser=4`**; sem esse parâmetro os links do console e do Studio caem na
  conta que tem os outros canais da casa.
- Projeto Cloud `ageless-fire-509501-r8`, Data API v3 + Analytics API ativas.
- **App OAuth EM PRODUÇÃO** — o token não expira mais (ver a armadilha abaixo).
- Secrets `YT_CLIENT_SECRET_GTA` e `YT_TOKEN_GTA` no repo; banner, bio,
  keywords e idioma aplicados por API.

## Feito em 22/09, tarde (rodada "faça você")

- Repo `gta6-canais` e `gta6-media` **públicos**; 7 workflows ativos; a suíte
  passa no runner do GitHub.
- **Shopee fechada**: 6 produtos medidos (preço, vendas, comissão reais) e
  **36 links de afiliado gerados** (6 × 6 origens), com Sub_id por origem.
- **Instagram @rumoavicecity** criado em `gta6diegomoraes@gmail.com`,
  convertido em conta profissional de Criador, com foto de perfil e bio no ar.
- `produzir/instalar.py` — um comando para tudo o que vem depois de criar a
  conta (acha o JSON do Cloud, autoriza, grava o channel_id, sobe os secrets,
  aplica a marca) e para o Instagram (descobre o IG_USER_ID sozinho).
- `produzir/conferir_instalacao.py` — diz em uma tela o que falta.

⚠ **O jogo GTA 6 de PS5 não existe na Shopee.** A oferta principal do plano
(pré-venda a R$ 449, ~R$ 13/venda) foi substituída por quadro (R$ 4,75/venda),
capa de PS5 (30 % de comissão) e camiseta. **R$ 1.000/mês passam a ser ~210
vendas, ou 7 por dia** — a conta honesta do projeto piorou em tíquete e
melhorou em facilidade de conversão. Detalhe em `conteudo/ofertas.json`.

⚠ **O rastreador da Shopee é o Sub_id, não `?src=`**: o campo só aceita
alfanumérico e o encurtador descarta parâmetro colado na URL. Como o link curto
não mostra o Sub_id, a rastreabilidade é **declarada** no campo `subid` — e é
isso que `test_config` exige.

## O que está pronto ESPERANDO secret

Nada disso é código faltando — é conta que só o Diego pode criar.
Passo a passo em **`PENDENCIAS-DIEGO.md`** (~2 h, uma vez).

- ~~YouTube~~ — **pronto e no ar.** Falta só `YT_TOKEN_ANALYTICS_GTA`
  (opcional: `python produzir/instalar.py analytics`), que mede hora contável.
- ~~Instagram~~ — **pronto e no ar.** App próprio da Meta `3300084843713046`,
  secrets `IG_USER_ID_GTA` e `IG_TOKEN_GTA` no repo. ⚠ **Reaproveitar o app do
  `psicologia-fria` NÃO funcionou**: para adicionar a conta como testadora, a
  Meta exige que ela tenha *conta de desenvolvedor do Facebook* — e
  `@rumoavicecity` é conta de Instagram pura ("O formulário não pode ser
  salvo"). Daí o app próprio.
  ⚠ **O token está exposto no histórico da conversa de 22/09** (foi colado em
  texto puro no chat). Regerar pela Meta quando der — regerar invalida o antigo.
- TikTok: `ZERNIO_KEY_GTA` (e `tiktok.ativo: true`). Zernio já logado.
- Notícias: `ANTHROPIC_API_KEY` (sem ele o resumo de emergência entra com nota 6
  e a notícia **não** vira Short sozinha — de propósito)
- Shopee: **fechada**, nada a fazer.

## O que falta, em ordem

1. ~~Tornar o repo público~~ — **feito em 22/09** (`gta6-canais` e
   `gta6-media`, os dois públicos; o repo foi auditado antes e não tem token,
   chave nem credencial no código ou no histórico). Os 7 workflows estão ativos
   e a suíte de 81 testes já passou no runner (47 s).
2. Diego faz os passos de `PENDENCIAS-DIEGO.md` — **só criar conta e login**,
   com as abas já abertas no Chrome na ordem certa.
3. Depois de cada passo: `python produzir/conferir_instalacao.py` diz em uma
   tela o que está de pé e o que falta, com o comando de cada pendência.
4. Fase 0 fecha em **30/09** com o 1º post no ar.

## Decisões que não se reabrem

- ViceScale não se assina: a mecânica está replicada no motor da casa.
- Arquivo de vídeo **só de fonte limpa** (Rockstar oficial, CC BY com crédito).
  Vídeo de outra página serve para MEDIR formato, nunca para postar.
- **Uma cena recebe uma frase por 7 dias**, e a trava vale para a CENA e para o
  PAR cena+frase — não para a frase sozinha (40 frases para 35 cartões/semana
  torna isso aritmeticamente impossível, e o que a política do Instagram chama
  de repetitivo é o arquivo repetido, não a legenda parecida).
- Canal em conta Google **NOVA**, nunca a dos 5 canais bíblicos.
- Link de afiliado **nunca** sobre imagem da Rockstar; só bio, descrição e story.
- Camada autoral em todo post: narração própria de fato no YouTube, cartão com
  frase própria no IG/TikTok. É o que separa monetizável de "reused".
- Nome: **Rumo a Vice City / @rumoavicecity**. Voz:
  `pt-BR-ThalitaMultilingualNeural` (Antonio e Francisca já são da casa).
- **O longo NÃO consome o poço.** Ele é compilação temática rotativa (6 temas em
  ciclo, título e capa próprios). Medido em 22/09: com alvo de 18 min um longo
  leva ~55 fatos — se consumisse o poço como o Short, os 150 fatos acabariam em
  TRÊS dias.

## Armadilhas já pagas

As do `Palavra-Viva-3x/CLAUDE.md` e do `psicologia-fria/CLAUDE.md` valem
inteiras (`-framerate 30`, cron nunca esparso, state versionado, tags
comparadas por CONJUNTO, contato confirmado do IG por alias do Gmail, TikTok só
via Zernio). E estas, novas, todas medidas em 22/09/2026:

- ⚠ **O "An Extended Look" tem RESTRIÇÃO DE IDADE no YouTube.** O yt-dlp exige
  cookies de conta logada e o runner não tem navegador. Consequência aceita: o
  ARQUIVO de vídeo do pipeline é trailer 1 + trailer 2; o Extended Look continua
  sendo FONTE de fatos (os timestamps já estão no poço), mas as cenas dele saem
  marcadas `no_runner: true` e o `escalar.py` as ignora.
- ⚠ **`scdet` com limiar 0,35 não acha corte nenhum.** Achou 1 corte no Trailer 1
  inteiro e zero no Trailer 2, e o resultado eram "cenas" de 12 s fatiadas no
  relógio. Com 0,10 (o padrão do filtro) os cortes reais aparecem: 43 e 54.
- ⚠ **A zona de vídeo do cartão é 1080×608, não 1080×1350.** O desenho original
  supunha fonte vertical; os trailers são 16:9 e recortar para 1350 px exigiria
  ampliar 2,2×. O primeiro render saiu com tarja preta de 700 px e, no layout 3,
  a frase por cima da foto.
- ⚠ **O selo do cartão em x fixo caiu em cima do nome.** Agora a largura do nome
  é medida com a mesma fonte (`cartao.largura_texto`).
- ⚠ **`galeria: logo GTA VI` casava com o logo do GTA+**, e o primeiro Short saiu
  com a marca do GTA+ ocupando a tela. Agora o casamento ignora palavras vazias
  (`gta`, `vi`, `logo`, `art`…) e, quando não casa, `cenas.fundo_para_fato` cai
  numa foto da galeria que compartilhe TAG com o fato.
- ⚠ **`gap_shorts_min` de 300 não fecha o dia.** Contra as execuções que o cron
  do GitHub entrega de verdade (~6/dia), o 2º e o 3º Short caíam fora do dia.
  Está em 180, e o `test_agenda` replica o cron real para provar.
- ⚠ **A galeria oficial não sai por script simples** (`rockstargames.com/VI/media`
  monta por JavaScript). Saiu pelo Chrome: as 308 URLs estão em
  `marca/oficial/galeria-urls.txt` e o downloader do `baixar_oficial.py` as usa.
- ⚠ **App OAuth em "Testando" mata o canal em 7 dias**, e publicar não é um
  clique: o console só libera "Publicar app" quando a página de *Branding* tem
  página inicial, política de privacidade e termos, e só aceita URLs de um
  domínio **pré-registrado** em "Domínios autorizados". Resolvido em 22/09 sem
  depender de servidor nem DNS: as três páginas estão em `docs/`, publicadas
  por **GitHub Pages** em `diegohenriquemoraes-eng.github.io/gta6-canais/`, e
  esse é o domínio autorizado. O app está **Em produção**.
- ⚠ **`git add` de caminho inexistente derruba o passo do workflow** (exit 128).
  Aconteceu no primeiro Short publicado de verdade: o vídeo subiu e o estado
  NÃO foi commitado, porque `publicacoes-ig.md` ainda não existia — e sem
  estado a execução seguinte recontaria o dia. Os 4 workflows agora filtram os
  caminhos existentes antes do `git add`.
- ⚠ **O runner não baixa os trailers**: o YouTube devolve "Sign in to confirm
  you're not a bot" para o yt-dlp em IP de datacenter. O Short sobrevivia
  (cai no gradiente), mas **o CARTÃO do Instagram simplesmente falhava** — ele
  precisa do arquivo de verdade (`origem de trailer2-013 ausente`). Resolvido
  em 23/09: `produzir/subir_acervo.py` empacota trailers + galeria **reduzida a
  1080 px** (487 MB → **110 MB**; o render nunca usa mais que 1080 de largura)
  e sobe para o Release `acervo` do repo de mídia. `baixar_oficial.py` agora
  tenta o Release PRIMEIRO e só cai no yt-dlp quando roda no PC. O runner passou
  a ver 2 vídeos e 308 imagens.
- ⚠ **O `GITHUB_TOKEN` do Actions escreve APENAS no repo que o executa.** O
  cartão renderizou no runner e morreu em
  `gh release create cartoes -R .../gta6-media` com exit 1. Ler de outro repo
  público é livre (é assim que o acervo chega); escrever, não. Por isso
  `instagram.repo_midia` aponta para **este** repo — asset de Release não entra
  no clone, então não incha o Git, e um PAT em secret seria segredo a mais por
  nada. `test_config` trava isso.
- ⚠ **Foto clara de GTA come o texto do longo.** O fundo do longo herdou o
  escurecimento do motor bíblico (-0,34), pensado para foto noturna; com
  screenshot de praia ao meio-dia o cabeçalho ciano sumia no céu. Agora há duas
  faixas `drawbox` translúcidas no topo e no rodapé — contraste garantido em
  qualquer foto, e a imagem continua parecendo GTA.
- ⚠ **A Shopee bloqueia acesso automatizado enquanto deslogada**: a busca do
  site devolve a página de verificação anti-robô. **Logado no portal de
  afiliados, tudo funciona** — a lista de produtos sai de
  `/api/v3/offer/product/list` (preço, vendas e as três taxas de comissão) e o
  Link personalizado gera até 5 links por vez com Sub_id.
- ⚠ **7 das 10 frases de "fato" dos cartões vinham do VAZAMENTO de 2022**, e
  uma era falsa: *"o romance entre Jason e Lucia é opcional"* — a Rockstar diz
  que a FORÇA dessa relação muda a história e o final. Três cartões com ela já
  estavam na fila. Frase de cartão é queimada no pixel e, ao contrário do fato,
  **não tem campo `fonte`** — ninguém a auditava. As dez foram reescritas a
  partir de fatos do poço, a fila foi corrigida sem tocar no que já publicou, e
  `test_poco` ganhou duas travas: a frase de `fato` tem de espelhar UM fato do
  poço (≥ 2 palavras e ≥ 60 % de cobertura, contra um fato só — contra o poço
  inteiro o vocabulário é largo demais) e uma lista de termos proibidos
  (`testemunha`, `opcional`, `animacoes`, `clonador`, `80 horas`,
  `perfil criminal`), porque peneira de vocabulário não pega frase que fala do
  assunto certo e afirma o contrário.
- ⚠ **Instagram: o link da bio e o nome de exibição só saem pelo APP do
  celular.** A própria tela do web avisa sobre o link; o campo do nome resiste
  à automação e o Instagram só permite 2 trocas em 14 dias, então não se
  insiste às cegas.

## Réguas (de `PLANO.md` §6)

| data | régua | se falhar |
|---|---|---|
| 30/09 | 1º post no ar nas duas redes | não abre a fase 1 |
| 15/10 | YT mediana 7 d ≥ 1.000 views/Short · IG ≥ 2.000/Reel | trocar UMA variável por semana: gancho → layout → voz |
| 01/11 | ≥ 300 inscritos no YT | desliga o longo, fica só Short |
| ~~08/11~~ **01/12** | o poço foi a **218 fatos** em 23/09 e agora passa do lançamento com 12 dias de folga | o vigia avisa abaixo de 9 livres |
| 05/12 | 1º clique/venda no `src=` da Shopee | troca a oferta principal (jogo → DualSense → camiseta) |
| 31/12 | sem venda | 1 post/dia por rede, ativo dormente |

## Pendências do Diego

Tudo em **`PENDENCIAS-DIEGO.md`**, em ordem, com link de cada site. Resumo:
repo público → conta Google nova → canal + verificação por telefone → projeto
Cloud → token → Instagram + Página do Facebook → TikTok/Zernio → Shopee → bio.
