# ViceScale — engenharia reversa e réplica a custo zero (22/09/2026)

Fontes: vicescale.com e /97-vitalicio (texto integral), termos de uso, página
"Indique e Ganhe" (50 % de comissão por venda), mockups do site (`main.mp4`,
`clip-1..15.mp4`, `Passo-1..3.png`), e os dois vídeos do autor Heron Reis no
YouTube: "Como funciona a ViceScale" (GvTMKu8_3bU, 10:47, 139 views, 11/09/2026)
e "MEU PLANO pra FAZER R$5.000 POR MÊS com GTA 6 (me copie)" (jNZGcdVa99U,
23 min). Transcrições lidas na íntegra.

## 1. O método que ele ensina (o vídeo de 23 min)

1. Criar uma **página dark** de GTA 6 no Instagram (anônima; nome, bio, logo).
2. Achar páginas BR e gringas que já viralizam GTA (exemplo dele: "GTA 6 Club",
   27 mil seguidores, vídeos de 58 mil a 1 mi de views, link da Amazon/grupo de
   WhatsApp na bio).
3. **Reciclar** os vídeos delas em volume: meta de **10 posts/dia**, 900 em 3
   meses.
4. Monetizar por (a) afiliado Shopee/Amazon/Mercado Livre em stories e bio,
   (b) monetização por views do Instagram "quando chegar ao Brasil",
   (c) infoproduto próprio ou afiliado (Hotmart/Kiwify/Cakto).
5. A prova de renda: "R$ 3.200 numa semana" com stories de uma página de 1 mi
   de seguidores **de outro nicho** (frutas falantes), vendendo produto
   doméstico para mulheres 40+. Nada da página de GTA dele.

## 2. O que a ferramenta faz de verdade (o vídeo de 10 min)

| Aba | O que faz | Como aparece |
|---|---|---|
| **Vice Scrap** | Cola link ou @ do perfil → lista todos os posts → filtro por mais curtidos / comentados / **views** / recentes → seleciona N → "baixar selecionados" grava os MP4 no PC | É a peça que a página de vendas omite |
| **Templates** | 3 modelos: (1) "Twitter": cabeçalho com avatar + nome + selo azul, frase, vídeo embaixo; (2) "meme/notícia": frase no topo, vídeo, avatar no rodapé; (3) "vídeo viral": tela dividida, vídeo em cima, imagem/vídeo embaixo, frase no meio. Preset **blur** (o próprio clipe borrado preenche o fundo). Zona de vídeo com corte, zoom, deslocamento H/V por clipe. Estilo de texto: fonte, cor (branco), tamanho, margens | `Passo-1.png`, `clip-*.mp4` |
| **Legenda + IA** | Frase padrão ("Você encontrou a página que fala tudo sobre GTA 6") → botão gera 5 variações ("A página perfeita para quem quer saber de GTA", "Tudo que você precisa saber de GTA"...) | |
| **Scale** | 10 vídeos × 5 frases = **50 variações**: sorteia vídeo e frase; o mesmo vídeo sai 5 vezes com frases diferentes "para testar" | `Passo-2.png` (fila de render) |
| **Publicação** | Conecta Instagram profissional; "publicar tudo" com data inicial + intervalo (5 min a 3 h); legenda do post manual ou por IA; TikTok/YouTube listados na integração mas a automação é só IG | `Passo-3.png` |
| **Pack Viral** | "packs, ganchos e peças" prontos, origem não declarada nos termos | risco: material de terceiro |
| **Editor** | corte simples sem timeline | |

Detalhe que decide tudo: **os clipes de demonstração são cenas do Trailer 2 da
Rockstar** (festa na piscina, ringue de luta, carro à noite, Lucia). As páginas
"virais" copiadas já são cortes do trailer. A fonte primária está em
rockstargames.com/VI, em 4K, de graça.

## 3. Réplica, peça por peça

| Peça do ViceScale | Nossa réplica (custo zero, no repo `gta6-canais`) | Diferença deliberada |
|---|---|---|
| Vice Scrap (perfil → ranking → download) | `produzir/ranquear_perfil.py`: Instagram via GraphQL replay no Chrome (memória `varrer-instagram-pelo-chrome`), YouTube via Data API (`search` + `videos.list` por `viewCount`), TikTok via página pública. Saída: `conteudo/benchmark.json` com views, duração, frase do cartão (OCR do 1º frame), cena reconhecida | **Baixa para medir, não para postar.** Só baixa arquivo para reuso se a licença for CC (YouTube `videoLicense=creativeCommon`). Roda também na NOSSA página, semanal: é a métrica de qual frase/cena rende |
| Templates 1/2/3 + blur | `nucleo/cartao.py` (ffmpeg): os 3 layouts em 1080×1920; fundo = clipe com `boxblur` + escurecido; cabeçalho avatar + nome + selo; frase em fonte do repo; zona de vídeo com `inicio/fim/zoom/dx/dy` por clipe | igual |
| Frase padrão + 5 variações por IA | `conteudo/frases.json`: 40 frases-base por categoria (identidade da página, fato, pergunta, contagem) + gerador de variações com LLM barato e teto diário; cada frase tem `usada_em` | frase casada com a cena (fato), não sorteada |
| Scale 10 × 5 = 50 | `produzir/escalar.py`: `clipes × frases → fila`, com **1 frase por clipe por 7 dias** e nunca 2 posts seguidos da mesma cena | evita o "repetitivo" que o IG rebaixa desde 30/04/2026 |
| Publicação automática IG com intervalo | `psicologia-fria/src/publicar.py` (Graph API, Release como hospedagem) + `intervalo_min` no config; Story diário com a oferta (`src=ig_story`) | já existe; ganha TikTok via Zernio e YouTube via publicador |
| Pack Viral | `marca/oficial/`: trailers 1, 2, Extended Look (yt-dlp do canal Rockstar), 99 screenshots + artworks; `fontes/PROVENIENCIA.md` | origem declarada |
| Editor | campos `inicio/fim/zoom` no pacote; cortes de cena pré-marcados em `conteudo/cenas.json` (timestamp + descrição) | igual |
| Cadastro fechado, fila de render, suporte | GitHub Actions público (minutos ilimitados), 2 núcleos | zero |

## 4. Leitura fria do método, para o Diego decidir com os olhos abertos

- O único número verificável do autor é a demo com **139 views**. A prova de
  renda é de outro nicho, outra escala (1 mi de seguidores) e outro formato
  (stories), sem print auditável.
- "Mesmo vídeo 5 vezes com frase diferente" é a definição de conteúdo
  repetitivo na atualização de originalidade do Instagram de 30/04/2026.
  Quem faz isso hoje perde Explorar, aba Reels e sugeridos.
- Baixar o arquivo de outra página e repostar é o que a mesma atualização
  chama de repost. O visual do cartão é bom e é público; o arquivo por baixo
  é o que troca.
- O que sobra do método e vale: página dark, cadência alta, cartão com
  identidade, frase por post, oferta em stories + bio, medir o que viraliza e
  copiar o FORMATO. Tudo isso entra no plano.
