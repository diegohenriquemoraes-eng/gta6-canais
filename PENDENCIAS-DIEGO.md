# PENDÊNCIAS DO DIEGO — só login e criação de conta

Atualizado em 22/09/2026, depois da rodada em que fiz tudo o que não exige as
suas credenciais. Depois de cada passo, rode:

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
- 7 workflows ativos; a suíte de **83 testes** passa no runner do GitHub.

**Conteúdo**
- Material oficial baixado (trailers 1 e 2 + **306 imagens** da galeria),
  193 cenas marcadas, fila com 3 dias, marca gerada.

**Shopee — fechada**
- 6 produtos escolhidos com **dados reais medidos** (preço, vendas, comissão).
- **36 links de afiliado gerados** (6 produtos × 6 origens), cada um com
  Sub_id próprio. Já entram nas descrições, nos Shorts e no story.

**Instagram @rumoavicecity — quase pronto**
- Conta profissional de **Criador** (categoria *Gaming video creator*).
- **Foto de perfil** aplicada (o avatar do projeto).
- **Bio** no ar: "Tudo sobre GTA 6, todo dia, até 19 de novembro. Fatos e cenas
  do que a Rockstar já mostrou. Quadro, capa e camiseta no link 👇"

---

## O que falta — na ordem

### 1. Instagram: o token (5 min) — é o mais perto de ficar pronto

A aba já está na tela certa:
`developers.facebook.com/apps/1717198369563451` → **Configuração da API com
login do Instagram** (o app "Palavra Viva Reels", reaproveitado; ele já serve
`vendanaobra` e `psicologiafria.br`).

1. No passo **2. Gerar tokens de acesso**, clique em **Adicionar conta**.
   Abre um popup do Instagram — **é aí que a automação não entra**: autorize
   com a conta `@rumoavicecity`.
2. Depois que ela aparecer na lista, clique em **Gerar token** e copie.
3. No terminal:

```bash
python produzir/instalar.py instagram
```

Ele pede o token **sem ecoar na tela**, descobre o `IG_USER_ID` sozinho em
`graph.instagram.com/me` (é o id que a API usa, não o número do painel — trocar
os dois é erro clássico) e sobe os dois secrets. **Daí o Instagram publica
sozinho.**

### 2. Instagram: duas coisas que só o APP do celular faz

- **Nome de exibição**: ainda está "Diego Moraes" → mudar para
  **Rumo a Vice City**. Tentei pelo web e o campo resiste à automação; como o
  Instagram só permite **2 trocas de nome em 14 dias**, não insisti às cegas.
- **Link da bio**: a própria tela do Instagram web avisa — *"Somente é possível
  editar o link no celular"*. Cole lá o link do **produto foco**:
  `https://s.shopee.com.br/9KiFc9wYfG`
  (chaveiro mini capa de PS5 GTA 6, Sub_id `igbio`).

### 3. YouTube: canal na conta nova (20 min)

Logado em `gta6diegomoraes@gmail.com`:

1. **Criar o canal** — youtube.com/create_channel. Nome **Rumo a Vice City**,
   handle **@rumoavicecity**. Suba `marca/avatar.png` e `marca/banner.png`.
2. **Verificação por telefone** — youtube.com/verify_phone_number (libera capa
   personalizada; sem ela o longo fica com um retângulo preto).
3. **Projeto Cloud próprio** — console.cloud.google.com/projectcreate, nome
   `gta6-canais`:
   - ativar **YouTube Data API v3** e **YouTube Analytics API**;
   - tela de consentimento OAuth → Externo → **PUBLICAR o app**
     (⚠ em "Em teste" o refresh token morre em 7 dias e o canal emudece);
   - Credenciais → ID do cliente OAuth → **App para computador** → baixar o JSON
     e **deixar na pasta Downloads**.
4. No terminal, **um comando só**:

```bash
python produzir/instalar.py youtube
```

Ele acha o JSON sozinho, abre a tela de consentimento (você escolhe o canal e
clica em Permitir — o único clique que não dá para automatizar), grava o token,
**lê o channel_id e põe no config**, sobe os dois secrets, aplica banner, bio,
keywords e idioma, e roda o conferidor.

Opcional, para medir hora contável:
```bash
python produzir/instalar.py analytics
```

### 4. TikTok + Zernio (15 min)

Você já deslogou do TikTok para criar a conta nova.

1. tiktok.com/signup — conta **business** (libera link na bio sem mínimo de
   seguidores), usuário **@rumoavicecity**, e-mail `gta6diegomoraes@gmail.com`.
2. No Zernio (já logado), conecte essa conta do TikTok.
3. Copie a chave de API e:

```bash
gh secret set ZERNIO_KEY_GTA -R diegohenriquemoraes-eng/gta6-canais
```

4. Em `publicador/config.json`, mude `tiktok.ativo` para `true`.

### 5. Opcional — notícias com resumo de verdade

```bash
gh secret set ANTHROPIC_API_KEY -R diegohenriquemoraes-eng/gta6-canais
```

Sem ela, o resumo de emergência entra com nota 6 — abaixo do corte de 7 — e a
notícia **não vira Short sozinha**. É de propósito: publicar resumo não
conferido sobre lançamento de jogo é o caminho curto para o canal virar fonte
de boato.

---

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
| *Poço de fatos quase seco* | menos de 9 fatos livres | escrever fatos novos em `conteudo/fatos/`. A 3 Shorts/dia os 150 cobrem até ~08/11 — e o lançamento é 19/11 |
| *publicou menos que a config* | a esteira entregou menos do que devia | olhar o workflow Publicar em Actions |
| *Fila sem pacote para amanhã* | o Reabastecer falhou | rodar à mão em Actions |
| *Licença mudou em `<videoId>`* | um gameplay CC BY deixou de ser CC | tirar as cenas `cc:<id>` de `conteudo/cenas.json` |
