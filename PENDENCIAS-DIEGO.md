# PENDÊNCIAS DO DIEGO — o que só você pode fazer

Tudo o que não depende de você já está feito e testado. Isto aqui é ~2 h, uma
vez. Depois disso você não participa mais.

**Faça na ordem.** Os passos 1 a 4 destravam o YouTube; 5 e 6 destravam o
Instagram; 7 destrava o TikTok; 8 destrava o dinheiro. Dá para parar no 4 e já
ter canal publicando sozinho.

---

## 0. Tornar o repositório PÚBLICO (2 min) — antes de qualquer cron

https://github.com/diegohenriquemoraes-eng/gta6-canais/settings → *Danger Zone*
→ **Change visibility** → Public.

Por quê: repo privado dá **2.000 minutos de Actions por mês**. Só o render
diário (1 longo de ~15 min + 3 Shorts + 5 cartões) passa disso na primeira
semana. Em repo público os minutos são ilimitados — é a mesma decisão que o
`Palavra-Viva-3x` já tomou.

Não há segredo no código: tokens moram nos Secrets, e `marca/oficial/`
(432 MB de galeria da Rockstar) é gitignorado.

---

## 1. Conta Google NOVA (10 min)

https://accounts.google.com/signup

- Nome sugerido da conta: **Rumo a Vice City**.
- Senha no gerenciador, **2FA ligado**.
- ⚠ **NÃO usar a conta dos 5 canais bíblicos nem a `diegohenriquemoraes@gmail.com`.**
  Um strike de copyright atinge todos os canais da mesma conta, e em 08/09/2026
  você chegou a um clique de excluir quatro canais de uma vez por causa disso.

---

## 2. Criar o canal no YouTube (5 min)

https://www.youtube.com/ (logado na conta nova) → foto → **Criar canal**

- Nome: **Rumo a Vice City** · handle: **@rumoavicecity**
  (conferido livre em 22/09/2026; se tiver sido tomado, tente
  `@rumoavicecitybr` e me avise o handle final).
- Avatar e banner já estão prontos em `marca/avatar.png` e `marca/banner.png` —
  suba os dois pelo YouTube Studio (o avatar **não tem API**; o banner tem, e o
  script `produzir/aplicar_marca.py` aplica sozinho depois).
- **Copie o channel_id** (Studio → Configurações → Canal → Configurações
  avançadas) e cole em `publicador/config.json`, campo `channel_id`.

## 2b. Verificação por telefone (5 min)

https://www.youtube.com/verify_phone_number

Libera **capa personalizada** (sem isso o longo fica com o frame automático do
YouTube, que num fundo escuro é um retângulo preto) e Shorts acima de 60 s.

---

## 3. Projeto Google Cloud PRÓPRIO (20 min)

https://console.cloud.google.com/ (logado na conta NOVA)

1. **Novo projeto**: `gta6-canais`.
2. **APIs e serviços → Biblioteca** → ativar **YouTube Data API v3** e
   **YouTube Analytics API**.
3. **Tela de consentimento OAuth** → Externo → preencher → **PUBLICAR o app**
   (deixar "Em teste" faz o refresh token morrer em 7 dias e o canal emudece
   sem avisar).
4. **Credenciais → Criar credencial → ID do cliente OAuth → App para
   computador** → baixar o JSON.
5. Salvar como `credenciais/gta/client_secret.json` (a pasta é gitignorada).

Projeto próprio é obrigatório: a cota de 10.000 unidades/dia é por projeto, e
este canal sozinho gasta ~7.500.

---

## 4. Gerar o token e colar nos secrets (10 min)

```bash
cd C:\Users\NOTE\Desktop\Projetos\gta6-canais
python produzir/autorizar.py --canal gta
```

Abre o navegador; **escolha a conta/canal certo**. O script confere o canal e
se recusa a gravar se não bater com o `channel_id` do config.

Depois (opcional, para a medição de horas):

```bash
python produzir/autorizar.py --canal gta --analytics
```

E suba os secrets:

```bash
gh secret set YT_CLIENT_SECRET_GTA < credenciais/gta/client_secret.json
gh secret set YT_TOKEN_GTA < credenciais/gta/token.json
```

**A partir daqui o YouTube publica sozinho.** Rode uma vez à mão para ver:
Actions → **Publicar** → Run workflow → `forcar_tipo: short`.

---

## 5. Instagram profissional + Página do Facebook (20 min)

1. Criar conta nova no app do Instagram: **@rumoavicecity**.
2. Configurações → Conta → **Mudar para conta profissional** → Criador.
3. Criar uma **Página do Facebook** nova (facebook.com/pages/create) e vincular
   à conta do Instagram.
4. ⚠ **Armadilha já paga**: bio e foto ficam travadas até haver **contato
   confirmado**. Use um alias do Gmail (`seuemail+gta6@gmail.com`) na Central
   de Contas; o código chega no WhatsApp.

