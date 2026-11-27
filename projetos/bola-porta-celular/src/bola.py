# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Bola porta-celular + porta-canetas (brinde Rio Novo / FMT) em pecas encaixadas, cada uma de uma cor,
para impressora de um bico (FDM, PLA), todas imprimiveis SEM suporte:

  1) corpo_inferior - metade de baixo da bola (imprime de boca para baixo); pino embaixo entra na base;
  1) corpo_superior - metade de cima (imprime com o topo no prato); o ressalto de baixo entra no canal
                      da metade de baixo; face plana na frente com 2 furos para os pinos do encosto;
  2) encosto        - placa de apoio do celular;
  3) suporte        - bandeja de baixo do celular (aba e vao do cabo); entra no recorte da base e
                      recebe a borda de baixo do encosto;
  4) aro            - anel do topo, espiga conica que entra na boca da bola;
  5) base           - disco de 120 mm com berco;
  +  pastilha_rio_novo, pastilha_fmt - logos de encaixar nos rebaixos planos dos lados da bola.
     A Rio Novo tem fundo + rio (relevo 1,0 mm) + letras (relevo 2,0 mm): trocando o filamento
     na camada do rio e na das letras ela sai branca, azul e verde numa impressora de um bico.
     A da FMT e lisa (lugar reservado) ate chegar o arquivo do logo.

Folga de encaixe: FOLGA por lado (0,2 mm).
Rodar:      cad run src/bola.py
Exportar:   cad run src/exportar.py   (um 3MF por peca, ja deitada para imprimir, e o STEP da montagem)
Check:      cad model dfm "$ID" --process printing --technology fdm --material pla

