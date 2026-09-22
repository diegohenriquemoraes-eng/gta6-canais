# Prompt — GTA 6 canais automáticos

Uso: colar o BLOCO 1 numa conversa com o **Fable 5** (arquitetura + poço de
fatos + decisões). Salvar a saída em `ARQUITETURA.md` neste repo. Depois abrir
conversa nova com o **Opus 5** dentro de `Desktop\Projetos\gta6-canais` e colar
o BLOCO 2 (execução). Cada bloco é autossuficiente.

---

## BLOCO 1 — Fable 5 (arquitetar)

```
Você vai desenhar um sistema 100 % automático e de custo zero de canais sobre
GTA 6 (YouTube Shorts + longos, Instagram Reels + Stories, TikTok) que
monetiza por link de afiliado da Shopee na bio. O dono (Diego) não participa
depois da fundação e não assina ferramenta nenhuma. Leia primeiro, nesta ordem:

- C:\Users\NOTE\Desktop\Projetos\gta6-canais\PLANO.md — o plano aprovado; as
  decisões da seção 7 não se reabrem.
- C:\Users\NOTE\Desktop\Projetos\gta6-canais\VICESCALE.md — a ferramenta que
  vamos REPLICAR peça por peça (ranqueador de perfil, cartão com 3 layouts e
  blur, frases com variações, escala clipe × frase, agendamento em lote), com
  a fonte do material trocada pelo que a Rockstar libera e por gameplay CC-BY.
- C:\Users\NOTE\Desktop\Projetos\Palavra-Viva-3x\CLAUDE.md — o motor que será
  clonado (fila leve, render na hora de publicar, cota, anatomia do Short,
  suíte de testes, armadilhas pagas). Reaproveite; não reinvente.
- C:\Users\NOTE\Desktop\Projetos\psicologia-fria\CLAUDE.md — publicação no
  Instagram pela Graph API (src/publicar.py) e armadilhas do Reel.
- ~/.claude/projects/.../memory/tiktok-via-zernio.md e
  varrer-instagram-pelo-chrome.md — TikTok só via Zernio; Instagram lido por
  GraphQL replay no Chrome.

Restrições inegociáveis:
1. Arquivo de vídeo só de fonte limpa: trailers oficiais, "An Extended Look"
   (27/08/2026), galeria rockstargames.com/VI/media e, pós-19/11, clipes do
   YouTube com licença Creative Commons (Data API, videoLicense=creativeCommon)
   com crédito. Vídeo de outra página serve para MEDIR formato, nunca para
   postar. Nada de vazamento.
2. Camada própria em todo post: narração de fato no YouTube; cartão com
   frase/fato no IG e TikTok. Cada clipe recebe uma frase por 7 dias.
3. Link de afiliado só em bio, descrição, stories e card de fim; nunca sobre
   a imagem.
4. Canal em conta Google NOVA, projeto Cloud próprio, OAuth em produção.
5. Custo zero: GitHub Actions em repo público, edge-tts, ffmpeg, Openverse e
   galeria oficial. LLM só para variações de frase e resumo de notícia, no
   modelo mais barato, com teto diário.
6. Cota YouTube: 3 Shorts + 1 longo/dia (~7.100 de 10.000). Instagram 4-6
   cartões/dia + 1 story. Nunca 6 uploads/dia no YouTube.

Entregue, nesta ordem, em Markdown para salvar como ARQUITETURA.md:

A. Árvore do repo gta6-canais (o que copia do Palavra-Viva-3x, o que copia do
   psicologia-fria, o que é novo), um parágrafo por módulo novo. Os módulos
   novos obrigatórios: produzir/ranquear_perfil.py, nucleo/cartao.py,
   produzir/escalar.py, produzir/cenas.py (marcação de cenas dos trailers).
B. Esquemas: conteudo/fatos.json (id, gancho ≤ 10 palavras, narracao 35-55
   palavras, fonte, cena/imagem, tags, formato A/B/C, usado_em);
   conteudo/cenas.json (video_origem, inicio, fim, descricao, tags, licenca);
   conteudo/frases.json (categoria, texto, variacoes, usada_em);
   conteudo/ofertas.json (produto, link com src= por origem, comissao,
   prioridade, vigencia); conteudo/benchmark.json (o que o ranqueador grava).
C. O agendador: contagem regressiva pela data (19/11/2026), hora fixa por
   rede, gap como alvo (não veto), 2º cron aos :30, alarme "publicou menos
   que a config", troca automática A/B → E/F depois do lançamento, regra de
   1 frase por clipe por 7 dias e nunca 2 posts seguidos da mesma cena.
D. O cartão (nucleo/cartao.py): os 3 layouts em 1080×1920 com ffmpeg (fundo
   = clipe com boxblur escurecido, cabeçalho avatar + nome + selo, frase em
   fonte do repo, zona de vídeo com inicio/fim/zoom/dx/dy), o filtergraph de
   cada um e o custo de render estimado no runner de 2 núcleos.
E. O ranqueador (produzir/ranquear_perfil.py): entrada @ ou URL (IG, YT,
   TikTok), saída ordenada por views com duração, frase do 1º frame (OCR) e
   cena reconhecida; download só quando a licença é CC; rotina semanal na
   nossa própria página.
F. Pipeline E/F pós-lançamento: busca CC-BY por termo e viewCount, filtro de
   duração/qualidade, yt-dlp, corte, crédito no rodapé e na descrição,
   registro do videoId de origem.
G. Coleta de notícias (formato C): Newswire RSS + 2 fontes grandes, resumo
   com teto diário, regra fato vs. rumor e rótulo.
H. Marca: nome do canal/página e handle (3 opções sem homônimo, conferir por
   search.list e curl), voz TTS pt-BR ainda não usada na casa, paleta noturna
   Vice City (rosa/ciano sobre escuro), avatar e selo do cartão, rodapé de
   crédito, bio com o link único.
I. Os 150 primeiros fatos do poço (esquema de B) escritos a partir dos
   trailers 1 e 2, do Extended Look e do Newswire, com fonte em cada um; e
   as 40 frases-base do cartão por categoria. Sem rumor sem fonte. Sem
   spoiler além do que a Rockstar mostrou.
J. Lista das tarefas que SÓ o Diego pode fazer (contas, tokens, Zernio,
   vitrine da Shopee) em ordem, com o tempo estimado de cada uma.
K. Suíte de testes mínima (sem rede): agenda, cota, coerência da config (link
   sem src=, fato sem fonte, cena sem licença, clipe repetido na semana).
L. Réguas com data e número, copiadas da seção 6 do PLANO.md, e o que se
   desliga se cada uma falhar.

Responda em português. Não pergunte; decida e registre a premissa.
```

