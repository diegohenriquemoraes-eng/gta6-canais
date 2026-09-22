# RETOMAR — gta6-canais

## O que é
Canais automáticos sobre GTA 6 (YouTube Shorts + longo, Instagram Reels +
Stories, TikTok) monetizando por afiliado Shopee na bio, custo zero, sem
assinar ferramenta. Lançamento do jogo: 19/11/2026. Plano em `PLANO.md`;
engenharia reversa do ViceScale (a ferramenta que replicamos) em
`VICESCALE.md`; prompts em `PROMPT.md`; **`ARQUITETURA.md` é a saída do
BLOCO 1 (Fable 5.1, 22/09/2026)**, com a árvore do repo, esquemas, agendador,
cartão, ranqueador, pipeline CC-BY, notícias, marca, testes e réguas.

## O que está no ar
Nada ainda. Estão gravados e validados (22/09/2026):
- `conteudo/fatos/*.json`: 150 fatos (F001-F150), todos com fonte, gancho ≤ 10
  palavras, narração 35-55 palavras, cena e tags. `F110` está com
  `revisar: true` (número de vendas da franquia com fonte secundária).
- `conteudo/frases.json`: 40 frases do cartão em 4 categorias.

## O que falta, em ordem
1. Diego roda o **BLOCO 2** de `PROMPT.md` no Opus 5 dentro desta pasta
   (o BLOCO 1 já foi executado; não repetir).
2. Diego cria as contas e tokens: lista com tempos em `ARQUITETURA.md` §J
   (~2 h, uma vez).
3. Fase 0 fecha em 30/09 com o 1º post no ar.

## Decisões que não se reabrem
- ViceScale não se assina: replicamos a mecânica (ranqueador, cartão, frases,
  escala, agendamento) no motor da casa. `VICESCALE.md` §3.
- Arquivo de vídeo só de fonte limpa (Rockstar oficial, CC-BY). Vídeo de
  outra página serve para medir formato, nunca para postar. `PLANO.md` §0 e §2.
- Cada clipe recebe 1 frase por 7 dias (repetição idêntica é o que o IG
  rebaixa desde 30/04/2026).
- Canal em conta Google NOVA, nunca na conta dos 5 canais bíblicos.
- Link de afiliado nunca sobre imagem da Rockstar.
- Nome recomendado: **Rumo a Vice City / @rumoavicecity** (livre no YouTube em
  22/09); voz `pt-BR-ThalitaMultilingualNeural` (ou Antonio ajustado).

## Armadilhas já pagas (herdadas)
As do `Palavra-Viva-3x/CLAUDE.md` e do `psicologia-fria/CLAUDE.md` valem
inteiras: `-framerate 30`, cron esparso, state versionado, tags por conjunto,
contato confirmado do IG por alias do Gmail, TikTok só via Zernio. E uma nova:
o site oficial `rockstargames.com/VI` e o Newswire não se leem por script
simples (JS); as descrições de lugares no poço estão em palavras próprias até o
Opus conferir na galeria baixada.

## Pendências do Diego
- Rodar o BLOCO 2 no Opus 5.
- Criar as contas (`ARQUITETURA.md` §J).
