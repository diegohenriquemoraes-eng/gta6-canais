# PENDÊNCIAS DO DIEGO — só login e criação de conta

Atualizado em 23/09/2026, de madrugada. **As duas redes já publicam sozinhas** —
o que sobrou aqui é TikTok e dois campos do Instagram que só o celular edita. Depois de cada passo, rode:

```bash
python produzir/conferir_instalacao.py
```

Ele diz em uma tela o que está de pé e o que falta, com o comando de cada
pendência.

---

## ✅ Já feito (não precisa tocar)

**Infra**
- Repositório `gta6-canais` **público** (privado dá 2.000 min/mês de Actions e
  o render diário passa disso na 1ª semana). Auditado antes: nenhum token,
  chave ou credencial no código nem no histórico.
- Repositório de mídia `gta6-media` **público** criado.
- 7 workflows ativos; a suíte de **84 testes** passa no runner do GitHub.

**Conteúdo**
- Material oficial baixado (trailers 1 e 2 + **306 imagens** da galeria),
  193 cenas marcadas, fila com 3 dias, marca gerada.

**Shopee — fechada**
- 6 produtos escolhidos com **dados reais medidos** (preço, vendas, comissão).
- **36 links de afiliado gerados** (6 produtos × 6 origens), cada um com
  Sub_id próprio. Já entram nas descrições, nos Shorts e no story.

**YouTube — NO AR, publicando sozinho** 🟢
- Canal **Rumo a Vice City** `@rumoavicecity` (`UCUJdsMoY_H4hLlvckVjCcEg`), na
  conta `gta6diegomoraes@gmail.com` (⚠ **authuser=4** neste Chrome).
- Projeto Cloud próprio, Data API v3 + Analytics ativas, token e secrets no ar,
  banner/bio/keywords aplicados por API.
- **App OAuth EM PRODUÇÃO** — o token não expira mais em 7 dias. Para liberar a
  publicação, escrevi as páginas de política e termos e as pus no ar por
  **GitHub Pages** (`diegohenriquemoraes-eng.github.io/gta6-canais/`), que virou
  o domínio autorizado. Sem servidor, sem DNS, sem custo.
- Primeiro vídeo no ar: https://youtu.be/evMAZGzD5fY

**TikTok @rumoavicecity — NO AR, espelhando sozinho** 🟢
- Conta própria no Zernio (`gta6diegomoraes@`), porque o teto grátis é de
  **2 contas por conta do Zernio** e as suas duas já eram do @vendanaobra.
  Perfil novo dentro da mesma conta não abre vaga.
- `publicador/tiktok.py` republica o cartão do Instagram (mesmo MP4 já
  hospedado), 3/dia, 30 min depois do Instagram.
- ⚠ A chave que você colou no chat (`sk_e5152bb…`) foi **trocada e apagada** em
  23/09: criei outra pela própria API do Zernio (`POST /api-keys`), troquei o
  secret, validei no runner e apaguei a antiga — ela devolve 401 agora.
- Primeiro vídeo: https://www.tiktok.com/@rumoavicecity/video/7688738476300258566

**Instagram @rumoavicecity — NO AR, publicando sozinho** 🟢
- Conta profissional de **Criador** (categoria *Gaming video creator*), com
  foto de perfil e bio aplicadas.
- App próprio da Meta (`3300084843713046`), secrets `IG_USER_ID_GTA` e
  `IG_TOKEN_GTA` no repo.
- Primeiro Reel no ar: https://www.instagram.com/reel/18209930776368705/

**Poço de fatos ampliado (23/09)**
- De 150 para **218 fatos**, todos com fonte verificável: o Extended Look
  inteiro (mecânicas, polícia, corpo, corridas, atividades), o elenco de apoio
  (Boobie Ike, Dre'Quan Priest, Real Dimez, Raul Bautista, Cal Hampton, Brian
  Heder), as seis regiões de Leonida e as edições/pré-venda.
- A 3 Shorts/dia o poço agora **passa do lançamento** (seca ~01/12, o jogo sai
  19/11). Antes secava em 08/11 e o canal ficaria mudo justamente no pico.

---

## O que falta — na ordem

### 1. Instagram: duas coisas que só o APP do celular faz

- **Nome de exibição**: ainda está "Diego Moraes" → mudar para
  **Rumo a Vice City**. O campo resiste à automação e o Instagram só permite
  **2 trocas em 14 dias**, então não insisti às cegas.
- **Link da bio**: a própria tela do Instagram web avisa que *"somente é
  possível editar o link no celular"*. Cole lá o link do **produto foco**:
  `https://s.shopee.com.br/9KiFc9wYfG`
  (chaveiro mini capa de PS5 GTA 6, Sub_id `igbio`).

