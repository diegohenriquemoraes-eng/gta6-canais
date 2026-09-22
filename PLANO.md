# GTA 6 — canais automáticos para monetizar (plano de 22/09/2026)

Objetivo do Diego: crescer canal no YouTube (Shorts + longo), perfil no Instagram e
no TikTok em cima do hype do GTA 6, **100 % automatizado, custo zero, sem
assinar ferramenta**, monetizando pelo link de afiliado da Shopee na bio (e, se
vier, pelo YPP). Este arquivo é o plano. `PROMPT.md` é o prompt para o Fable 5
arquitetar e o Opus 5 executar. `VICESCALE.md` é a engenharia reversa da
ferramenta, peça por peça, com a réplica de cada uma.

## 0. O que a pesquisa mudou no pedido

| Pedido | O que foi achado | Decisão |
|---|---|---|
| "Ferramenta ViceScale" | vicescale.com, R$ 97,90 vitalício, de Heron Reis (canal com 2 vídeos; a demo tem 139 views). A página de vendas fala só em "subir seu conteúdo", mas a **demonstração mostra a aba "Vice Scrap"**: cola o @ de um perfil, lista os posts por views/curtidas e baixa os 10 mais vistos para "reciclar". Depois: template de cartão (avatar + nome + selo + frase), 5 frases geradas por IA, 10 vídeos × 5 frases = 50 posts, agendados no Instagram em intervalo fixo. Sem depoimento, sem garantia, sem CNPJ nos termos; os termos jogam toda a responsabilidade autoral no usuário. | **Não assinar. Replicar a mecânica** (ranqueador de perfil, cartão, variações de frase, agendamento em lote) no motor da casa. Ver `VICESCALE.md`. |
| "Baixar os vídeos mais virais e republicar" | Os clipes de exemplo do próprio ViceScale são cenas do Trailer 2 (festa na piscina, ringue de luta, carro à noite). Ou seja: **as páginas "virais" que ele copia já são cortes do trailer da Rockstar**. A fonte original está de graça em rockstargames.com, sem depender de terceiro. E republicar arquivo alheio não entrega em 2026: YouTube não monetiza "reused/inauthentic content" (varredura de jan/2026), TikTok tira do For You desde 15/09/2025, Instagram parou de recomendar repost em Reels (2024) e em foto/carrossel (30/04/2026). Um strike de copyright na conta Google atinge os outros canais da conta (regra já paga no `Palavra-Viva-3x/CLAUDE.md`). | O ranqueador de perfil entra como **medição** (o que retém, que frase, que cena, que duração). O **arquivo** vem do trailer/galeria oficial e, pós-lançamento, de gameplay com licença Creative Commons. Mesmo visual, mesma cadência, fonte limpa. |
| "Produto que mais vende de GTA 6 na Shopee" | A Shopee não expõe ranking por busca; os candidatos estão no item 4 e o "N vendidos" tem de ser lido na página de cada produto (o Opus faz isso pelo Chrome). | Escolha inicial + medição a cada 2 semanas. |

## 1. O calendário é o ativo: 58 dias até o lançamento

| Data | Marco | O que rende |
|---|---|---|
| 25/06/2026 | pré-venda aberta (US$ 79,99 / Ultimate US$ 99,99) | Shopee: Standard PS5 a R$ 449, chegou a R$ 365 no 9.9 |
| 27/08/2026 | "An Extended Look" (26 min, Netflix + YouTube Rockstar; 31,1 mi views na Netflix em 4 dias) | 26 min de gameplay oficial para fatiar |
| 31/08/2026 | Rockstar soltou 29 screenshots (galeria oficial: 99 + artworks) | imagem licenciada para todo post |
| **12/11/2026** | pré-download digital | pico de busca "gta 6 tamanho / horário" |
| **19/11/2026** | lançamento PS5 / Xbox Series | pico absoluto; DualSense edição GTA 6 chega no mesmo dia |
| 20/11/2026 | fim do bônus Vintage Vice City Pack | urgência para a pré-venda |
| provável out/nov | trailer de lançamento (histórico da Rockstar) | novo lote de cenas e fatos |

Depois de 19/11 sai o "faltam N dias" e entra o gameplay. Sem o Diego jogar, o
gameplay vem de **uploads com licença Creative Commons** (YouTube Data API,
`videoLicense=creativeCommon`; a CC-BY autoriza reutilização com crédito).
Isso é "baixar e reutilizar" do jeito que as plataformas aceitam.

