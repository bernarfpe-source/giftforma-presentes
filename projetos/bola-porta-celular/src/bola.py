# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Bola porta-celular + porta-canetas (brinde Rio Novo / FMT), modelada com text-to-cad.

Bola de futebol com abertura no topo para canetas, face plana na frente onde o celular apoia
e base verde com bandeja. Quatro pecas, uma por cor (impressao multicor FDM, PLA):
branco (corpo), preto (pentagonos), verde (base, bandeja, moldura, texto do logo) e azul (rio do logo).

Rodar:      cad run src/bola.py
Exportar:   cad run src/exportar.py
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
R = model.param("raio_bola", 55.0, min=40, max=75, unit="mm")
PAREDE = model.param("parede", 3.0, min=1.6, max=6, unit="mm")
ANG_APOIO = model.param("inclinacao_celular", 78.0, min=65, max=88, unit="deg")
D_APOIO = model.param("profundidade_face", 24.0, min=10, max=35, unit="mm")
CELULAR_ESP = model.param("encaixe_celular", 14.0, min=9, max=20, unit="mm")
VAO_CABO = model.param("vao_cabo", 24.0, min=0, max=50, unit="mm")
LOGO_LARG = model.param("largura_logo", 50.0, min=25, max=70, unit="mm")

BASE_H = 5.0          # altura da base verde redonda
BASE_R = 44.0         # raio da base
ZC = BASE_H + 0.8 * R  # centro da bola
TOPO = ZC + 0.745 * R  # corte do topo (abertura das canetas)
INLAY = 0.8           # profundidade das cores embutidas: ficam lisas, sem relevo
MOLDURA = 6.0         # largura da moldura verde da face de apoio
BANDEJA_LARG = 76.0
BANDEJA_Z = 8.0       # piso onde o celular apoia
ABA_H = 10.0
ABA_ESP = 4.0

LOGOS = [  # arquivo, largura, angulo em volta da bola (0 = frente, 90 = lado esquerdo), altura em relacao ao centro
    dict(arquivo="../logos/rio-novo.png", largura=LOGO_LARG, azimute=100.0, dz=4.0),
    # Logo oficial da FMT: salvar em logos/fmt.png e descomentar.
    # dict(arquivo="../logos/fmt.png", largura=34.0, azimute=-100.0, dz=4.0),
]

CORES = {"branco": "#F4F4F2", "preto": "#1A1A1A", "verde": "#2E8B3C", "azul": "#0078C8"}

_a = math.radians(ANG_APOIO)
C = bd.Vector(0, 0, ZC)
N = bd.Vector(0, -math.sin(_a), math.cos(_a))      # normal da face de apoio (frente/cima)


def plano_apoio(recuo=0.0):
    return bd.Plane(origin=C + N * (D_APOIO - recuo), z_dir=N)


def esfera(r):
    return bd.Pos(*C) * bd.Sphere(r)


def acima(shape, z):
    return bd.split(shape, bd.Plane.XY.offset(z), keep=bd.Keep.TOP)


def abaixo(shape, z):
    return bd.split(shape, bd.Plane.XY.offset(z), keep=bd.Keep.BOTTOM)


def atras_da_face(shape, recuo=0.0):
    return bd.split(shape, plano_apoio(recuo), keep=bd.Keep.BOTTOM)


def casca():
    return esfera(R + 1) - esfera(R - INLAY)


# ------------------------------------------------------------------ CORPO
@memo
def envelope():
    """A bola inteira ja cortada (piso, topo, face de apoio) e oca."""
    bola = atras_da_face(abaixo(acima(esfera(R), BASE_H), TOPO))
    cavidade = atras_da_face(acima(esfera(R - PAREDE), BASE_H + PAREDE), PAREDE)
    return bola - cavidade


# ------------------------------------------------------------------ PENTAGONOS (icosaedro truncado)
def direcoes_pentagonos():
    phi = (1 + 5 ** 0.5) / 2
    vs = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            vs += [bd.Vector(0, s1, s2 * phi), bd.Vector(s1, s2 * phi, 0), bd.Vector(s2 * phi, 0, s1)]
    rot = bd.Rot(18, 31, 7)   # gira o padrao para nao cair um pentagono no meio do logo
    return [(rot * bd.Pos(*v)).position.normalized() for v in vs]