### 2. Regerar o token do Instagram (~2 min)

O token de acesso foi colado em texto puro no chat de 22/09 e está no histórico
da conversa. Ele funciona, e nada indica vazamento — mas o certo é gerar outro
na Meta (o novo invalida o antigo) e rodar de novo:

```bash
python produzir/instalar.py instagram
```

### 3. Opcional

- **Analytics** (mede hora contável): `python produzir/instalar.py analytics`
- **Notícias com resumo de verdade**:
  `gh secret set ANTHROPIC_API_KEY -R diegohenriquemoraes-eng/gta6-canais`.
  Sem ela o resumo de emergência entra com nota 6 — abaixo do corte — e a
  notícia **não vira Short sozinha**, de propósito.
- **Verificação por telefone** do canal (`youtube.com/verify_phone_number?authuser=4`):
  libera capa personalizada. Sem ela o vídeo longo fica com um retângulo preto
  no lugar da miniatura. O Short não é afetado.

## O que mudou no plano (leia, muda a expectativa de dinheiro)

**O jogo GTA 6 de PS5 não está à venda na Shopee.** Medido em 22/09: a busca
por "grand theft auto vi ps5 lacrado" volta vazia e "gta 6 ps5 mídia física" só
devolve mod de PS2 e peça decorativa. A oferta principal do plano (pré-venda a
R$ 449, ~3 % = ~R$ 13 por venda) **não existe** nessa plataforma.

**O foco é UM produto** (decisão sua, 22/09): o **acessório mais vendido**.
Varri 157 produtos do tema em 12 buscas, ordenando pelo "Mais vendidos" da
própria Shopee:

| vendas | produto | preço | comissão | por venda |
|---|---|---|---|---|
| 449 | Camiseta GTA 6 | R$ 33,75 | 5 % | R$ 1,69 |
| **355** | **Chaveiro mini capa de PS5** | **R$ 13,99** | **16 %** | **R$ 2,24** |
| 298 | Totem display de mesa | R$ 33,68 | 5 % | R$ 1,68 |
| 267 | Skin adesiva PS5 Slim | R$ 49,97 | 5 % | R$ 2,50 |
| 265 | Quadro 3 peças | R$ 27,96 | 17 % | R$ 4,75 |
| 163 | Mouse pad grande | R$ 19,99 | 5 % | R$ 1,00 |

**O foco ficou no chaveiro.** A camiseta vende mais, mas é vestuário, não
acessório — e paga menos (R$ 1,69 contra R$ 2,24) com tíquete duas vezes e meia
maior. O chaveiro é o caso raro de **volume alto E comissão alta**: 355 vendas a
16 %, contra 84 vendas do segundo chaveiro do mesmo tipo. A R$ 13,99 é compra de
impulso, que é o que um canal sem autoridade nenhuma consegue converter.

A descrição de cada vídeo leva **uma oferta só** — com duas, nenhuma converte e
o Sub_id não diz qual produto falhou, só a rede.

O **quadro de 3 peças fica em prioridade 2** porque paga o dobro por venda
(R$ 4,75): é a troca natural na régua de 05/12 se o chaveiro não vender.

**R$ 1.000/mês = ~450 chaveiros, ou 15 por dia.** Muito longe dos ~80 jogos do
plano original. O tíquete baixo é o que torna isso plausível para um canal novo,
mas é honesto dizer que 15 vendas/dia por afiliado é meta agressiva.

⚠ **O rastreador da Shopee é o Sub_id, não `?src=`.** O campo só aceita
alfanumérico (`yt_largo` com underscore é recusado) e parâmetro colado na URL
encurtada o encurtador descarta. Os Sub_ids são `ytlargo`, `ytshort`, `ytbio`,
`igbio`, `igstory`, `ttbio`. O relatório sai em affiliate.shopee.com.br →
**Relatório de cliques / Relatório de vendas**, filtrando por Sub_id 1.

---

## Quando o vigia abrir issue

| issue | o que significa | o que fazer |
|---|---|---|
| *Poço de fatos quase seco* | menos de 9 fatos livres | escrever fatos novos em `conteudo/fatos/`. A 3 Shorts/dia os **218** cobrem até ~01/12 — o lançamento é 19/11, então já passa dele |
| *publicou menos que a config* | a esteira entregou menos do que devia | olhar o workflow Publicar em Actions |
| *Fila sem pacote para amanhã* | o Reabastecer falhou | rodar à mão em Actions |
| *Licença mudou em `<videoId>`* | um gameplay CC BY deixou de ser CC | tirar as cenas `cc:<id>` de `conteudo/cenas.json` |