## 2. Base legal do material

- **Rockstar** ("Policy on posting copyrighted Rockstar Games material"): libera
  gameplay, machinima e clipes, inclusive com receita de anúncio de plataforma;
  derruba material **vazado / pré-lançamento** e trapaça em online; reserva o
  direito de derrubar qualquer coisa. Trailers, Extended Look e a galeria
  oficial (`rockstargames.com/VI/media`) são material de divulgação, o uso mais
  seguro que existe. **Nunca** o vazamento de 2022 nem "gameplay vazado".
- **Link de afiliado**: bio, descrição e card de fim; **não vai por cima da
  imagem da Rockstar** (isso é "usar o material como promoção de produto", que
  a política veta).
- **Camada autoral** em todo post: no YouTube, narração própria (fato, contexto,
  contagem); no Instagram/TikTok, o cartão com fato e frase própria. É o que
  separa "monetizável" de "reused" e "original" de "repost".
- **Gameplay CC-BY**: crédito ao canal de origem na descrição e no rodapé;
  `videoId` de origem guardado no pacote (prova).

## 3. Os formatos (todos gerados pelo motor, sem gente)

| # | Formato | Fonte | Frequência | Fase |
|---|---|---|---|---|
| A | **Contagem regressiva** "Faltam N dias para GTA 6" + 1 fato oficial, narrado | screenshot oficial + poço de fatos | 1 Short/dia, hora fixa | até 19/11 |
| B | **"Você viu isso no trailer?"**: cena do trailer/Extended Look, zoom, fato narrado | trailers oficiais (~30 min) | 1 Short/dia | até 19/11 |
| C | **Notícia**: Newswire da Rockstar / preço da pré-venda / DualSense | RSS + resumo por LLM barato | quando houver (teto 1/dia) | sempre |
| D | **Longo** "Tudo o que sabemos sobre GTA 6" (fatos A+B encadeados, 15-25 min) | poço de fatos | 1 a cada 2-3 dias | até 19/11 |
| E | **Gameplay comentado** (clipe CC-BY + narração de contexto) | YouTube CC-BY | 2 Shorts/dia | pós 19/11 |
| F | **Longo pós-lançamento**: "guia", "mapa", "segredos" com clipes CC-BY | YouTube CC-BY | 1/dia | pós 19/11 |
| **G** | **Cartão** (o formato do ViceScale): cena do trailer de 6-12 s dentro de um cartão com avatar + nome + selo + frase, fundo blur, sem narração | trailer/Extended Look/CC-BY | 4-6 Reels/dia no IG, espelho no TikTok | sempre |

O formato G é o que as páginas dark de GTA 6 postam (é o que o ViceScale
fabrica) e é barato: sem TTS, render de segundos. A regra que o ViceScale não
tem: **cada clipe recebe UMA frase por semana** (repetir o mesmo vídeo 5 vezes
com frase diferente é exatamente o "conteúdo repetitivo" que o Instagram
rebaixa desde 30/04/2026). Variação é entre clipes, não do mesmo clipe.

Anatomia do Short narrado = a do `Palavra-Viva-3x` (gancho no frame zero, sem
preto, teto 25 s, `-framerate 30`, legenda queimada, sem música de terceiro).
Voz TTS pt-BR **diferente** das já usadas na casa. Rodapé: "Material oficial ©
Rockstar Games" (crédito CC-BY nos formatos E/F).

**Poço de fatos** (`conteudo/fatos.json`): 150 a 250 fatos verificáveis, cada
um com fonte (URL oficial ou timestamp do trailer), gancho ≤ 10 palavras,
narração de 35-55 palavras, cena/imagem oficial associada, tags. Rumor entra
rotulado e só com fonte grande (IGN, GameSpot, Rockstar Intel).

## 4. Shopee: o que vender e como medir

Afiliado já ativo; comissão por categoria 3-15 % (campanhas sobem); conferir a
taxa de cada item no portal antes de escolher.

| Produto | Preço visto | Por que | Quando |
|---|---|---|---|
| **GTA VI PS5 Standard, pré-venda** (loja oficial da Shopee) | R$ 449 (R$ 365 no 9.9) | maior tíquete; a intenção de compra é o tema do canal | link principal até 20/11 |
| DualSense edição GTA 6 (2 modelos) | sem preço BR ainda | chega 19/11; produto-desejo | principal a partir de 19/11 |
| Camiseta GTA 6 (várias lojas) | ~R$ 40-70 | moda tem a maior comissão | secundário |
| Caneca GTA 6 | ~R$ 30-50 | | secundário |
| Pôster adesivo A3 GTA 6 | ~R$ 15-25 | impulso | secundário |
| Chaveiro 3D / action figure GTA VI | ~R$ 15-90 | | secundário |

