"""Upload e publicação na YouTube Data API — multi-canal.

Cada canal (es/en/pt) tem projeto Google Cloud PRÓPRIO (para não dividir a
quota de 10.000/dia) e credenciais em credenciais/{idioma}/. Escopo
youtube.force-ssl. Custos de quota: upload 1600, thumbnail 50, update 50.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
RETRIABLE = {500, 502, 503, 504}


def credenciais(pasta: Path) -> Credentials:
    token = pasta / "token.json"
    if not token.exists():
        raise SystemExit(f"token.json ausente em {pasta}")
    # utf-8-sig: o caminho PowerShell -> gh secret pode enfiar BOM no JSON
    info = json.loads(token.read_text(encoding="utf-8-sig"))
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.write_text(creds.to_json(), encoding="utf-8")
    if not creds.valid:
        raise SystemExit(f"Token inválido em {pasta}; reautorizar localmente.")
    return creds


def servico(pasta_cred: Path):
    return build("youtube", "v3", credentials=credenciais(pasta_cred),
                 cache_discovery=False)


def canal_do_token(youtube) -> tuple[str, str]:
    itens = youtube.channels().list(part="id,snippet", mine=True
                                    ).execute().get("items", [])
    if len(itens) != 1:
        raise SystemExit("Token não identifica um único canal")
    return itens[0]["id"], itens[0]["snippet"]["title"]


LIMITE_DESCRICAO = 4900   # o limite do YouTube é 5000; margem de segurança


def limpar_texto(txt: str) -> str:
    """Tira o que o YouTube recusa em título/descrição.

    `< >` derrubam o upload com 'invalid video description' (custou um longo
    de 16 min já renderizado em 19/07). Caracteres de controle idem.
    """
    txt = txt.replace("<", "(").replace(">", ")")
    return "".join(c for c in txt if c == "\n" or ord(c) >= 32)


def upload(youtube, arquivo: Path, titulo: str, descricao: str,
           tags: list[str], idioma_bcp47: str, categoria: str = "22",
           privacidade: str = "private") -> str:
    titulo = limpar_texto(titulo)
    descricao = limpar_texto(descricao)
    if len(descricao) > LIMITE_DESCRICAO:
        descricao = descricao[:LIMITE_DESCRICAO].rsplit("\n", 1)[0]
    if len(titulo) > 100:
        raise SystemExit(f"Título com {len(titulo)} caracteres (máx. 100)")
    body = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "categoryId": categoria,
            "tags": tags,
            "defaultLanguage": idioma_bcp47,
            "defaultAudioLanguage": idioma_bcp47,
        },
        "status": {
            "privacyStatus": privacidade,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }
    media = MediaFileUpload(str(arquivo), chunksize=8 * 1024 * 1024,
                            resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body,
                                  media_body=media)
    resposta = None
    tentativa = 0
    while resposta is None:
        try:
            progresso, resposta = req.next_chunk()
            if progresso:
                print(f"  upload: {progresso.progress() * 100:.0f}%", flush=True)
        except HttpError as exc:
            if exc.resp.status not in RETRIABLE:
                raise
            tentativa += 1
            if tentativa > 8:
                raise
            espera = min(64, 2 ** tentativa) + random.random()
            print(f"  erro {exc.resp.status}; retry em {espera:.0f}s", flush=True)
            time.sleep(espera)
        except (OSError, httplib2.HttpLib2Error) as exc:
            tentativa += 1
            if tentativa > 8:
                raise
            espera = min(64, 2 ** tentativa) + random.random()
            print(f"  falha de rede; retry em {espera:.0f}s: {exc}", flush=True)
            time.sleep(espera)
    return resposta["id"]


def esperar_processamento(youtube, video_id: str, limite_s: int) -> dict:
    fim = time.time() + limite_s
    vazios = 0
    while True:
        itens = youtube.videos().list(part="status,processingDetails",
                                      id=video_id).execute().get("items", [])
        if not itens:
            # Vídeo grande recém-enviado às vezes não é consultável na hora —
            # a lista volta vazia por alguns segundos. Antes isto derrubava a
            # execução (IndexError) e o Short do dia não saía. Agora espera.
            vazios += 1
            if vazios > 20:
                raise SystemExit("Vídeo não aparece na API após o upload")
            if time.time() >= fim:
                raise SystemExit("Tempo esgotado aguardando o vídeo indexar")
            time.sleep(15)
            continue
        vazios = 0
        item = itens[0]
        st = item.get("processingDetails", {}).get("processingStatus", "unknown")
        if st == "succeeded":
            return item
        if st in {"failed", "terminated"}:
            raise SystemExit(f"Processamento falhou: {st}")
        if time.time() >= fim:
            # Não é erro fatal: vídeo grande pode levar mais que o limite. Ele
            # fica privado e vira público na próxima passagem. Devolve o item
            # para o fluxo seguir sem derrubar o Short.
            raise SystemExit("Tempo esgotado no processamento; vídeo ficou privado")
        time.sleep(15)


def tornar_publico(youtube, video_id: str, item: dict) -> None:
    status = dict(item["status"])
    status["privacyStatus"] = "public"
    status["selfDeclaredMadeForKids"] = False
    youtube.videos().update(part="status",
                            body={"id": video_id, "status": status}).execute()


def ja_publicado(youtube, titulo: str, dias: int = 1) -> str | None:
    """Devolve o id se o canal JÁ tem um vídeo com este título recente.

    O state.json não basta como verdade: em 19/07 uma execução ficou na fila
    (trava de concorrência), começou logo depois da anterior publicar e fez
    checkout do repositório com o estado ANTIGO — para ela o longo do dia não
    tinha saído, e publicou um segundo idêntico. O canal é a única fonte
    confiável, então conferimos nele antes de subir. Custo: 2 unidades.
    """
    from datetime import datetime, timedelta, timezone
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    canais = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads = canais["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    itens = youtube.playlistItems().list(
        part="snippet,contentDetails", playlistId=uploads, maxResults=15
    ).execute().get("items", [])
    alvo = limpar_texto(titulo).strip().casefold()
    for it in itens:
        publicado = it["contentDetails"].get("videoPublishedAt")
        if publicado and datetime.fromisoformat(
                publicado.replace("Z", "+00:00")) < corte:
            continue
        if it["snippet"]["title"].strip().casefold() == alvo:
            return it["contentDetails"]["videoId"]
    return None


def playlist_por_titulo(youtube, titulo: str, descricao: str) -> str:
    """Acha (ou cria) a playlist do canal com este título e devolve o id.

    Playlist é o que transforma 1 vídeo assistido em sessão: o YouTube passa a
    encadear o próximo vídeo do canal em vez de mandar o espectador embora.
    Custo de quota: list=1, insert=50 (só na primeira vez de cada formato).
    """
    pagina = None
    while True:
        r = youtube.playlists().list(part="id,snippet", mine=True,
                                     maxResults=50, pageToken=pagina).execute()
        for pl in r.get("items", []):
            if pl["snippet"]["title"] == titulo:
                return pl["id"]
        pagina = r.get("nextPageToken")
        if not pagina:
            break
    novo = youtube.playlists().insert(
        part="snippet,status",
        body={"snippet": {"title": titulo, "description": descricao},
              "status": {"privacyStatus": "public"}},
    ).execute()
    return novo["id"]


def adicionar_na_playlist(youtube, playlist_id: str, video_id: str) -> None:
    youtube.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id,
                          "resourceId": {"kind": "youtube#video",
                                         "videoId": video_id}}},
    ).execute()


def definir_thumbnail(youtube, video_id: str, thumb: Path) -> None:
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg"),
    ).execute()


def enviar_legenda(youtube, video_id: str, srt: Path, idioma_bcp47: str,
                   nome: str = "") -> str:
    """Sobe o .srt como faixa de legenda do vídeo. Custa 400 de cota.

    A legenda queimada no vídeo é imagem — a busca do YouTube não lê nada dela.
    Esta faixa é o texto que a plataforma indexa, e é dela que sai a tradução
    automática para outros idiomas. Como o texto e os tempos já existem para
    queimar, o único custo é a cota.
    """
    resp = youtube.captions().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id, "language": idioma_bcp47,
                          "name": nome, "isDraft": False}},
        media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream"),
    ).execute()
    return resp["id"]
