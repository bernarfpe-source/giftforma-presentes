# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Animacao da montagem (GLB): as pecas chegam na ordem do LEIA-ME e terminam na bola completa.

Rodar:     cad run src/animacao.py
Exportar:  cad model export <id> GLB/montagem_animada.glb
O visualizador do text-to-cad toca a animacao do GLB (cad viewer GLB/montagem_animada.glb).
"""
import math

from cad import model
from cad.build123d import animation

import bola

DURACAO = 14.0
ZERO = (0.0, 0.0, 0.0)


def _lado(azimute, dist, dz=0.0):
    """Deslocamento para fora da bola, do lado de um logo."""
    az = math.radians(azimute)
    return (-math.sin(az) * dist, -math.cos(az) * dist, dz)


def _soma(a, b):
    return tuple(x + y for x, y in zip(a, b))


def entra(anim, peca, caminho):
    """`caminho`: [(t, deslocamento), ...]; a peca fica no primeiro deslocamento ate o primeiro t."""
    t0, d0 = caminho[0]
    keys = [(0.0, d0)] if t0 > 0 else []
    anim.channel(peca, path="translation", keys=keys + list(caminho))


def aparece(anim, peca, t):
    """A peca fica invisivel (escala 0) ate a sua vez de entrar."""
    anim.channel(peca, path="scale", keys=[(0.0, 0.0), (t, 1.0)], interpolation="STEP")


@model
def bola_montagem_animada():
    montagem = bola.bola_5_pecas().shape
    montagem.label = "bola_montagem_animada"
    a = math.radians(bola.ANG_APOIO)
    subida_fenda = (0.0, math.cos(a), math.sin(a))      # para cima, ao longo da face de apoio

    alto_bola = (0.0, 0.0, 70.0)   # metade de cima esperando no alto
    meio = (0.0, 0.0, 35.0)        # bola fechada, antes de descer na base
    anim = animation(montagem, "montagem", duration=DURACAO)

    # 1) logos entram na metade de cima (que espera no alto)
    sup = _soma(alto_bola, meio)
    for i, nome in enumerate(["logo_rio_novo_azul", "logo_rio_novo_verde",
                              "logo_rio_novo_faixa_verde", "logo_rio_novo_faixa_amarela"]):
        fora = _soma(sup, _lado(104.0, 95.0, 15.0))
        t = 0.8 + 0.35 * i
        entra(anim, nome, [(t, fora), (t + 1.2, sup), (3.6, sup), (5.0, meio), (6.4, ZERO)])
    for j, nome in enumerate(["logo_fmf_verde", "logo_fmf_azul", "logo_fmf_branco", "logo_fmf_amarelo"]):
        t = 1.2 + 0.3 * j
        entra(anim, nome, [(t, _soma(sup, _lado(-92.0, 95.0, 15.0))), (t + 1.2, sup), (3.6, sup),
                           (5.0, meio), (6.4, ZERO)])
    # 2) a metade de cima fecha a bola e a bola desce na base
    for peca in ("corpo_superior", "gomos_superior"):
        entra(anim, peca, [(3.6, sup), (5.0, meio), (6.4, ZERO)])
    for peca in ("corpo_inferior", "gomos_inferior"):
        entra(anim, peca, [(5.0, meio), (6.4, ZERO)])
    # 3) suporte pela frente, encosto descendo pela fenda
    entra(anim, "suporte", [(6.6, (0.0, -90.0, 0.0)), (7.8, ZERO)])
    entra(anim, "encosto", [(8.0, tuple(100.0 * v for v in subida_fenda)), (9.6, ZERO)])
    # 4) emblema na bandeja e aro travando o encosto
    entra(anim, "emblema_bola", [(9.8, (0.0, -60.0, 0.0)), (10.6, ZERO)])
    entra(anim, "aro", [(10.8, (0.0, 0.0, 60.0)), (12.0, ZERO)])
    for peca, t in [("suporte", 6.5), ("encosto", 7.9), ("emblema_bola", 9.7), ("aro", 10.7)]:
        aparece(anim, peca, t)
    return montagem


if __name__ == "__main__":
    bola_montagem_animada()