Como o Opus escolhe: abrir cada página no Chrome, ler "N vendidos" e nota,
ordenar por `vendidos × comissão × preço`, gravar em `conteudo/ofertas.json`
com `src=` por origem (`yt_short`, `yt_longo`, `ig_bio`, `tt_bio`, `ig_story`).
A bio recebe **um** link (vitrine de afiliado da Shopee com 4-6 produtos).

**Conta honesta**: jogo a R$ 449 com ~3 % rende ~R$ 13/venda; camiseta de
R$ 50 a ~12 % rende ~R$ 6. R$ 1.000/mês são ~80 jogos ou ~170 camisetas pelo
link. O "R$ 3.200 numa semana" do vídeo do método veio de uma página de 1 mi de
seguidores de outro nicho, por stories, sem print verificável; a página de GTA
que ele copia tem 27 mil seguidores. O projeto se justifica por rodar sozinho e
pelo pico de 19/11, não por renda garantida.

## 5. Redes e publicação (o que já existe na casa)

| Rede | Como publica | Base de código | O que o Diego faz UMA vez |
|---|---|---|---|
| YouTube | Data API, cron horário, `state.json` versionado | `Palavra-Viva-3x/publicador/` | **conta Google NOVA** (isola os 5 canais bíblicos), projeto Cloud próprio, OAuth em produção, token |
| Instagram | Graph API, Release do GitHub como hospedagem do MP4, intervalo configurável | `psicologia-fria/src/publicar.py` | conta profissional + Page, token longo; contato confirmado por alias do Gmail |
| TikTok | **Zernio** (API oficial só publica público após auditoria; robô de navegador é proibido) | memória `tiktok-via-zernio` | conta + conectar no Zernio (grátis para 2 contas) |

Cota YouTube (1 canal, projeto próprio): 3 Shorts + 1 longo/dia ≈ 7.100 de
10.000, com margem para 1 reenvio. Nunca 6 uploads/dia. O Instagram aceita até
25 publicações/dia por API; o plano usa 4-6.

## 6. Fases e régua

| Fase | Período | Entrega | Régua |
|---|---|---|---|
| 0 Fundação | 22/09 → 30/09 | repo clonado do motor, poço ≥ 150 fatos, cartão G renderizando, marca, contas, testes verdes, 1º post no ar | render local OK nos formatos A, B, D, G |
| 1 Contagem | 01/10 → 18/11 (49 dias) | YT 2-3 Shorts/dia + longo a cada 2-3 dias; IG 4-6 cartões/dia; TikTok espelho | **15/10**: mediana 7 d ≥ 1.000 views/Short no YT e ≥ 2.000/Reel no IG, senão troca gancho/voz/template; **01/11**: ≥ 300 inscritos ou o YT vira só Shorts |
| 2 Lançamento | 19/11 → 31/12 | E+F com CC-BY, DualSense como link principal, stories diários com oferta | **05/12**: 1º clique/venda medido no `src=`; sem venda até 31/12 → 1 post/dia por rede e deixar rodar |
| 3 Manutenção | 2027 | 1 Short + 2 cartões/dia | YPP quando bater 1.000 inscritos + 10 mi views/90 d |

Medição: `medir.py` da casa (coorte 2-7 d, mediana, "continuaram vs. pularam"
só no Studio) + `src=` da Shopee + o ranqueador de perfil rodando **na nossa
própria página** toda semana (o mesmo "Vice Scrap", apontado para nós). Relatório
entra na rotina de segunda dos canais.

## 7. O que NÃO fazer (decidido)

- Não republicar arquivo de terceiro sem licença CC. Não usar vazamento.
- Não repetir o mesmo clipe com 5 frases na mesma semana.
- Não abrir o canal na conta Google que tem os 5 canais bíblicos.
- Não assinar ViceScale nem "viral finder" pago: a Data API e o GraphQL do
  Instagram dão o mesmo dado de graça.
- Não colocar link de afiliado por cima de imagem da Rockstar.
- Não mudar duas variáveis na mesma janela de medição (lição de 20/07/2026).
