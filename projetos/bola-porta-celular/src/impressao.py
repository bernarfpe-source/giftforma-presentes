# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Cada peca da bola na posicao de imprimir (no prato, z = 0, centrada), sem suporte.

  corpo_inferior   - de boca para baixo (a divisao no prato)
  corpo_superior   - de cabeca para baixo (o topo no prato)
  encosto          - deitado com a frente no prato (pinos para cima)
  suporte, base    - como ficam na mesa
  aro              - de cabeca para baixo (o topo no prato, espiga para cima)
  pastilhas        - deitadas, fundo no prato, relevo para cima. Rio Novo: imprimir em branco e trocar
                     o filamento na 1a camada acima de 2,0 mm (azul, rio) e na 1a acima de 3,0 mm (verde, letras).

Rodar:  cad run src/impressao.py
Check:  cad model dfm "$ID" --process printing --technology fdm --material pla
"""
import build123d as bd
from cad import model

import bola


def no_prato(shape, virar=False):
    if virar:
        shape = bd.Rot(180, 0, 0) * shape
    bb = shape.bounding_box()
    return bd.Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shape


def peca(shape, nome, cor):
    from bd_materials import plastics
    from bd_materials.processes import fdm

    shape.label = nome
    shape.material = plastics.pla(process=fdm(layer_height_mm=0.2))
    shape.color = cor
    return shape


def pastilha_deitada(p):
    """A pastilha impressa e uma peca so: fundo e relevos fundidos, fundo no prato."""
    partes = [s for _, _, s in bola.pecas_pastilha_local(p)]
    s = partes[0]
    for o in partes[1:]:
        s = s + o
    return s


@model
def imprimir_corpo_inferior():
    return peca(no_prato(bola.corpo_inferior().shape, virar=True), "corpo_inferior", bola.CORES["corpo_inferior"])


@model
def imprimir_corpo_superior():
    return peca(no_prato(bola.corpo_superior().shape, virar=True), "corpo_superior", bola.CORES["corpo_superior"])


@model
def imprimir_encosto():
    # mesma geometria do modelo `encosto`, no plano da face: frente no prato, pinos para cima
    return peca(no_prato(bola.forma_encosto_local(), virar=True), "encosto", bola.CORES["encosto"])


@model
def imprimir_suporte():
    return peca(no_prato(bola.suporte().shape), "suporte", bola.CORES["suporte"])


@model
def imprimir_aro():
    return peca(no_prato(bola.aro().shape, virar=True), "aro", bola.CORES["aro"])


@model
def imprimir_base():
    return peca(no_prato(bola.base().shape), "base", bola.CORES["base"])


def _pastilha(i):
    p = bola.PASTILHAS[i]
    return peca(no_prato(pastilha_deitada(p)), f"pastilha_{p['nome']}", p["fundo"])


@model
def imprimir_pastilha_rio_novo():
    return _pastilha(0)


@model
def imprimir_pastilha_fmt():
    return _pastilha(1)


TODAS = [imprimir_corpo_inferior, imprimir_corpo_superior, imprimir_encosto, imprimir_suporte,
         imprimir_aro, imprimir_base, imprimir_pastilha_rio_novo, imprimir_pastilha_fmt]

if __name__ == "__main__":
    for m in TODAS:
        m()
