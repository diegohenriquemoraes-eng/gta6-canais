"""Trilha ambiente PROCEDURAL para os vídeos longos — zero copyright.

Em vez de biblioteca de música (que sempre carrega risco de claim), o pad é
sintetizado aqui: acordes menores suaves em camadas de senos com envelope
lento. É nosso, determinístico (seed) e gratuito. Shorts seguem SEM música
(regra editorial herdada do Palabra Viva).

Sai um WAV mono 32 kHz; o render mixa baixinho sob a narração.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 32000

# progressões em lá menor (graus como semitons a partir da tônica)
PROGRESSOES = [
    [0, -4, 5, -2],   # Am - F - Dm - G (relativo)
    [0, 5, -4, -2],
    [0, -2, -4, 5],
]
ACORDE_MENOR = [0, 3, 7, 12]
ACORDE_MAIOR = [0, 4, 7, 12]


def _acorde(freq_base: float, semitons: list[int], dur: float,
            rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, dtype=np.float32)
    for st in semitons:
        f = freq_base * (2 ** (st / 12))
        detune = rng.uniform(0.9985, 1.0015)
        fase = rng.uniform(0, 2 * np.pi)
        # fundamental + 2º harmônico fraco: pad escuro, sem brilho agressivo
        out += np.sin(2 * np.pi * f * detune * t + fase).astype(np.float32)
        out += 0.35 * np.sin(2 * np.pi * 2 * f * detune * t + fase).astype(np.float32)
    # envelope lento (ataque/queda de 2,5 s) evita cliques na troca de acorde
    env = np.ones(n, dtype=np.float32)
    borda = min(int(2.5 * SR), n // 2)
    rampa = np.linspace(0, 1, borda, dtype=np.float32)
    env[:borda] = rampa
    env[-borda:] = rampa[::-1]
    return out * env


def gerar_trilha_fria(dur: float, seed: int, destino: Path) -> Path:
    """Trilha do Reel sem narração: pad escuro + sub-pulso lento.

    Nasceu em 13/08/2026, quando o Reel do Psicologia Fria perdeu a voz TTS.
    Sem narração o vídeo precisa de alguma coisa segurando o tempo, e silêncio
    puro no feed soa como vídeo quebrado. O pulso (um sub-grave a cada ~2 s,
    com queda rápida) faz o papel do metrônomo: o olho troca de bloco de texto
    junto com ele.

    Continua PROCEDURAL pelo mesmo motivo do pad dos longos — biblioteca de
    música de terceiros sempre carrega risco de claim, e aqui o risco seria no
    Instagram, onde um claim derruba o áudio do Reel inteiro.
    """
    rng = np.random.default_rng(seed)
    total = int(dur * SR)
    t = np.arange(total, dtype=np.float32) / SR

    # Faixa AUDÍVEL EM CELULAR: o alto-falante do telefone corta quase tudo
    # abaixo de ~200 Hz. A primeira versão desta trilha foi escrita em 55-82 Hz
    # (grave de fone) e no feed teria soado como vídeo mudo. A tônica agora
    # fica entre A3 e C4 e o acorde sobe daí.
    base = 220.0 * (2 ** (int(seed) % 4 / 12))
    mix = np.zeros(total, dtype=np.float32)
    for k, st in enumerate((0, 3, 7, 12)):          # menor com oitava
        f = base * (2 ** (st / 12))
        fase = rng.uniform(0, 2 * np.pi)
        detune = rng.uniform(0.999, 1.001)
        peso = (0.85, 0.55, 0.45, 0.25)[k]
        mix += peso * np.sin(2 * np.pi * f * detune * t + fase).astype(np.float32)

    # pulso a cada ~2 s: é o metrônomo do olho, que troca de bloco junto.
    # Duas oitavas (110 + 220) para existir tanto no fone quanto no celular.
    periodo = 2.0 + (seed % 3) * 0.25
    env = np.exp(-((t % periodo) / periodo) * 9.0).astype(np.float32)
    mix += env * 0.8 * (np.sin(2 * np.pi * 110.0 * t)
                        + 0.6 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)

    # ar: ruído filtrado bem baixo, só para o pad não soar sintetizado demais
    ruido = rng.standard_normal(total).astype(np.float32)
    kernel = np.ones(64, dtype=np.float32) / 64
    mix += np.convolve(ruido, kernel, mode="same") * 0.10

    # respiração lenta + rampas de borda (sem clique na emenda do loop)
    mix *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 12.0)).astype(np.float32)
    borda = min(int(0.6 * SR), total // 2)
    if borda:
        rampa = np.linspace(0, 1, borda, dtype=np.float32)
        mix[:borda] *= rampa
        mix[-borda:] *= rampa[::-1]

    pico = np.max(np.abs(mix)) or 1.0
    dados = (mix / pico * 0.5 * 32767).astype(np.int16)
    with wave.open(str(destino), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(dados.tobytes())
    return destino


def gerar_pad(dur: float, seed: int, destino: Path) -> Path:
    rng = np.random.default_rng(seed)
    prog = PROGRESSOES[seed % len(PROGRESSOES)]
    base = 110.0 * (2 ** (int(seed) % 5 / 12))  # tônica entre A2 e C#3
    dur_acorde = 18.0
    sobre = 2.5  # sobreposição = crossfade natural dos envelopes

    total = int(dur * SR)
    mix = np.zeros(total + int(dur_acorde * SR), dtype=np.float32)
    pos = 0.0
    i = 0
    while pos < dur:
        grau = prog[i % len(prog)]
        tipo = ACORDE_MENOR if i % len(prog) != 1 else ACORDE_MAIOR
        bloco = _acorde(base * (2 ** (grau / 12)), tipo, dur_acorde, rng)
        ini = int(pos * SR)
        mix[ini:ini + len(bloco)] += bloco
        pos += dur_acorde - sobre
        i += 1
    mix = mix[:total]

    # respiração de volume bem lenta (LFO de ~40 s)
    t = np.arange(total, dtype=np.float32) / SR
    mix *= (0.8 + 0.2 * np.sin(2 * np.pi * t / 40.0 + 1.0)).astype(np.float32)

    pico = np.max(np.abs(mix)) or 1.0
    mix = (mix / pico * 0.22 * 32767).astype(np.int16)

    with wave.open(str(destino), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(mix.tobytes())
    return destino