@memo
def regiao_pentagonos():
    vs = direcoes_pentagonos()
    piramides = []
    for v in vs:
        viz = [w for w in vs if 0.4 < v.dot(w) < 0.5]
        cantos = [(v + (w - v) / 3).normalized() for w in viz]
        # ordena os 5 cantos em volta do eixo v
        ref = (cantos[0] - v * cantos[0].dot(v)).normalized()
        perp = v.cross(ref)
        cantos.sort(key=lambda d: math.atan2(d.dot(perp), d.dot(ref)))
        perto = bd.Wire.make_polygon([C + d * 2 for d in cantos], close=True)
        longe = bd.Wire.make_polygon([C + d * (R * 1.3) for d in cantos], close=True)
        piramides.append(bd.Solid.make_loft([perto, longe]))
    return bd.Compound(piramides).fuse() & casca() if len(piramides) > 1 else piramides[0] & casca()


# ------------------------------------------------------------------ LOGOS (vetoriza o PNG por cor)
def limpa_mascaras(mascaras, px):
    """Imprimivel em FDM: fecha vaos menores que `px` pixels (entre letras e entre cores, que virariam
    filetes brancos finos demais), dando cada pixel preenchido a cor mais proxima, e engrossa os tracos 1 px."""
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
    mascaras = limpa_mascaras(mascaras, int(math.ceil(minimo_mm * larg / largura_mm)))
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


def face_do_logo(grupos, escala, larg, alt):
    import cv2

    def wire(c):
        c = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2)
        pts = [bd.Vector((x - larg / 2) * escala, (alt / 2 - y) * escala, 0) for x, y in c]
        return bd.Wire.make_polygon(pts, close=True) if len(pts) >= 3 else None

    faces = []
    for externo, furos in grupos:
        w = wire(externo)
        if w is None:
            continue
        faces.append(bd.Face(w, [f for f in (wire(h) for h in furos) if f is not None]))
    return faces


def plano_lateral(azimute, dz):
    az = math.radians(azimute)
    u = bd.Vector(-math.sin(az), -math.cos(az), 0)     # para fora da bola
    tx = bd.Vector(0, 0, 1).cross(u)                    # da esquerda para a direita de quem olha
    return bd.Plane(origin=C + bd.Vector(0, 0, dz), x_dir=tx, z_dir=u)


@memo
def logos():
    """Pecas de cada cor dos logos e a area branca reservada em volta deles."""
    por_cor = {"azul": [], "verde": []}
    reservas = []
    for lg in LOGOS:
        caminho = os.path.normpath(os.path.join(AQUI, lg["arquivo"]))
        larg, alt, grupos = contornos_por_cor(caminho, lg["largura"])
        esc = lg["largura"] / larg
        pl = plano_lateral(lg["azimute"], lg["dz"])
        for cor, gs in grupos.items():
            for f in face_do_logo(gs, esc, larg, alt):
                por_cor[cor].append(pl.location * bd.extrude(bd.Pos(0, 0, -2) * f, R + 4))
        ret = bd.Rectangle(lg["largura"] + 10, alt * esc + 10)
        reservas.append(pl.location * bd.extrude(ret, R + 4))
    cs = casca()
    pecas = {cor: (bd.Compound(s).fuse() & cs) if s else None for cor, s in por_cor.items()}
    return pecas, (bd.Compound(reservas).fuse() if len(reservas) > 1 else (reservas[0] if reservas else None))


# ------------------------------------------------------------------ MOLDURA, BASE E BANDEJA
def moldura(folga=0.0):
    """Anel verde de 1 mm em volta da face de apoio; `folga` o alarga para dentro e para tras."""
    camada = bd.split(bd.Pos(*C) * bd.Box(300, 300, 300), plano_apoio(1.0 + folga), keep=bd.Keep.TOP)
    r_miolo = math.sqrt(R ** 2 - D_APOIO ** 2) - MOLDURA - folga
    miolo = plano_apoio().location * bd.Cylinder(r_miolo, 40)
    return camada - miolo


def caixa(x0, x1, y0, y1, z0, z1, raio):
    b = bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)
    return bd.fillet(b.edges().filter_by(bd.Axis.Z), raio)


