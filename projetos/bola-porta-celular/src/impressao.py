# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Cada peca da bola na posicao de imprimir (no prato, z = 0, centrada), sem suporte.

  corpo_inferior   - de boca para baixo (a divisao no prato); 2 cores: branco + gomos pretos (AMS)
  corpo_superior   - de cabeca para baixo (o topo no prato); 2 cores: branco + gomos pretos (AMS)
                     sem AMS: imprimir so o branco e pintar os rebaixos dos gomos de preto
  encosto          - deitado de costas no prato (placa com os pezinhos)
  apoios_celular   - os dois blocos verdes, de pe
  suporte, base    - como ficam na mesa
  aro              - de cabeca para baixo
  logos            - plaquinha de tras no prato, colunas para cima
  emblema_bola     - fundo no prato; imprimir em branco e trocar para preto na 1a camada acima de 2,0 mm

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


def _metade_com_gomos(corpo, gomos, nome):
    """Metade da bola + gomos pretos, as duas cores no mesmo lugar (multicor/AMS)."""
    c = peca(corpo().shape, nome, bola.CORES[nome])
    g = peca(gomos().shape, f"gomos_{nome.split('_')[1]}", bola.CORES[f"gomos_{nome.split('_')[1]}"])
    junto = no_prato(bd.Compound(children=[c, g]), virar=True)
    junto.label = nome
    return junto


@model
def imprimir_corpo_inferior():
    return _metade_com_gomos(bola.corpo_inferior, bola.gomos_inferior, "corpo_inferior")


@model
def imprimir_corpo_superior():
    return _metade_com_gomos(bola.corpo_superior, bola.gomos_superior, "corpo_superior")


@model
def imprimir_encosto():
    # mesma geometria do modelo `encosto`, no plano do canal; a rampa (y local) vira a vertical
    # placa deitada de costas no prato (os pezinhos ficam no mesmo plano: sem suporte)
    return peca(no_prato(bola.forma_encosto_local_recortada()), "encosto", bola.CORES["encosto"])


@model
def imprimir_suporte():
    return peca(no_prato(bola.suporte().shape), "suporte", bola.CORES["suporte"])


@model
def imprimir_apoios_celular():
    """Os dois blocos verdes, de pe como ficam na bandeja."""
    a = bd.Compound([bola.bloco_verde(1), bola.bloco_verde(-1)])
    return peca(no_prato(a), "apoios_celular", bola.CORES["apoios_celular"])


@model
def imprimir_aro():
    return peca(no_prato(bola.aro().shape, virar=True), "aro", bola.CORES["aro"])


@model
def imprimir_base():
    return peca(no_prato(bola.base().shape), "base", bola.CORES["base"])


def _logo(i, cor, nome):
    return peca(no_prato(bola.geometria_logo(i)[0][cor]), nome, bola.LOGOS[i]["cores"][cor])


@model
def imprimir_logo_rio_novo_azul():
    return _logo(0, "azul", "logo_rio_novo_azul")


@model
def imprimir_logo_rio_novo_verde():
    return _logo(0, "verde", "logo_rio_novo_verde")


@model
def imprimir_logo_rio_novo_faixa_verde():
    return _logo(0, "faixa_verde", "logo_rio_novo_faixa_verde")


@model
def imprimir_logo_rio_novo_faixa_amarela():
    return _logo(0, "faixa_amarela", "logo_rio_novo_faixa_amarela")


@model
def imprimir_logo_fmf_verde():
    return _logo(1, "verde", "logo_fmf_verde")


@model
def imprimir_logo_fmf_azul():
    return _logo(1, "azul", "logo_fmf_azul")


@model
def imprimir_logo_fmf_branco():
    return _logo(1, "branco", "logo_fmf_branco")


@model
def imprimir_logo_fmf_amarelo():
    return _logo(1, "amarelo", "logo_fmf_amarelo")


@model
def imprimir_emblema_bola():
    disco, pent = bola.emblema_local()
    return peca(no_prato(disco + pent), "emblema_bola", "#F4F4F2")


TODAS = [imprimir_corpo_inferior, imprimir_corpo_superior, imprimir_encosto, imprimir_suporte,
         imprimir_apoios_celular,
         imprimir_aro, imprimir_base, imprimir_logo_rio_novo_azul, imprimir_logo_rio_novo_verde,
         imprimir_logo_rio_novo_faixa_verde, imprimir_logo_rio_novo_faixa_amarela,
         imprimir_logo_fmf_verde, imprimir_logo_fmf_azul, imprimir_logo_fmf_branco,
         imprimir_logo_fmf_amarelo, imprimir_emblema_bola]

if __name__ == "__main__":
    for m in TODAS:
        m()
