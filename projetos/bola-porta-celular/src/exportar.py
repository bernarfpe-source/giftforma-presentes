# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Arquivos de entrega: um 3MF por peca (ja deitada para imprimir) e o STEP da montagem.

Rodar:  cad run src/exportar.py
"""
from pathlib import Path

from cad import model

import bola
import impressao

PASTA = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    model.export(bola.bola_5_pecas(), PASTA / "STEP/bola_5_pecas.step")
    for m in impressao.TODAS:
        nome = m.__name__.removeprefix("imprimir_")
        # malha fina: as folgas de encaixe sao de 0,2 mm
        model.export(m(), PASTA / f"3MF/{nome}.3mf", tolerance=0.02)