## 6. Token de longa duração da Graph API (15 min)

https://developers.facebook.com/ — dá para **reaproveitar o app da Meta do
`psicologia-fria`**: basta adicionar a conta nova.

Você precisa de dois valores:

- `IG_USER_ID_GTA` — o id de `graph.instagram.com/me`, **não** o número que
  aparece no painel;
- `IG_TOKEN_GTA` — token longo com `instagram_business_content_publish`.

```bash
gh secret set IG_USER_ID_GTA
gh secret set IG_TOKEN_GTA
```

E crie o repositório de mídia **público** (o Instagram baixa o MP4 de lá; asset
de repo privado ele recusa sem explicar):

```bash
gh repo create diegohenriquemoraes-eng/gta6-media --public --description "Hospedagem dos MP4 do @rumoavicecity"
```

---

## 7. TikTok + Zernio (15 min)

1. Conta nova no TikTok, **business** (libera link na bio sem mínimo de
   seguidores): @rumoavicecity.
2. Conectar no **Zernio** (grátis para 2 contas; a API oficial do TikTok só
   publica público depois de auditoria e robô de navegador é proibido).
3. `gh secret set ZERNIO_KEY_GTA` e mude `tiktok.ativo` para `true` em
   `publicador/config.json`.

---

## 8. Shopee: gerar os links (15 min) — este é o passo do dinheiro

Em 22/09/2026 o Chrome **não estava logado** na Shopee: `affiliate.shopee.com.br`
redirecionou para a tela de login e a busca do site devolveu a página de
verificação anti-robô. Logar e passar por verificação anti-robô não é coisa que
eu faça por você, então este passo ficou inteiro aqui.

`conteudo/ofertas.json` já está montado com os 6 produtos, a prioridade, a
vigência de cada um e o porquê de cada escolha. Falta preencher 4 campos por
produto:

1. Entre em https://affiliate.shopee.com.br/ (conta de afiliado já ativa).
2. Para cada produto de `conteudo/ofertas.json`:
   - ache o item na Shopee, **anote `preco`, `vendidos` e `nota`** da página;
   - anote a **`comissao_pct`** que o portal mostra para aquele item;
   - cole a URL em **Ofertas → Link personalizado** e gere um link **por
     origem**, acrescentando `?src=` (ou `&src=` se já houver `?`):
     `yt_short`, `yt_largo`, `yt_bio`, `ig_bio`, `ig_story`, `tt_bio`.
3. Preencha `links` no JSON, assim:

```json
"links": {
  "yt_largo": "https://s.shopee.com.br/XXXXXXX?src=yt_largo",
  "yt_short": "https://s.shopee.com.br/XXXXXXX?src=yt_short",
  "ig_bio":   "https://s.shopee.com.br/XXXXXXX?src=ig_bio",
  "ig_story": "https://s.shopee.com.br/XXXXXXX?src=ig_story",
  "tt_bio":   "https://s.shopee.com.br/XXXXXXX?src=tt_bio"
}
```

4. Reordene `prioridade` por **vendidos × comissão × preço** (prioridade 1 = o
   link principal, que hoje é a pré-venda do jogo).
5. Monte a **vitrine de afiliado** com os 4-6 primeiros e guarde o link único —
   é ele que vai na bio das três redes.
6. Rode `python -m unittest testes.test_config` — ele reprova link sem `src=` e
   oferta sem `vigencia.ate`.

⚠ Sem `src=`, daqui a dois meses não dá para saber se a oferta gerou um clique
sequer, e trocar de produto vira achismo.

---

## 9. Bio e links nas três redes (5 min)

A bio já está em `publicador/config.json` (`bio`) e é aplicada no YouTube por
`python produzir/aplicar_marca.py`. O que **não tem API** e é seu:

- **avatar** do YouTube (só Studio/app);
- **nome e handle** do canal (só Studio — a API devolve 200 gravando nada);
- **trailer para não inscritos** (só Studio);
- **seção Links** do canal (só Studio);
- bio e link do **Instagram** e do **TikTok** (cole o link da vitrine).

---

## O que fazer quando o vigia abrir issue

| issue | o que significa | o que fazer |
|---|---|---|
| *Poço de fatos quase seco* | menos de 9 fatos livres | escrever fatos novos em `conteudo/fatos/` (gancho ≤ 10 palavras, narração 35-55, fonte, cena, tags) e dar push. A 3 Shorts/dia os 150 fatos cobrem até ~08/11 |
| *publicou menos que a config* | a esteira está entregando menos do que devia | olhar o workflow Publicar em Actions |
| *Fila sem pacote para amanhã* | o Reabastecer falhou | rodar à mão em Actions |
| *Licença mudou em `<videoId>`* | um gameplay CC BY deixou de ser CC | tirar as cenas `cc:<id>` de `conteudo/cenas.json` |