---

## BLOCO 2 — Opus 5 (executar)

```
Contexto: pasta C:\Users\NOTE\Desktop\Projetos\gta6-canais. Leia PLANO.md,
VICESCALE.md e ARQUITETURA.md (saída do Fable) e execute tudo que não depende
do Diego, sem pedir confirmação. Permissão total para ferramentas. Regras da
casa em ~/.claude/CLAUDE.md valem (português, git desde o 1º commit, estado em
arquivo, cérebro atualizado ao final).

Ordem de execução:

1. Copiar do Desktop\Projetos\Palavra-Viva-3x os módulos que ARQUITETURA.md
   manda (nucleo/, publicador/, testes/, workflows) e de
   Desktop\Projetos\psicologia-fria o src/publicar.py (Graph API). Adaptar
   config para 1 canal, pt-BR, cota 3 Shorts + 1 longo, IG 4-6 cartões + 1
   story. Commit.
2. Material oficial: baixar trailers 1, 2 e An Extended Look do canal
   Rockstar Games (yt-dlp, melhor qualidade) e a galeria oficial
   rockstargames.com/VI/media (screenshots + artworks). Guardar em
   marca/oficial/ (gitignorado, com script de reobtenção) e registrar cada
   arquivo em fontes/PROVENIENCIA.md.
3. Marcar cenas: gerar conteudo/cenas.json com detecção de corte do ffmpeg
   (scdet) nos 3 vídeos, 6-12 s por cena, descrição curta por cena (usar a
   transcrição/legenda oficial quando houver), licenca="rockstar_oficial".
4. Gravar conteudo/fatos.json e conteudo/frases.json com o que o Fable
   escreveu; validar com o teste de poço.
5. Cartão: implementar nucleo/cartao.py com os 3 layouts; renderizar 3
   exemplos (um por layout) com cena real do trailer e abrir para conferir:
   frase legível, blur, avatar, sem preto, duração de vídeo = duração de
   áudio original do clipe.
6. Ranqueador: implementar produzir/ranquear_perfil.py; rodar contra 3
   páginas de GTA 6 no Instagram (a partir de "gta6club") e contra a busca
   "gta 6" no YouTube (30 dias, viewCount). Gravar conteudo/benchmark.json e
   um resumo de 10 linhas do que rende (duração, tipo de frase, cena). Nada
   é baixado para reuso; só metadados e o 1º frame para OCR.
7. Shopee (Chrome, afiliado já logado): abrir cada candidato da seção 4 do
   PLANO.md, ler "vendidos", nota e comissão, ordenar por vendidos ×
   comissão × preço, gerar links com src= por origem e gravar
   conteudo/ofertas.json. Montar a vitrine de afiliado com os 4-6 primeiros
   e guardar o link único da bio.
8. Escala: implementar produzir/escalar.py (cena × frase → fila com as
   regras de repetição) e o agendador (formatos A, B, C, D, G agora; E, F
   depois de 19/11, automático).
9. Render local de A, B, D, G (e E com um vídeo CC-BY de teste):
   python publicador/publicar.py --render-apenas. Conferir duração áudio =
   vídeo, legenda no frame zero, rodapé de crédito, sem preto.
10. Marca: avatar, banner, capa e selo do cartão em marca/; script que aplica
    por API quando o token existir; bio pronta com o link da vitrine.
11. Workflows: publicar (cron horário + :30), reabastecer (6 h), medir
    (diário, inclui ranqueador na própria página aos domingos), testes (todo
    push), vigia (silêncio + "publicou menos"). Secrets em CREDENCIAIS.md
    (nomes, nunca valores).
12. Suíte de testes verde: python -m unittest discover -s testes.
13. RETOMAR.md (o que é, o que está no ar, o que falta em ordem, decisões que
    não se reabrem, armadilhas, pendências do Diego) e PENDENCIAS-DIEGO.md com
    passo a passo de cada conta/token/Zernio/vitrine.
14. Commit + push. Atualizar o cérebro (Desktop\Cérebro) e o CANAIS.md.

Quando algo depender do Diego (conta Google nova, token, Zernio, Facebook
Page), deixe o código pronto para rodar assim que o secret existir e siga
para o próximo item. Reporte ao final, em português: o que está no ar, o que
está pronto esperando secret, o que ficou de fora e por quê.
```
