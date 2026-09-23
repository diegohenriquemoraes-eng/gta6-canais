# LEITURA do benchmark — o que os números mandam fazer

Os números crus ficam em `RESUMO.md`, que `produzir/ranquear_perfil.py --resumo`
**regrava por inteiro** a cada rodada. Esta análise mora aqui de propósito: em
23/09/2026 ela foi escrita no RESUMO e a rodada seguinte a apagou.

---

## YouTube — 250 vídeos do nicho (23/09/2026)

| consulta | mediana de views |
|---|---|
| gta 6 curiosidades | **933.336** |
| gta 6 detalhes trailer | 543.358 |
| gta 6 contagem regressiva | **18.258** |
| gta 6 fatos | **16.878** |

**O termo é "curiosidades", não "fatos" nem "contagem regressiva".** Cinquenta
vezes de diferença entre a palavra que a massa digita e o jargão que estávamos
usando — e "Faltam N dias para GTA 6" era a cauda de TODO título do formato A.

Aplicado no mesmo dia (`nucleo/fabrica._titulo_short` e `canal.CONFIG["tags"]`),
com o canal na primeira semana: mudar depois cairia no meio da janela de
medição de 15/10, e a regra da casa é não mexer em duas variáveis dentro de
uma janela.

**Dentro da contagem, o mais curto vence**: 0-10 s rende 32.651 (mediana),
10-20 s rende 14.612, 20-30 s rende 7.174. O nosso teto é 25 s. Isto **não**
foi mexido — a duração é a variável da PRÓXIMA janela, depois de 15/10, para a
medição não ficar ilegível.

**O topo do nicho é material oficial**: o vídeo mais visto em três das quatro
buscas é o próprio "An Extended Look" da Rockstar (28,8 mi). Não é competição,
é o teto do interesse — e ele passa por nós também, porque usamos o mesmo
material de divulgação.

**Há gameplay em Creative Commons circulando** (14 dos 50 em uma das buscas).
É o insumo do formato E, que liga em 19/11.

---

## Instagram — 3 páginas do nicho (23/09/2026)

Colhido no Chrome logado, da aba **Reels** de cada perfil: as views aparecem na
própria grade, o que é mais estável que o replay de GraphQL (a API interna
devolveu **429** em três chamadas seguidas). ⚠ **A duração não vem na grade**,
então as faixas de duração das linhas `ig` no RESUMO saem todas como "0-10 s" —
ignore esse corte, o número que vale é a mediana.

| perfil | seguidores | mediana de views | o que a página é |
|---|---|---|---|
| `gta6.only` | 201 mil | **51.100** | inglês, notícia e vazamento, verificado |
| `gta6clube` | 28,1 mil | 4.706 | BR, "memes e vazamentos", 1.295 posts |
| `gta6_brasil_` | 27,4 mil | 3.728 | BR, notícia |

**A régua de 15/10 está bem calibrada.** Ela pede ≥ 2.000 views/Reel, e as duas
páginas brasileiras ESTABELECIDAS, com ~28 mil seguidores, fazem 3.700 a 4.700.
Pedir metade do que elas fazem, com o canal recém-nascido, é exigente sem ser
fantasia.

**O teto do nicho escala com tamanho, não com formato**: `gta6.only` faz 10×
mais views que as páginas BR tendo 7× mais seguidores. Não existe atalho de
template que valha 10× — existe trabalho de audiência.

⚠ **E o desconfortável: as duas páginas BR vivem de MEME e VAZAMENTO.** A
`gta6clube` se descreve assim no próprio nome, e os Reels de maior alcance dela
são piada sobre imagem ("E se GTA 6 fosse DUBLADO em português do BRASIL?",
"POV: os NPCs de GTA 6..."). Nós apostamos no contrário — fato com fonte, sem
vazamento, que é diretriz e não preferência.

Ou seja: o número delas é referência de **alcance do nicho**, não prova de que
o nosso formato chega lá. Se em 15/10 a mediana estiver muito abaixo, a
pergunta certa não será "mudamos o gancho?", e sim **"fato com fonte tem
público neste nicho?"** — e essa resposta muda o projeto, não o template.