Milimetros, +Z para cima, a FRENTE (onde fica o celular) e -Y.
"""
import math
import os

import build123d as bd
from cad import model
from cad.build123d import memo

AQUI = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ PARAMETROS
R = model.param("raio_bola", 54.0, min=40, max=60, unit="mm")
PAREDE = model.param("parede", 3.0, min=2, max=5, unit="mm")
ANG_APOIO = model.param("inclinacao_celular", 75.0, min=65, max=88, unit="deg")
D_APOIO = model.param("profundidade_face", 30.0, min=15, max=40, unit="mm")
CELULAR_ESP = model.param("encaixe_celular", 14.0, min=9, max=20, unit="mm")
VAO_CABO = model.param("vao_cabo", 24.0, min=0, max=50, unit="mm")
LOGO_LARG = model.param("largura_logo", 44.0, min=25, max=50, unit="mm")
FOLGA = model.param("folga_encaixe", 0.2, min=0.1, max=0.4, unit="mm")

ALTURA = 110.0        # altura total (topo do aro)
BASE_R = 60.0         # raio da base (120 mm)
BASE_H = 8.0          # espessura da base; a bola assenta em cima
ZC = BASE_H + 50.0    # centro da bola: o fundo plano fica em z = BASE_H
Z_TOPO = ZC + 39.0    # corte do topo da bola (onde o aro assenta)
Z_CORTE = ZC - 12.0   # divisao entre as duas metades do corpo (abaixo dos logos)
RESSALTO_H, RESSALTO_ESP = 3.0, 1.4     # encaixe entre as metades
Z_FUNDO_CONE = ZC - 22.0                # abaixo disso o fundo da cavidade e um cone de 45 graus
BERCO_H = 12.0        # altura do berco da base em volta da bola
PINO_BOLA_R, PINO_BOLA_H = 8.0, 4.0
ENC_ESP, ENC_LARG = 4.0, 72.0           # encosto
ENC_Z0, ENC_Z1 = BASE_H + 2.0, Z_TOPO - 2.0
PISO_Z = 16.0                           # piso onde o celular apoia
ABA_H, ABA_ESP = 10.0, 4.0
SUP_LARG = 80.0
RECUO_SUP = 5.0       # o suporte vai ate 5 mm atras da face de apoio (parede atras do canal do encosto)
ARO_R_EXT = 38.5
ARO_ESPIGA = 5.0
GOMO = 0.6            # profundidade dos pentagonos rebaixados
PAST_ESP = 2.0        # espessura do fundo da pastilha
PAST_MARGEM = 4.0     # moldura da pastilha em volta do logo

PASTILHAS = [
    dict(nome="rio_novo", arquivo="../logos/rio-novo.png", largura=LOGO_LARG, azimute=100.0, dz=4.0,
         fundo="#F4F4F2", relevos={"azul": ("#0078C8", 1.0), "verde": ("#2E8B3C", 2.0)}),
    # Logo oficial da FMT: salvar em logos/fmt.png, por arquivo= e relevos= aqui (como na Rio Novo).
    dict(nome="fmt", arquivo=None, largura=30.0, altura=20.0, azimute=-100.0, dz=4.0,
         fundo="#B8B8B8", relevos={}),
]

CORES = {"corpo_inferior": "#F4F4F2", "corpo_superior": "#F4F4F2", "encosto": "#0078C8",
         "suporte": "#F2C200", "aro": "#1A1A1A", "base": "#2E8B3C"}

_a = math.radians(ANG_APOIO)
C = bd.Vector(0, 0, ZC)
N = bd.Vector(0, -math.sin(_a), math.cos(_a))      # normal da face de apoio (frente/cima)
CIMA = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


# ------------------------------------------------------------------ AJUDANTES
def plano_apoio(recuo=0.0):
    """Plano da face plana da frente; x para a direita, y subindo pela rampa, z = N."""
    return bd.Plane(origin=C + N * (D_APOIO - recuo), x_dir=(1, 0, 0), z_dir=N)


def esfera(r):
    return bd.Pos(*C) * bd.Sphere(r)


def acima(shape, z):
    return bd.split(shape, bd.Plane.XY.offset(z), keep=bd.Keep.TOP)


def abaixo(shape, z):
    return bd.split(shape, bd.Plane.XY.offset(z), keep=bd.Keep.BOTTOM)


def atras_da_face(shape, recuo=0.0):
    return bd.split(shape, plano_apoio(recuo), keep=bd.Keep.BOTTOM)


def cilindro(r, z0, z1, x=0.0, y=0.0):
    return bd.Pos(x, y, z0) * bd.Cylinder(r, z1 - z0, align=CIMA)


def cone(r0, r1, z0, z1):
    return bd.Pos(0, 0, z0) * bd.Cone(r0, r1, z1 - z0, align=CIMA)


def anel(r0, r1, z0, z1):
    return cilindro(r1, z0, z1) - cilindro(r0, z0 - 1, z1 + 1)


def caixa(x0, x1, y0, y1, z0, z1, raio=0.0):
    b = bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)
    return bd.fillet(b.edges().filter_by(bd.Axis.Z), raio) if raio else b


def r_esfera_em(r, z):
    return math.sqrt(max(r ** 2 - (z - ZC) ** 2, 0.0))


def y_local(z):
    """Coordenada y no plano de apoio da altura z."""
    return (z - (C + N * D_APOIO).Z) / math.sin(_a)


def boca():
    """Teto conico (45 graus) da cavidade: comeca em z_c com o raio da esfera interna e fecha 1:1
    ate o corte do topo. Devolve (z_c, raio em z_c, raio da boca em Z_TOPO)."""
    z_c = Z_TOPO - 10.0
    r_c = r_esfera_em(R - PAREDE, z_c)
    return z_c, r_c, r_c - (Z_TOPO - z_c)


def _encosta(a, b):
    x = a & b
    return x is not None and x.volume > 1e-3


def _maior(shape):
    return sorted(shape.solids(), key=lambda s: s.volume, reverse=True)[0]


# ------------------------------------------------------------------ GOMOS (icosaedro truncado)
def direcoes_pentagonos():
    phi = (1 + 5 ** 0.5) / 2
    vs = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            vs += [bd.Vector(0, s1, s2 * phi), bd.Vector(s1, s2 * phi, 0), bd.Vector(s2 * phi, 0, s1)]
    rot = bd.Rot(18, 31, 7)   # gira o padrao para nao cair um pentagono no meio do logo
    return [(rot * bd.Pos(*v)).position.normalized() for v in vs]


def pentagonos(evitar):
    vs = direcoes_pentagonos()
    casca = esfera(R + 1) - esfera(R - GOMO)
    gomos = []
    for v in vs:
        viz = [w for w in vs if 0.4 < v.dot(w) < 0.5]
        cantos = [(v + (w - v) / 3).normalized() for w in viz]
        ref = (cantos[0] - v * cantos[0].dot(v)).normalized()
        perp = v.cross(ref)
        cantos.sort(key=lambda d: math.atan2(d.dot(perp), d.dot(ref)))
        perto = bd.Wire.make_polygon([C + d * 2 for d in cantos], close=True)
        longe = bd.Wire.make_polygon([C + d * (R * 1.3) for d in cantos], close=True)
        g = bd.Solid.make_loft([perto, longe]) & casca
        if not any(_encosta(g, e) for e in evitar):
            gomos.append(g)
    return gomos


# ------------------------------------------------------------------ LOGO (vetoriza o PNG por cor)
def limpa_mascaras(mascaras, px):
    """Imprimivel em FDM: fecha vaos menores que `px` pixels (entre letras e entre cores),
    dando cada pixel preenchido a cor mais proxima, e engrossa os tracos 1 px."""
    import cv2
    import numpy as np

    nomes = list(mascaras)
    ms = [cv2.morphologyEx(mascaras[n].astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) for n in nomes]
    uniao = np.zeros_like(ms[0])
    for m in ms:
        uniao |= m
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (px | 1, px | 1))
    fechado = cv2.morphologyEx(uniao, cv2.MORPH_CLOSE, k)
    dist = [cv2.distanceTransform(255 - m, cv2.DIST_L2, 3) for m in ms]
    mais_perto = np.argmin(np.stack(dist), axis=0)
    um = np.ones((3, 3), np.uint8)
    saida = {}
    for i, n in enumerate(nomes):
        m = ((fechado > 0) & (mais_perto == i)).astype(np.uint8) * 255
        saida[n] = cv2.dilate(m, um) & cv2.dilate(fechado, um)
    return saida


def contornos_por_cor(caminho, largura_mm, minimo_mm=1.0):
    import cv2
    import numpy as np

    img = cv2.imread(caminho, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(caminho)
    if img.ndim == 3 and img.shape[2] == 4:
        alfa = img[:, :, 3:4] / 255.0
        img = (img[:, :, :3] * alfa + 255 * (1 - alfa)).astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = (hsv[:, :, i].astype(int) for i in range(3))
    colorido = (s > 70) & (v > 50)
    mascaras = {"azul": colorido & (h >= 90) & (h <= 130), "verde": colorido & (h >= 35) & (h < 90)}
    alt, larg = img.shape[:2]
    px_mm = larg / largura_mm
    mascaras = limpa_mascaras(mascaras, int(math.ceil(minimo_mm * px_mm)))
    # tira as pontas mais finas que 0,9 mm (a cauda do rio): viram parede fina demais em FDM
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(math.ceil(0.9 * px_mm)) | 1,) * 2)
    mascaras = {c: cv2.morphologyEx(m, cv2.MORPH_OPEN, k) for c, m in mascaras.items()}
    saida = {}
    for cor, m in mascaras.items():
        conts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        grupos = []
        if hier is not None:
            for i, c in enumerate(conts):
                if hier[0][i][3] != -1 or cv2.contourArea(c) < 12:
                    continue
                furos, j = [], hier[0][i][2]
                while j != -1:
                    if cv2.contourArea(conts[j]) >= 6:
                        furos.append(conts[j])
                    j = hier[0][j][0]
                grupos.append((c, furos))
        saida[cor] = grupos
    return larg, alt, saida


def faces_do_logo(grupos, escala, larg, alt):
    import cv2

    def wire(c):
        c = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2)
        pts = [bd.Vector((x - larg / 2) * escala, (alt / 2 - y) * escala, 0) for x, y in c]
        return bd.Wire.make_polygon(pts, close=True) if len(pts) >= 3 else None

    faces = []
    for externo, furos in grupos:
        w = wire(externo)
        if w is not None:
            faces.append(bd.Face(w, [f for f in (wire(h) for h in furos) if f is not None]))
    return faces


@memo
def desenho_do_logo(arquivo, largura):
    """Faces 2D do logo por cor (no plano XY, centradas) e a altura do desenho em mm."""
    caminho = os.path.normpath(os.path.join(AQUI, arquivo))
    larg, alt, grupos = contornos_por_cor(caminho, largura)
    esc = largura / larg
    return {cor: faces_do_logo(gs, esc, larg, alt) for cor, gs in grupos.items()}, alt * esc


# ------------------------------------------------------------------ PASTILHAS (logos de encaixar)
def plano_lateral(azimute, dz):
    az = math.radians(azimute)
    u = bd.Vector(-math.sin(az), -math.cos(az), 0)     # para fora da bola
    tx = bd.Vector(0, 0, 1).cross(u)                    # da esquerda para a direita de quem olha
    return bd.Plane(origin=C + bd.Vector(0, 0, dz), x_dir=tx, z_dir=u)


def medidas_pastilha(p):
    """(faces por cor, largura, altura, d_face, d_fundo): a face da pastilha fica plana a d_face do
    centro da bola, com os cantos rentes a superficie; o fundo do rebaixo fica a d_fundo."""
    if p["arquivo"]:
        faces, alt_logo = desenho_do_logo(p["arquivo"], p["largura"])
    else:
        faces, alt_logo = {}, p["altura"]
    w, h = p["largura"] + 2 * PAST_MARGEM, alt_logo + 2 * PAST_MARGEM
    d_face = math.sqrt(R ** 2 - (w / 2) ** 2 - (h / 2 + abs(p["dz"])) ** 2) - 0.3
    return faces, w, h, d_face, d_face - PAST_ESP


def contorno(w, h, folga=0.0):
    return bd.RectangleRounded(w + 2 * folga, h + 2 * folga, 4.0 + folga)


def rebaixo(p, folga=FOLGA):
    """O vao da pastilha na bola (do fundo para fora). A parede de baixo, acima da face da pastilha,
    e chanfrada a 45 graus: a metade de cima imprime de cabeca para baixo e ali seria um teto."""
    _, w, h, d_face, d_fundo = medidas_pastilha(p)
    pl = plano_lateral(p["azimute"], p["dz"])
    reto = bd.Pos(0, 0, d_fundo) * bd.extrude(contorno(w, h, folga), R + 5 - d_fundo)
    L = R + 5 - d_face
    perfil = bd.Pos(0, 0, d_face) * contorno(w, h, folga)
    w0 = perfil.faces()[0].outer_wire()
    chanfro = bd.Solid.make_loft([w0, bd.Pos(0, -L, L) * w0])
    return pl.location * (reto + chanfro)


def reforco(p):
    """Bloco por dentro da bola atras do rebaixo, com laterais a 45 graus (imprime sem suporte)."""
    _, w, h, _, d_fundo = medidas_pastilha(p)
    pl = plano_lateral(p["azimute"], p["dz"])
    d0 = d_fundo - 2.5
    return pl.location * (bd.Pos(0, 0, d0) * bd.extrude(contorno(w, h, 1.0), R - d0, taper=-44))


def pecas_pastilha_local(p):
    """Partes da pastilha no plano dela (fundo em z = 0): fundo e o relevo de cada cor do logo."""
    faces, w, h, _, _ = medidas_pastilha(p)
    partes = [("fundo", p["fundo"], bd.extrude(contorno(w, h), PAST_ESP))]
    for cor, (hexa, alto) in p["relevos"].items():
        fs = faces.get(cor, [])
        if fs:
            relevo = bd.extrude(fs[0], alto)
            for f in fs[1:]:
                relevo = relevo + bd.extrude(f, alto)
            partes.append((cor, hexa, bd.Pos(0, 0, PAST_ESP) * relevo))
    return partes


def pecas_pastilha(p):
    """Partes da pastilha no lugar, na bola."""
    _, _, _, _, d_fundo = medidas_pastilha(p)
    loc = plano_lateral(p["azimute"], p["dz"]).location * bd.Pos(0, 0, d_fundo)
    return [(n, c, loc * s) for n, c, s in pecas_pastilha_local(p)]


def pastilha(p):
    filhos = []
    for nome, hexa, s in pecas_pastilha(p):
        s.label, s.color = nome, hexa
        filhos.append(s)
    c = bd.Compound(children=filhos)
    c.label = f"pastilha_{p['nome']}"
    return c


@model
def pastilha_rio_novo():
    return pastilha(PASTILHAS[0])


@model
def pastilha_fmt():
    return pastilha(PASTILHAS[1])


# ------------------------------------------------------------------ FORMAS USADAS EM MAIS DE UMA PECA
def pinos_encosto_local(folga=0.0):
    pinos = [bd.Pos(x, -5.0, folga) * bd.Box(12 + 2 * folga, 6 + 2 * folga, PAREDE + 2 + 2 * folga,
                                             align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
             for x in (-20.0, 20.0)]
    return pinos[0] + pinos[1]


def forma_encosto_local(folga=0.0):
    """Encosto no plano da face de apoio: placa de z = 0 (costas) a ENC_ESP (frente), pinos em z < 0."""
    y0, y1 = y_local(ENC_Z0), y_local(ENC_Z1)
    placa = bd.Pos(0, (y0 + y1) / 2, -folga) * bd.extrude(
        bd.RectangleRounded(ENC_LARG + 2 * folga, (y1 - y0) + 2 * folga, 8.0), ENC_ESP + 2 * folga)
    return placa + pinos_encosto_local(folga)


def pinos_encosto(folga=0.0):
    return plano_apoio().location * pinos_encosto_local(folga)


def forma_encosto(folga=0.0):
    return plano_apoio().location * forma_encosto_local(folga)


def forma_suporte(folga=0.0):
    """Bloco cheio do suporte (antes dos recortes); tambem e o recorte da base."""
    p = plano_apoio()
    frente = (p.location * bd.Pos(0, y_local(PISO_Z), ENC_ESP)).position.Y
    y_aba = frente - CELULAR_ESP
    y_tras = (p.location * bd.Pos(0, y_local(ENC_Z0), 0)).position.Y + 10.0
    f = folga
    bloco = caixa(-SUP_LARG / 2 - f, SUP_LARG / 2 + f, y_aba - ABA_ESP - f, y_tras, 0, PISO_Z, 4.0)
    return bd.split(bloco, plano_apoio(RECUO_SUP + f), keep=bd.Keep.TOP), y_aba


def ressalto(folga=0.0):
    """Anel que desce da metade de cima e entra na de baixo."""
    r0 = r_esfera_em(R - PAREDE, Z_CORTE) - 0.6
    # o canal (com folga) abre para dentro da bola: degrau, sem parede fina entre o canal e a cavidade
    a = anel(r0 - (3.0 if folga else 0.0), r0 + RESSALTO_ESP + folga, Z_CORTE - RESSALTO_H - folga,
             Z_CORTE + (1.0 if folga else 0.0))
    return atras_da_face(a, PAREDE + 1.0 - folga)


# ------------------------------------------------------------------ CORPO
def cavidade():
    z_c, r_c, r_top = boca()
    teto = cone(r_c, r_top - 1.0, z_c, Z_TOPO + 1)
    # fundo em "V": parede a 45 graus por fora e um cone (45 graus) no meio, sem nenhum teto plano
    # quando a metade de baixo imprime de boca para baixo; as canetas apoiam no anel do V
    z_f = BASE_H + PAREDE
    r_b = r_esfera_em(R - PAREDE, Z_FUNDO_CONE)
    r_v = r_b - (Z_FUNDO_CONE - z_f)
    fundo = cone(r_v, r_b, z_f, Z_FUNDO_CONE + 0.01) - cone(r_v, 0.0, z_f - 0.01, z_f + r_v)
    meio = abaixo(acima(esfera(R - PAREDE), Z_FUNDO_CONE), z_c)
    return atras_da_face(fundo + meio + teto, PAREDE)


@memo
def corpo_inteiro():
    """A bola inteira, oca, com os rebaixos das pastilhas, gomos e furos do encosto (antes de dividir)."""
    bola = atras_da_face(abaixo(acima(esfera(R), BASE_H), Z_TOPO))
    bola = bola - cavidade()
    for p in PASTILHAS:
        bola = bola + acima(reforco(p) & esfera(R - 0.5), Z_CORTE)
    bola = bola + cilindro(PINO_BOLA_R, BASE_H - PINO_BOLA_H, BASE_H + 0.5)
    # sem gomo nas pastilhas nem cortado pela divisao das metades (deixaria quinas finas)
    evitar = [rebaixo(p, PAST_MARGEM) for p in PASTILHAS] + [cilindro(R + 2, Z_CORTE - 1.5, Z_CORTE + 1.5)]
    gomos = pentagonos(evitar)
    if gomos:
        bola = bola - bd.Compound(gomos)
    for p in PASTILHAS:
        bola = bola - rebaixo(p)
    return bola - pinos_encosto(FOLGA)


@model
def corpo_inferior():
    """1a) Metade de baixo da bola."""
    c = abaixo(corpo_inteiro(), Z_CORTE) - ressalto(FOLGA)
    c.label = "corpo_inferior"
    return c


@model
def corpo_superior():
    """1b) Metade de cima da bola, com o ressalto de encaixe."""
    c = acima(corpo_inteiro(), Z_CORTE) + ressalto()
    c.label = "corpo_superior"
    return c


# ------------------------------------------------------------------ AS OUTRAS PECAS
@model
def encosto():
    """2) Placa de apoio do celular."""
    e = forma_encosto()
    e.label = "encosto"
    return e


@model
def suporte():
    """3) Bandeja de baixo: piso, aba da frente com vao de cabo, canal do encosto."""
    bloco, y_aba = forma_suporte()
    aba = caixa(-SUP_LARG / 2, SUP_LARG / 2, y_aba - ABA_ESP, y_aba, 0, PISO_Z + ABA_H, 1.5)
    if VAO_CABO > 0:
        aba = aba - bd.Pos(0, y_aba - ABA_ESP / 2, PISO_Z + 20) * bd.Box(VAO_CABO, ABA_ESP + 2, 40)
    s = _maior(bloco + aba - esfera(R + FOLGA) - forma_encosto(FOLGA))
    s.label = "suporte"
    return s


@model
def aro():
    """4) Anel do topo, com espiga conica que entra na boca da bola."""
    _, _, r_boca = boca()
    r_int = r_boca - FOLGA - 2.6
    a = cilindro(ARO_R_EXT, Z_TOPO, ALTURA) - cilindro(r_int, Z_TOPO - 1, ALTURA + 1)
    a = bd.fillet(a.edges().filter_by(bd.GeomType.CIRCLE).sort_by(bd.Axis.Z)[-2:], 1.5)
    a = atras_da_face(a)
    f = FOLGA * 1.42
    espiga = cone(r_boca + ARO_ESPIGA - f, r_boca - f, Z_TOPO - ARO_ESPIGA, Z_TOPO) + cilindro(r_boca - f, Z_TOPO - 0.01, Z_TOPO + 0.5)
    espiga = atras_da_face(espiga - cilindro(r_int, Z_TOPO - ARO_ESPIGA - 1, Z_TOPO + 1), PAREDE + FOLGA)
    a = a + espiga
    a.label = "aro"
    return a


@model
def base():
    """5) Disco de 120 mm com berco, furo do pino da bola e recorte do suporte."""
    berco = cone(44.0, 42.0, BASE_H, BASE_H + BERCO_H) - esfera(R + FOLGA)
    berco = atras_da_face(berco, RECUO_SUP - 1.0)
    b = cilindro(BASE_R, 0, BASE_H)
    b = bd.chamfer(b.edges().filter_by(bd.GeomType.CIRCLE).sort_by(bd.Axis.Z)[0], 1.0)
    b = b + berco - cilindro(PINO_BOLA_R + FOLGA, BASE_H - PINO_BOLA_H - 0.5, BASE_H + 1)
    b = _maior(b - forma_suporte(FOLGA)[0])
    b.label = "base"
    return b


PECAS = [("corpo_inferior", corpo_inferior), ("corpo_superior", corpo_superior), ("encosto", encosto),
         ("suporte", suporte), ("aro", aro), ("base", base)]
PASTILHAS_MODELOS = [("pastilha_rio_novo", pastilha_rio_novo), ("pastilha_fmt", pastilha_fmt)]


# ------------------------------------------------------------------ MONTAGEM
@model
def bola_5_pecas():
    from bd_materials import plastics
    from bd_materials.processes import fdm

    pla = plastics.pla(process=fdm(layer_height_mm=0.2))
    partes = []
    for nome, m in PECAS:
        s = m().shape
        s.label = nome
        s.material = pla            # o material antes da cor: atribuir o material troca a cor
        s.color = CORES[nome]
        partes.append(s)
    for nome, m in PASTILHAS_MODELOS:
        c = m().shape
        for filho in c.children:
            cor = filho.color
            filho.material = pla
            filho.color = cor
        c.label = nome
        partes.append(c)
    montagem = bd.Compound(children=partes)
    montagem.label = "bola_5_pecas"
    bb = montagem.bounding_box()
    assert abs(bb.max.Z - ALTURA) < 0.5, bb.max.Z
    assert abs(bb.size.X - 2 * BASE_R) < 0.5, bb.size.X
    return montagem


if __name__ == "__main__":
    bola_5_pecas()