def y_piso_celular():
    """Onde a face de apoio encontra o piso da bandeja."""
    off = N.dot(C + N * D_APOIO)
    return (off - N.Z * BANDEJA_Z) / N.Y


def base_e_bandeja():
    y_plano = y_piso_celular()
    y_aba = y_plano - CELULAR_ESP
    base = bd.Cone(BASE_R, BASE_R - 1.0, BASE_H, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    bandeja = caixa(-BANDEJA_LARG / 2, BANDEJA_LARG / 2, y_aba - ABA_ESP, y_plano + 12, 0, BANDEJA_Z, 6)
    aba = caixa(-BANDEJA_LARG / 2, BANDEJA_LARG / 2, y_aba - ABA_ESP, y_aba, 0, BANDEJA_Z + ABA_H, 1.5)
    if VAO_CABO > 0:
        aba = aba - bd.Pos(0, y_aba - ABA_ESP / 2, BANDEJA_Z + 20) * bd.Box(VAO_CABO, ABA_ESP + 2, 40)
    # cunha entre o piso e a face: o celular nao escorrega para baixo da bola
    cunha = bd.Pos(0, y_plano + 10, (BANDEJA_Z + 14) / 2) * bd.Box(BANDEJA_LARG - 8, 30, BANDEJA_Z + 14)
    cunha = bd.split(cunha, plano_apoio(), keep=bd.Keep.BOTTOM)
    # anel de apoio em 45 graus: tira o balanco da parte de baixo da bola (dispensa suporte)
    r45, z45 = R * math.sin(math.pi / 4), ZC - R * math.cos(math.pi / 4)
    r_pe = math.sqrt(R ** 2 - (ZC - BASE_H) ** 2)
    anel = bd.Pos(0, 0, BASE_H) * bd.Cone(min(r45 + z45 - BASE_H, BASE_R - 1.0), r45, z45 - BASE_H,
                                          align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    anel = atras_da_face(anel - bd.Cylinder(r_pe - 0.5, 200))
    return base + bandeja + aba + cunha + anel


# ------------------------------------------------------------------ MONTAGEM POR COR
def _soma(*xs):
    xs = [x for x in xs if x is not None and x.volume > 1e-6]
    if not xs:
        return None
    s = xs[0]
    for x in xs[1:]:
        s = s + x
    return s


def _menos(a, *bs):
    for b in bs:
        if a is not None and b is not None:
            a = a - b
    return a


def _encosta(a, b):
    if b is None:
        return False
    x = a & b
    return x is not None and x.volume > 1e-3


def _limpa(shape, minimo=1.0):
    """Tira farelos (sobras de corte menores que `minimo` mm3)."""
    if shape is None:
        return None
    solidos = [s for s in shape.solids() if s.volume >= minimo]
    return bd.Compound(solidos) if solidos else None


@memo
def pecas_por_cor():
    env = envelope()
    pecas_logo, reserva = logos()
    verde = _soma(moldura() & env, pecas_logo["verde"] & env if pecas_logo["verde"] else None)
    azul = _menos(pecas_logo["azul"] & env if pecas_logo["azul"] else None, verde)
    # pentagono que encosta na area do logo sai inteiro (sem "dente"); os outros ficam a 1 mm da
    # moldura, para nao sobrar filete branco fino entre o preto e o verde
    pent = regiao_pentagonos() & env
    pent = _soma(*[p for p in pent.solids() if not _encosta(p, reserva)])
    preto = _menos(pent, moldura(folga=1.0) & env, verde, azul)
    branco = _menos(env, verde, azul, preto)
    verde = _soma(verde, _menos(base_e_bandeja(), env))
    return {"branco": _limpa(branco), "preto": _limpa(preto), "verde": _limpa(verde), "azul": _limpa(azul)}


@model
def bola_porta_celular():
    from bd_materials import plastics
    from bd_materials.processes import fdm

    partes = []
    for nome, shape in pecas_por_cor().items():
        if shape is None:
            continue
        shape.label = nome
        shape.material = plastics.pla(process=fdm(layer_height_mm=0.2))
        shape.color = CORES[nome]
        partes.append(shape)
    montagem = bd.Compound(children=partes)
    montagem.label = "bola_porta_celular"
    return montagem


if __name__ == "__main__":
    bola_porta_celular()
