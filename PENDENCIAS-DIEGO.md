# PENDÊNCIAS DO DIEGO — só login e criação de conta

Tudo o que não exige as suas credenciais **já está feito**. O que sobrou é
exatamente o que você pediu para ficar com você: criar conta e fazer login.

**As abas já estão abertas no Chrome, na ordem.** Vá da esquerda para a direita.
Depois de cada passo, rode:

```bash
python produzir/conferir_instalacao.py
```

Ele diz, em uma tela, o que já está de pé e o que falta — com o comando exato
de cada pendência.

## Já feito por mim (não precisa tocar)

- ✅ Repositório `gta6-canais` **público** (privado dá 2.000 min/mês de Actions
  e o render diário passa disso na 1ª semana). Auditado antes: nenhum token,
  chave ou credencial no código nem no histórico.
- ✅ Repositório de mídia `gta6-media` **público** criado (o Instagram baixa o
  MP4 de um Release de lá; asset de repo privado ele recusa sem explicar).
- ✅ Os 7 workflows ativos no GitHub, e a suíte de **81 testes já passou no
  runner** (47 s).
- ✅ Material oficial baixado, 193 cenas marcadas, fila com 3 dias, marca
  gerada, `ofertas.json` montado.

---

## Aba 1 — Conta Google nova · `accounts.google.com/signup`

Crie a conta. Sugestão de nome: **Rumo a Vice City**.

- 2FA ligado, senha no gerenciador.
- ⚠ **Não use a conta dos 5 canais bíblicos nem a `diegohenriquemoraes@gmail.com`.**
  Strike de copyright atinge todos os canais da mesma conta — em 08/09/2026
  você chegou a um clique de excluir quatro canais de uma vez por causa disso.
- **Anote o e-mail**: ele vai ser usado nas abas 5 e 8 (alias `+gta6`).

## Aba 2 — Criar o canal · `youtube.com/create_channel`

Logado na conta nova:

- Nome: **Rumo a Vice City** · handle: **@rumoavicecity**
  (livre em 22/09/2026; se tiver sido tomado, use `@rumoavicecitybr` e me avise).
- Avatar e banner prontos em `marca/avatar.png` e `marca/banner.png` — suba os
  dois pelo Studio (o avatar **não tem API**; o banner tem, e o script aplica
  depois).
- **Copie o channel_id**: Studio → Configurações → Canal → Configurações
  avançadas. Cole em `publicador/config.json`, campo `channel_id`.

## Aba 3 — Verificação por telefone · `youtube.com/verify_phone_number`

Libera **capa personalizada** (sem isso o longo fica com o frame automático do
YouTube, que num fundo escuro é um retângulo preto) e Shorts acima de 60 s.

## Aba 4 — Projeto Cloud próprio · `console.cloud.google.com/projectcreate`

1. Nome do projeto: `gta6-canais`.
2. **APIs e serviços → Biblioteca** → ativar **YouTube Data API v3** e
   **YouTube Analytics API**.
3. **Tela de consentimento OAuth** → Externo → preencher → **PUBLICAR o app**.
   ⚠ Deixar "Em teste" faz o refresh token morrer em 7 dias e o canal emudece
   sem avisar.
4. **Credenciais → Criar credencial → ID do cliente OAuth → App para
   computador** → baixar o JSON.
5. Salve como `credenciais/gta/client_secret.json` (pasta gitignorada).

Projeto próprio é obrigatório: a cota de 10.000 unidades/dia é por projeto e
este canal sozinho gasta ~7.600.

### Depois da aba 4, no terminal (é só colar)

```bash
python produzir/autorizar.py --canal gta
```

Abre o navegador; **escolha o canal certo**. O script confere e se recusa a
gravar se não bater com o `channel_id`. Depois:

```bash
gh secret set YT_CLIENT_SECRET_GTA < credenciais/gta/client_secret.json
gh secret set YT_TOKEN_GTA < credenciais/gta/token.json
python produzir/aplicar_marca.py
```

**A partir daqui o YouTube publica sozinho.** Para ver na hora:
Actions → **Publicar** → Run workflow → `forcar_tipo: short`.

Opcional, para medir hora contável:
```bash
python produzir/autorizar.py --canal gta --analytics
gh secret set YT_TOKEN_ANALYTICS_GTA < credenciais/gta/token_analytics.json
```

## Aba 5 — Instagram novo · `instagram.com/accounts/emailsignup`

- Usuário: **@rumoavicecity**. E-mail: o alias `seuemailnovo+gta6@gmail.com`.
- Depois de criar: Configurações → Conta → **Mudar para conta profissional** →
  Criador.
