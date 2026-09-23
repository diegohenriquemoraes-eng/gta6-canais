# -*- coding: utf-8 -*-
"""UM comando para tudo o que vem depois de criar a conta e o canal.

O Diego cria a conta, o canal e o projeto Cloud, baixa o JSON da credencial
OAuth e roda isto. O script faz o resto sozinho:

    python produzir/instalar.py youtube

1. **acha o JSON sozinho** na pasta Downloads (o Google o nomeia
   `client_secret_….apps.googleusercontent.com.json`) e o põe em
   `credenciais/gta/client_secret.json`;
2. abre a tela de consentimento — **o único clique que nenhum robô pode dar**;
3. confere de qual canal é o token e grava `credenciais/gta/token.json`;
4. **lê o channel_id do próprio token** e grava em `publicador/config.json`
   (o passo que mais se esquece, e que faz o publicador aceitar qualquer canal);
5. sobe `YT_CLIENT_SECRET_GTA` e `YT_TOKEN_GTA` como secrets do repo;
6. aplica banner, bio, keywords e idioma no canal por API;
7. roda o conferidor e diz o que ainda falta.

E para o Instagram:

    python produzir/instalar.py instagram

**Lê o token da área de transferência** (basta clicar em copiar no portal da
Meta) ou, se não achar, pede **sem ecoar na tela**, descobre o `IG_USER_ID` sozinho em
`graph.instagram.com/me` (é o id que a API usa, não o número do painel — a
troca dos dois é erro clássico) e sobe os dois secrets. O valor nunca aparece
em linha de comando nem em log.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

CRED = RAIZ / "credenciais" / "gta"
CONFIG = RAIZ / "publicador" / "config.json"
REPO = "diegohenriquemoraes-eng/gta6-canais"
GRAPH = "https://graph.instagram.com"


def passo(n: int, texto: str) -> None:
    print(f"\n[{n}] {texto}", flush=True)


def _rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=RAIZ, **kw)


# ------------------------------------------------------------------ YouTube --

def achar_client_secret() -> Path | None:
    """Procura o JSON que o Google acabou de baixar.

    Ordem: o lugar certo (se já estiver lá), depois Downloads, do mais novo
    para o mais velho. Só aceita arquivo que PAREÇA uma credencial OAuth de
    app de computador — JSON com a chave `installed`.
    """
    certo = CRED / "client_secret.json"
    if certo.exists():
        return certo
    candidatos: list[Path] = []
    for pasta in (Path.home() / "Downloads", Path.home() / "Transferências",
                  Path(os.environ.get("USERPROFILE", "")) / "Downloads"):
        if pasta.is_dir():
            candidatos += list(pasta.glob("client_secret*.json"))
            candidatos += list(pasta.glob("*apps.googleusercontent.com.json"))
    for p in sorted(set(candidatos), key=lambda x: -x.stat().st_mtime):
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if "installed" in d:
            return p
        if "web" in d:
            print(f"  ! {p.name} é credencial do tipo 'Aplicativo da Web'. "
                  f"Precisa ser 'App para computador' — crie outra no Cloud.")
    return None


def gravar_channel_id(cid: str) -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    atual = cfg["canais"]["gta"].get("channel_id", "")
    if atual == cid:
        print(f"  channel_id já estava correto ({cid})")
        return
    cfg["canais"]["gta"]["channel_id"] = cid
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"  channel_id gravado em publicador/config.json: {cid}")


def subir_secret(nome: str, arquivo: Path) -> bool:
    r = _rodar(["gh", "secret", "set", nome, "-R", REPO,
                "--body", arquivo.read_text(encoding="utf-8-sig")],
               capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  secret {nome} enviado")
        return True
    print(f"  ! secret {nome} falhou: {r.stderr.strip()[:200]}")
    return False


def instalar_youtube(pular_marca: bool = False) -> None:
    passo(1, "Procurando o JSON da credencial OAuth")
    origem = achar_client_secret()
    if not origem:
        raise SystemExit(
            "Não achei o JSON da credencial.\n"
            "  → Console do Cloud → Credenciais → Criar credencial → "
            "ID do cliente OAuth → **App para computador** → baixar.\n"
            "  Deixe o arquivo na pasta Downloads e rode isto de novo.")
    CRED.mkdir(parents=True, exist_ok=True)
    destino = CRED / "client_secret.json"
    if origem != destino:
        shutil.copyfile(origem, destino)
        print(f"  {origem.name} → credenciais/gta/client_secret.json")
    else:
        print("  já estava em credenciais/gta/client_secret.json")

    passo(2, "Abrindo a tela de consentimento do Google")
    print("  ESCOLHA A CONTA/CANAL NOVO e clique em Permitir.")
    print("  (é o único clique que não dá para automatizar)")
    r = _rodar([sys.executable, "produzir/autorizar.py", "--canal", "gta"])
    if r.returncode != 0:
        raise SystemExit("A autorização não terminou. Rode de novo.")

    passo(3, "Lendo o channel_id do próprio token")
    from nucleo import youtube_api
    yt = youtube_api.servico(CRED)
    cid, titulo = youtube_api.canal_do_token(yt)
    print(f"  canal: {titulo} ({cid})")
    gravar_channel_id(cid)

    passo(4, "Enviando os secrets para o GitHub")
    subir_secret("YT_CLIENT_SECRET_GTA", destino)
    subir_secret("YT_TOKEN_GTA", CRED / "token.json")

    if not pular_marca:
        passo(5, "Aplicando banner, bio, keywords e idioma no canal")
        _rodar([sys.executable, "produzir/aplicar_marca.py"])

    passo(6, "Conferindo a instalação")
    _rodar([sys.executable, "produzir/conferir_instalacao.py"])

    print("\nPronto. O YouTube publica sozinho a partir da próxima execução do "
          "workflow Publicar.\nPara ver agora, sem esperar o cron:")
    print("  gh workflow run Publicar -R " + REPO + " -f forcar_tipo=short")
    print("\nFalta pelo Studio (não tem API): avatar, nome, handle, trailer "
          "para não inscritos e a seção Links.")


def instalar_analytics() -> None:
    passo(1, "Token de Analytics (somente leitura)")
    r = _rodar([sys.executable, "produzir/autorizar.py", "--canal", "gta",
                "--analytics"])
    if r.returncode != 0:
        raise SystemExit("A autorização não terminou.")
    subir_secret("YT_TOKEN_ANALYTICS_GTA", CRED / "token_analytics.json")


# ---------------------------------------------------------------- Instagram --

def _do_clipboard() -> str:
    """Lê o token da área de transferência, sem ele passar por lugar nenhum.

    O portal da Meta tem um botão de copiar; assim o token vai do navegador
    direto para o secret, sem ser digitado, sem aparecer na tela e sem entrar
    no histórico do terminal.
    """
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-Clipboard -Raw"],
                           capture_output=True, text=True, timeout=30)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def instalar_instagram(do_clipboard: bool = True) -> None:
    import requests

    passo(1, "Token longo da Graph API")
    token = ""
    if do_clipboard:
        token = _do_clipboard()
        if token.startswith("IG") or (len(token) > 60 and " " not in token):
            print(f"  peguei um token da área de transferência "
                  f"({len(token)} caracteres). Não vou mostrá-lo.")
        else:
            print("  a área de transferência não tem cara de token; vou pedir.")
            token = ""
    if not token:
        print("  Cole o token com instagram_business_content_publish.")
        print("  Ele NÃO aparece na tela e não vai para log nenhum.")
        token = getpass.getpass("  token: ").strip()
    if not token:
        raise SystemExit("Nada colado; nada foi enviado.")

    passo(2, "Descobrindo o IG_USER_ID em graph.instagram.com/me")
    try:
        j = requests.get(f"{GRAPH}/me", timeout=60, params={
            "fields": "id,username", "access_token": token}).json()
    except Exception as exc:
        raise SystemExit(f"Não consegui falar com a Graph API: {exc}")
    if "id" not in j:
        raise SystemExit(
            f"A Graph API recusou o token: {j.get('error', j)}\n"
            f"  → confira se é token LONGO e se a conta é profissional "
            f"vinculada a uma Página do Facebook.")
    print(f"  conta: @{j.get('username', '?')} — id {j['id']}")

    passo(3, "Enviando os secrets para o GitHub")
    for nome, valor in (("IG_USER_ID_GTA", j["id"]), ("IG_TOKEN_GTA", token)):
        r = _rodar(["gh", "secret", "set", nome, "-R", REPO, "--body", valor],
                   capture_output=True, text=True)
        print(f"  secret {nome} "
              f"{'enviado' if r.returncode == 0 else '! ' + r.stderr[:120]}")

    passo(4, "Conferindo")
    _rodar([sys.executable, "produzir/conferir_instalacao.py"])
    print("\nO Instagram publica sozinho a partir da próxima execução.")


def instalar_tiktok(do_clipboard: bool = True) -> None:
    """Chave do Zernio → secret, e liga o espelho do TikTok no config.

    O Zernio é a ponte porque a Content Posting API do TikTok só publica
    público depois de auditoria do app. A chave sai do painel em API Keys;
    como toda credencial desta casa, ela vai da área de transferência direto
    para o secret — sem passar por chat, por log ou pela tela.
    """
    passo(1, "Chave da API do Zernio")
    chave = _do_clipboard() if do_clipboard else ""
    if chave and (len(chave) < 20 or " " in chave):
        print("  a área de transferência não tem cara de chave; vou pedir.")
        chave = ""
    if chave:
        print(f"  peguei uma chave da área de transferência "
              f"({len(chave)} caracteres). Não vou mostrá-la.")
    else:
        print("  Cole a chave do painel do Zernio (menu → API Keys).")
        chave = getpass.getpass("  chave: ").strip()
    if not chave:
        raise SystemExit("Nada colado; nada foi enviado.")

    passo(2, "Conferindo a chave e a conta conectada")
    import requests
    try:
        r = requests.get("https://api.zernio.com/v1/accounts", timeout=60,
                         headers={"Authorization": f"Bearer {chave}"})
        j = r.json() if r.headers.get("content-type", "").startswith(
            "application/json") else {}
    except Exception as exc:
        raise SystemExit(f"Não consegui falar com o Zernio: {exc}")
    if r.status_code >= 400:
        raise SystemExit(f"O Zernio recusou a chave (HTTP {r.status_code}): "
                         f"{str(j)[:200]}")
    contas = j.get("data", j if isinstance(j, list) else [])
    nomes = [c.get("username") or c.get("name") or c.get("id")
             for c in contas] if isinstance(contas, list) else []
    print(f"  contas conectadas: {', '.join(str(n) for n in nomes) or '(none)'}")
    if not any("rumoavicecity" in str(n).lower() for n in nomes):
        print("  ⚠ @rumoavicecity não aparece na lista. Conecte-a em "
              "New Connection → TikTok antes de ligar o espelho.")

    passo(3, "Enviando o secret")
    r = _rodar(["gh", "secret", "set", "ZERNIO_KEY_GTA", "-R", REPO,
                "--body", chave], capture_output=True, text=True)
    print(f"  secret ZERNIO_KEY_GTA "
          f"{'enviado' if r.returncode == 0 else '! ' + r.stderr[:120]}")

    passo(4, "Ligando tiktok.ativo no config")
    cfg_path = RAIZ / "publicador" / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg.setdefault("tiktok", {})["ativo"] = True
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print("  tiktok.ativo: true — falta commitar e dar push")

    passo(5, "Conferindo")
    _rodar([sys.executable, "produzir/conferir_instalacao.py"])


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Instala o que vem depois de criar a conta e o canal")
    ap.add_argument("alvo",
                    choices=["youtube", "analytics", "instagram",
                             "tiktok"],
                    nargs="?", default="youtube")
    ap.add_argument("--pular-marca", action="store_true")
    ap.add_argument("--sem-clipboard", action="store_true",
                    help="não tenta ler o token da área de transferência")
    a = ap.parse_args()
    if a.alvo == "youtube":
        instalar_youtube(a.pular_marca)
    elif a.alvo == "analytics":
        instalar_analytics()
    elif a.alvo == "tiktok":
        instalar_tiktok(not a.sem_clipboard)
    else:
        instalar_instagram(not a.sem_clipboard)


if __name__ == "__main__":
    main()
