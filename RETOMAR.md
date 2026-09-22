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
testes` → **81 casos verdes**, sem rede, em ~5 s.

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

## O que está pronto ESPERANDO secret

Nada disso é código faltando — é conta que só o Diego pode criar.
Passo a passo em **`PENDENCIAS-DIEGO.md`** (~2 h, uma vez).

- YouTube: `YT_CLIENT_SECRET_GTA`, `YT_TOKEN_GTA` (+ `YT_TOKEN_ANALYTICS_GTA`)
- Instagram: `IG_USER_ID_GTA`, `IG_TOKEN_GTA` + repo público `gta6-media`
- TikTok: `ZERNIO_KEY_GTA` (e `tiktok.ativo: true`)
- Notícias: `ANTHROPIC_API_KEY` (sem ele o resumo de emergência entra com nota 6
  e a notícia **não** vira Short sozinha — de propósito)
- Shopee: `conteudo/ofertas.json` está montado com os 6 produtos e a vigência de
  cada um, **faltando preço, vendidos, comissão e os links com `src=`**

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
- ⚠ **Foto clara de GTA come o texto do longo.** O fundo do longo herdou o
  escurecimento do motor bíblico (-0,34), pensado para foto noturna; com
  screenshot de praia ao meio-dia o cabeçalho ciano sumia no céu. Agora há duas
  faixas `drawbox` translúcidas no topo e no rodapé — contraste garantido em
  qualquer foto, e a imagem continua parecendo GTA.
- ⚠ **A Shopee bloqueia acesso automatizado**: a busca devolve a página de
  verificação anti-robô e `affiliate.shopee.com.br` redireciona para o login.
  O passo virou pendência do Diego, com o JSON já montado.

## Réguas (de `PLANO.md` §6)

| data | régua | se falhar |
|---|---|---|
| 30/09 | 1º post no ar nas duas redes | não abre a fase 1 |
| 15/10 | YT mediana 7 d ≥ 1.000 views/Short · IG ≥ 2.000/Reel | trocar UMA variável por semana: gancho → layout → voz |
| 01/11 | ≥ 300 inscritos no YT | desliga o longo, fica só Short |
| **~08/11** | **o poço de 150 fatos seca a 3 Shorts/dia** | escrever fatos novos antes disso (o vigia avisa abaixo de 9 livres) |
| 05/12 | 1º clique/venda no `src=` da Shopee | troca a oferta principal (jogo → DualSense → camiseta) |
| 31/12 | sem venda | 1 post/dia por rede, ativo dormente |

## Pendências do Diego

Tudo em **`PENDENCIAS-DIEGO.md`**, em ordem, com link de cada site. Resumo:
repo público → conta Google nova → canal + verificação por telefone → projeto
Cloud → token → Instagram + Página do Facebook → TikTok/Zernio → Shopee → bio.