- ⚠ **Armadilha já paga**: bio e foto ficam travadas até haver **contato
  confirmado**. Confirme o e-mail na Central de Contas; o código chega no
  WhatsApp.

## Aba 6 — Página do Facebook nova · `facebook.com/pages/creation`

Crie uma Página nova (**não** reaproveite nenhuma existente) e vincule-a à
conta do Instagram da aba 5. A Graph API só publica em conta profissional
vinculada a uma Página.

## Aba 7 — Token da Graph API · `developers.facebook.com/apps`

Dá para **reaproveitar o app da Meta do `psicologia-fria`** — basta adicionar a
conta nova. Você precisa de dois valores:

- `IG_USER_ID_GTA` — o id de `graph.instagram.com/me`, **não** o número que
  aparece no painel;
- `IG_TOKEN_GTA` — token longo com `instagram_business_content_publish`.

```bash
gh secret set IG_USER_ID_GTA
gh secret set IG_TOKEN_GTA
```

## Aba 8 — TikTok novo · `tiktok.com/signup`

Conta **business** (libera link na bio sem mínimo de seguidores):
**@rumoavicecity**. Use o mesmo alias de e-mail.

## Aba 9 — Zernio · `zernio.com`

Conta nova, conecte o TikTok da aba 8 (grátis para 2 contas; a API oficial do
TikTok só publica público depois de auditoria e robô de navegador é proibido).

```bash
gh secret set ZERNIO_KEY_GTA
```

E mude `tiktok.ativo` para `true` em `publicador/config.json`.

## Aba 10 — Shopee Afiliados · `affiliate.shopee.com.br`

⚠ **Aqui a regra "conta nova em todo lugar" não se aplica**, e é melhor assim:
o programa de afiliados é vinculado ao CPF — não dá para ter duas contas. E não
há interferência nenhuma com o que já roda: **cada link leva o seu próprio
`src=`**, então a medição de origem fica separada mesmo com a comissão caindo
na mesma conta. Se você ainda assim quiser conta separada, aí é CNPJ, e vale
decidir depois de ver a primeira venda.

`conteudo/ofertas.json` já está montado com os 6 produtos, prioridade, vigência
e o porquê de cada escolha. Falta preencher, por produto:

1. na página do produto: **`preco`, `vendidos`, `nota`**;
2. no portal: a **`comissao_pct`** daquele item;
3. em **Ofertas → Link personalizado**, um link **por origem**, com `?src=`
   (ou `&src=` se a URL já tiver `?`): `yt_short`, `yt_largo`, `yt_bio`,
   `ig_bio`, `ig_story`, `tt_bio`.

```json
"links": {
  "yt_largo": "https://s.shopee.com.br/XXXXXXX?src=yt_largo",
  "yt_short": "https://s.shopee.com.br/XXXXXXX?src=yt_short",
  "ig_bio":   "https://s.shopee.com.br/XXXXXXX?src=ig_bio",
  "ig_story": "https://s.shopee.com.br/XXXXXXX?src=ig_story",
  "tt_bio":   "https://s.shopee.com.br/XXXXXXX?src=tt_bio"
}
```

4. Reordene `prioridade` por **vendidos × comissão × preço** (1 = link
   principal; hoje é a pré-venda do jogo).
5. Monte a **vitrine** com os 4-6 primeiros e guarde o link único — é ele que
   vai na bio das três redes.
6. Rode `python -m unittest testes.test_config` (reprova link sem `src=` e
   oferta sem `vigencia.ate`).

## Por último — bio e links

A bio está em `publicador/config.json` e o `aplicar_marca.py` aplica no YouTube.
O que **não tem API** e é seu, pelo Studio/app:

- avatar do canal · nome e handle · trailer para não inscritos · seção Links;
- bio e link da vitrine no **Instagram** e no **TikTok**.

---

## Quando o vigia abrir issue

| issue | o que significa | o que fazer |
|---|---|---|
| *Poço de fatos quase seco* | menos de 9 fatos livres | escrever fatos novos em `conteudo/fatos/` (gancho ≤ 10 palavras, narração 35-55, fonte, cena, tags). A 3 Shorts/dia os 150 cobrem até ~08/11 |
| *publicou menos que a config* | a esteira entregou menos do que devia | olhar o workflow Publicar em Actions |
| *Fila sem pacote para amanhã* | o Reabastecer falhou | rodar à mão em Actions |
| *Licença mudou em `<videoId>`* | um gameplay CC BY deixou de ser CC | tirar as cenas `cc:<id>` de `conteudo/cenas.json` |
