# PROVENIÊNCIA — de onde vem cada arquivo e sob que licença

Gerado por `produzir/baixar_oficial.py`. `marca/oficial/` é
gitignorado: o repo é público e vídeo commitado incharia o Git para
sempre. O runner reobtém a cada rodada (com cache de Actions).

## 1. Vídeos oficiais da Rockstar Games

Material de **divulgação** publicado pela própria Rockstar no canal
oficial @rockstargames. A "Policy on posting copyrighted Rockstar
Games material" libera gameplay, machinima e clipes, inclusive com
receita de anúncio de plataforma, e derruba material vazado ou
pré-lançamento. Trailers e o Extended Look são o uso mais seguro que
existe. **Nunca** o vazamento de 2022.

| chave | vídeo | id | publicado | arquivo |
|---|---|---|---|---|
| `trailer1` | Grand Theft Auto VI Trailer 1 | `QdBZY2fkU-0` | 2023-12-04 | `trailer1.mp4` (20 MB) |
| `trailer2` | Grand Theft Auto VI Trailer 2 | `VQRLujxTm3c` | 2025-05-06 | `trailer2.mp4` (35 MB) |
| `extended` | Grand Theft Auto VI: An Extended Look | `tJbzMqJGH4k` | 2026-08-27 | **não baixado** |

Rodapé obrigatório em todo vídeo que usa este material:
`Material oficial © Rockstar Games` (queimado no pixel por
`nucleo/legendas.py`, estilo `Marca`, e repetido na descrição).

## 2. Galeria oficial (screenshots e artworks)

Origem: https://www.rockstargames.com/VI/media — **2 imagens** em disco.

## 3. Gameplay em Creative Commons (formatos E e F, pós-19/11/2026)

Colhido por `produzir/colher_cc.py` com `videoLicense=creativeCommon`
na YouTube Data API. A CC BY autoriza a reutilização **com crédito**:
o nome do canal de origem vai no rodapé do vídeo
(`Gameplay: <canal> · CC BY`) e o link do original vai na descrição.
Cada `videoId` usado ganha uma linha abaixo, com a licença lida da
API na data da colheita. Se a API deixar de reportar
`creativeCommon` para um id já usado, o vigia abre issue.

| videoId | canal | colhido em | licença lida |
|---|---|---|---|
| (nenhum ainda — o pipeline E/F só liga em 19/11/2026) | | | |

## 4. Fontes do repo

`marca/fontes/Montserrat-Bold.ttf` e `BebasNeue-Regular.ttf` —
SIL Open Font License, copiadas do repo `Palavra-Viva-3x`.

_Atualizado em 2026-09-22._
