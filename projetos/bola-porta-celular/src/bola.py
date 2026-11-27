# /// script
# dependencies = ["opencv-python-headless>=4.8", "numpy"]
# ///
"""Bola porta-celular + porta-canetas (brinde Rio Novo / FMT), no formato do mockup
(referencias/mockup-original.jpg): bola de futebol mais larga que a base, boca larga no topo,
canal na frente forrado por uma moldura verde onde o celular apoia, bandeja branca com duas
orelhas e emblema de bola, base verde baixa, logos rentes nos lados.

Pecas, cada uma de uma cor, impressas separadas (impressora de um bico, FDM, PLA), sem suporte:
  1) corpo_inferior / corpo_superior - a bola em duas metades (ressalto + canal);
  2) encosto   - moldura em U do canal do celular; a nervura de tras desce pela fenda da bola;
  3) suporte   - bandeja do celular (orelhas, vao no meio); entra no recorte da base;
  4) aro       - anel fino da boca; trava o encosto por cima;
  5) base      - disco de 120 mm; a bola assenta no rebaixo dela.
  + logos de encaixar, rentes a superficie da bola, colocados POR DENTRO da metade de cima antes
    de fechar a bola (uma plaquinha atras segura cada um): logo_rio_novo_azul (rio),
    logo_rio_novo_verde (letras), logo_fmt (escudo, lugar reservado ate chegar o arquivo da FMT);
  + emblema_bola - disco da frente da bandeja (branco, pentagono preto: troca de filamento a 2,0 mm).

Montagem: base -> metades da bola (com os logos) -> suporte no recorte da base -> encosto descendo
pela fenda ate o canal do suporte -> aro.
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
R = model.param("raio_bola", 64.0, min=45, max=75, unit="mm")
PAREDE = model.param("parede", 3.0, min=2, max=5, unit="mm")
ANG_APOIO = model.param("inclinacao_celular", 75.0, min=65, max=88, unit="deg")
D_APOIO = model.param("profundidade_canal", 32.0, min=15, max=45, unit="mm")
CANAL_LARG = model.param("largura_canal", 92.0, min=60, max=100, unit="mm")
CELULAR_ESP = model.param("encaixe_celular", 14.0, min=9, max=20, unit="mm")
LOGO_LARG = model.param("largura_logo", 60.0, min=25, max=70, unit="mm")
FOLGA = model.param("folga_encaixe", 0.2, min=0.1, max=0.4, unit="mm")

ALTURA = 110.0        # altura total (topo do aro)
BASE_R = 60.0         # raio da base (120 mm)
BASE_H = 8.0          # espessura da base; a bola assenta em cima
ZC = BASE_H + 50.0    # centro da bola
Z_TOPO = ALTURA - 6.0  # corte do topo da bola (o aro tem 6 mm)
Z_CORTE = ZC - 14.0   # divisao entre as duas metades (abaixo dos logos)
RESSALTO_H, RESSALTO_ESP = 3.0, 1.4
Z_FUNDO_CONE = ZC - 22.0
PE_R, PE_H = 36.0, 1.5             # "pe" da bola, entra no rebaixo da base
ENC_ESP = 4.0                      # espessura do fundo da moldura do celular
ABA_LAT = 3.0                      # espessura das abas laterais da moldura
NERVURA_L, NERVURA_P = 8.0, 2.5    # nervura de tras do encosto (desce pela fenda da bola)
PISO_Z = 18.0                      # piso onde o celular apoia
ORELHA_H, ORELHA_L, ABA_ESP = 12.0, 22.0, 5.0
SUP_MARGEM = 6.0                   # a bandeja passa 6 mm do canal de cada lado
ENC_Z0 = PISO_Z - 6.0              # o encosto desce 6 mm para dentro da bandeja
EMBLEMA_R, EMBLEMA_ESP = 7.0, 2.0
GOMO = 1.0           # profundidade dos gomos (rebaixo e peca preta); 1 mm = parede minima de 2 fios de 0,4
LOGO_FOLGA = 0.15                  # folga dos logos nos furos da bola
LOGO_APOIO = 1.5                   # espessura da plaquinha de tras dos logos
LOGO_AFINA = -0.08                 # mm por lado (negativo engrossa): a 60 mm o traco do desenho tem
                                   # ~1,2 mm, ja perto do minimo de FDM (bico 0,4); nao da para afinar mais
LOGO_SEPARA = 1.35                 # vao minimo entre partes do logo (letras, faixas): parede de bola >= 1 mm
LOGO_SEPARA_RIO = 1.8              # vao entre o rio e o "io" (o rio recua)

LOGOS = [
    dict(nome="rio_novo", arquivo="../logos/rio-novo.png", largura=LOGO_LARG, azimute=104.0, dz=15.0,
         cores={"azul": "#0078C8", "verde": "#2E8B3C", "faixa_verde": "#2E8B3C", "faixa_amarela": "#F2C200"},
         # faixas do mockup por baixo do logo: arcos de um circulo de centro `centro` (mm, em relacao ao
         # centro do logo), raio interno e espessura, de x0 a x1, afinando nas pontas (`ponta` mm)
         faixas=(("faixa_verde", 132.5, 3.5), ("faixa_amarela", 138.0, 3.5)),
         faixas_geo=dict(centro=(0.0, 115.0), x0=-34.0, x1=32.0, ponta=12.0)),
    # FMT: escudo liso no lugar reservado. Quando chegar o logo oficial (logos/fmt.png), trocar
    # "escudo" por arquivo= e cores= como na Rio Novo.
    dict(nome="fmt", escudo=(30.0, 36.0), azimute=-92.0, dz=8.0, cores={"escudo": "#1F4E9C"}),
]

CORES = {"corpo_inferior": "#F4F4F2", "corpo_superior": "#F4F4F2", "encosto": "#2E8B3C",
         "suporte": "#F4F4F2", "aro": "#F4F4F2", "base": "#2E8B3C",
         "gomos_inferior": "#1A1A1A", "gomos_superior": "#1A1A1A"}

_a = math.radians(ANG_APOIO)
C = bd.Vector(0, 0, ZC)
N = bd.Vector(0, -math.sin(_a), math.cos(_a))      # normal do fundo do canal (frente/cima)
CIMA = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


# ------------------------------------------------------------------ AJUDANTES
def plano_apoio(recuo=0.0):
    """Plano do fundo do canal do celular; x para a direita, y subindo pela rampa, z = N."""
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
    """Coordenada y no plano do canal da altura z."""
    return (z - (C + N * D_APOIO).Z) / math.sin(_a)


def canal(mais_lado=0.0, mais_fundo=0.0):
    """O canal do celular na frente da bola: tudo na frente do plano de apoio entre as abas.
    `mais_lado` alarga para os lados e `mais_fundo` recua o fundo (para as paredes e folgas)."""
    w = CANAL_LARG + 2 * mais_lado
    b = bd.Pos(0, 0, -mais_fundo) * bd.Box(w, 600, 300, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return plano_apoio().location * b


def boca():
    """Teto conico (45 graus) da cavidade ate a boca: (z_c, raio em z_c, raio da boca)."""
    z_c = Z_TOPO - 10.0
    r_c = r_esfera_em(R - PAREDE, z_c)
    return z_c, r_c, r_c - (Z_TOPO - z_c)


def _encosta(a, b):
    x = a & b
    return x is not None and x.volume > 1e-3


def _maior(shape):
    return sorted(shape.solids(), key=lambda s: s.volume, reverse=True)[0]


def _une(xs):
    s = xs[0]
    for x in xs[1:]:
        s = s + x
    return s


# ------------------------------------------------------------------ GOMOS (icosaedro truncado)
def direcoes_pentagonos():
    phi = (1 + 5 ** 0.5) / 2
    vs = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            vs += [bd.Vector(0, s1, s2 * phi), bd.Vector(s1, s2 * phi, 0), bd.Vector(s2 * phi, 0, s1)]
    # giro do padrao escolhido para deixar o maximo de gomos a vista, longe dos logos, do canal e da emenda
    m = ((0.065533, -0.776219, -0.627049), (0.948556, -0.146608, 0.280619), (-0.309752, -0.613181, 0.726679))
    return [bd.Vector(*(r[0] * v.X + r[1] * v.Y + r[2] * v.Z for r in m)).normalized() for v in vs]


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
def mascara_faixa(forma, px_mm, centro, r_in, esp, x0, x1, ponta):
    """Faixa em arco (por baixo do centro), afinando ate zero nas pontas, como um swoosh."""
    import numpy as np

    alt, larg = forma
    yy, xx = np.mgrid[0:alt, 0:larg]
    X = (xx - larg / 2) / px_mm
    Y = (alt / 2 - yy) / px_mm
    d = np.hypot(X - centro[0], Y - centro[1])
    t = esp * np.clip(np.minimum((X - x0) / ponta, (x1 - X) / ponta), 0.0, 1.0)
    return (d >= r_in) & (d <= r_in + t) & (Y < centro[1])


def separa_partes(mascaras, px_mm, vao):
    """Cada parte solta (cada letra, o pingo do i, o rio, cada faixa) fica a pelo menos `vao` mm das
    outras: a parede de bola entre dois furos nao fica fina e as letras nao se juntam. As partes vao da
    menor para a maior, e quem recua e a maior (o pingo do i fica inteiro; a haste encurta)."""
    import cv2
    import numpy as np

    partes = []                     # (area, cor, mascara da parte)
    for cor, m in mascaras.items():
        n, rotulos = cv2.connectedComponents(m)
        for i in range(1, n):
            p = (rotulos == i).astype(np.uint8) * 255
            partes.append((int(np.count_nonzero(p)), cor, p))
    partes.sort(key=lambda t: t[0])
    saida = {c: np.zeros_like(m) for c, m in mascaras.items()}
    ja = None
    for _, cor, m in partes:
        if ja is not None:
            m = m & ~_morf(ja, "dilata", vao, px_mm)
        saida[cor] |= m
        ja = m.copy() if ja is None else (ja | m)
    return saida


def mascaras_do_logo(caminho, largura_mm, faixas=(), faixas_geo=None):
    """Mascaras (pixels) de cada cor do logo (e das faixas), imprimiveis:
      - letras (verde) afinadas (ou engrossadas, se negativo) LOGO_AFINA mm de cada lado;
      - o rio (azul) recortado a LOGO_SEPARA_RIO mm das letras (as letras ficam inteiras);
      - toda parte solta a pelo menos LOGO_SEPARA mm das outras (nada se junta);
      - o que ficar mais fino que 0,8 mm tirado.
    Devolve (mascaras, px por mm, largura, altura em px)."""
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
    cru = {"azul": colorido & (h >= 90) & (h <= 130), "verde": colorido & (h >= 35) & (h < 90)}
    alt, larg = img.shape[:2]
    px_mm = larg / largura_mm
    # margem em volta (cabe as faixas e as dilatacoes nao batem na borda da imagem)
    pad = int((30 if faixas else 4) * px_mm)
    ms = {c: np.pad(m.astype(np.uint8) * 255, pad) for c, m in cru.items()}
    alt, larg = alt + 2 * pad, larg + 2 * pad
    ms = {c: _morf(m, "abre", 0.15, px_mm) for c, m in ms.items()}          # tira o ruido do PNG
    k = int(round(abs(LOGO_AFINA) * px_mm))
    if k:
        el = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))
        ms["verde"] = (cv2.erode if LOGO_AFINA > 0 else cv2.dilate)(ms["verde"], el)
    ms["azul"] = ms["azul"] & ~_morf(ms["verde"], "dilata", LOGO_SEPARA_RIO, px_mm)
    for nome, r_in, esp in faixas:
        g = faixas_geo
        f = mascara_faixa((alt, larg), px_mm, g["centro"], r_in, esp, g["x0"], g["x1"], g["ponta"])
        ms[nome] = f.astype(np.uint8) * 255
    ms = separa_partes(ms, px_mm, LOGO_SEPARA)
    ms = {c: _morf(m, "abre", 0.4, px_mm) for c, m in ms.items()}   # tira o mais fino que 0,8 mm
    return ms, px_mm, larg, alt


def _morf(m, op, mm, px_mm):
    """Operacao morfologica com um disco de raio `mm`: dilata, abre (tira o mais fino que 2*mm) ou
    fecha (junta o que esta a menos de 2*mm)."""
    import cv2

    r = max(1, int(round(mm * px_mm)))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    if op == "dilata":
        return cv2.dilate(m, k)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN if op == "abre" else cv2.MORPH_CLOSE, k)


def faces_da_mascara(m, escala, larg, alt):
    import cv2

    conts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    def wire(c):
        c = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2)
        pts = [bd.Vector((x - larg / 2) * escala, (alt / 2 - y) * escala, 0) for x, y in c]
        return bd.Wire.make_polygon(pts, close=True) if len(pts) >= 3 else None

    faces = []
    if hier is None:
        return faces
    for i, c in enumerate(conts):
        if hier[0][i][3] != -1 or cv2.contourArea(c) < 12:
            continue
        furos, j = [], hier[0][i][2]
        while j != -1:
            if cv2.contourArea(conts[j]) >= 6:
                furos.append(conts[j])
            j = hier[0][j][0]
        w = wire(c)
        if w is not None:
            faces.append(bd.Face(w, [f for f in (wire(h) for h in furos) if f is not None]))
    return faces


@memo
def desenho_do_logo(arquivo, largura, faixas=(), faixas_geo=None):
    """Faces 2D (no plano XY, centradas) do logo: as formas de cada cor, a plaquinha de apoio de cada
    cor e o furo na bola. Tudo feito nas mascaras (pixels), sem lascas finas:
      - plaquinha: o contorno da cor + LOGO_APOIO; numa cor de varias partes soltas (as letras), o
        retangulo delas + LOGO_APOIO (junta as letras); cada uma desvia das colunas das outras cores (0,6 mm) e das
        plaquinhas anteriores (0,3 mm), e perde o que ficar mais fino que 1,1 mm;
      - furo: a peca + LOGO_FOLGA, com os cantos estreitos fechados; a peca preenche o furo."""
    import cv2
    import numpy as np

    caminho = os.path.normpath(os.path.join(AQUI, arquivo))
    ms, px, larg, alt = mascaras_do_logo(caminho, largura, faixas, faixas_geo)
    ms = {c: m for c, m in ms.items() if m.any()}
    esc = 1.0 / px
    # pecas: nada fino demais (letras >= 1,1 mm, rio e faixas >= 1,3 mm)
    ms = {c: _morf(m, "abre", 0.55 if c == "verde" else 0.65, px) for c, m in ms.items()}
    # furo na bola: a peca + folga, fechando os cantos estreitos (< 1 mm) entre tracos, onde a bola
    # terminaria numa ponta fina. As partes estao a LOGO_SEPARA uma da outra: os furos nao se juntam.
    uniao = np.zeros_like(next(iter(ms.values())))
    for m in ms.values():
        uniao |= m
    furo = _morf(_morf(uniao, "dilata", LOGO_FOLGA, px), "fecha", 0.5, px)
    # a peca final preenche o furo (cada pixel para a cor mais proxima), menos a folga: sem vao aparente
    nomes = list(ms)
    dist = np.stack([cv2.distanceTransform(255 - ms[c], cv2.DIST_L2, 3) for c in nomes])
    mais_perto = np.argmin(dist, axis=0)
    r = max(1, int(round(LOGO_FOLGA * px)))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    # (a limpeza de novo tira os bicos finos do preenchimento; a peca limpa de antes fica inteira)
    ms = {c: _morf(cv2.erode(((furo > 0) & (mais_perto == i)).astype(np.uint8) * 255, k) | ms[c],
                   "abre", 0.55 if c == "verde" else 0.65, px)
          for i, c in enumerate(nomes)}
    apoios = {}
    for cor, m in ms.items():
        partes = cv2.connectedComponents(m)[0] - 1
        if not apoios or partes == 1:   # uma peca so: plaquinha no proprio contorno
            a = _morf(m, "dilata", LOGO_APOIO, px)
        else:
            x, y, w, h = cv2.boundingRect(m)
            a = np.zeros_like(m)
            a[y:y + h, x:x + w] = 255
            a = _morf(a, "dilata", LOGO_APOIO, px)
        for outra, mo in ms.items():
            if outra != cor:
                a = a & ~_morf(mo, "dilata", 0.6, px)
        for ap in apoios.values():
            a = a & ~_morf(ap, "dilata", 0.3, px)
        apoios[cor] = _morf(a, "abre", 0.55, px) | m   # sem tiras finas (< 1,1 mm)
    return {
        "formas": {c: faces_da_mascara(m, esc, larg, alt) for c, m in ms.items()},
        "apoios": {c: faces_da_mascara(a, esc, larg, alt) for c, a in apoios.items()},
        "furo": faces_da_mascara(furo, esc, larg, alt),
    }


def escudo(w, h):
    pts = [(-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 8), (0, -h / 2), (-w / 2, -h / 8)]
    f = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in pts], close=True))
    return bd.fillet(f.vertices(), 3.0)


# ------------------------------------------------------------------ LOGOS DE ENCAIXAR
# Cada logo e montado no plano lateral dele (z local = para fora da bola). A parede da bola tem um
# reforco por dentro com face plana a d_in do centro; as formas do logo atravessam a parede (furos) e
# as pecas do logo sao: colunas com o topo rente a esfera + uma plaquinha de apoio por tras.
def plano_lateral(azimute, dz):
    az = math.radians(azimute)
    u = bd.Vector(-math.sin(az), -math.cos(az), 0)     # para fora da bola
    tx = bd.Vector(0, 0, 1).cross(u)                    # da esquerda para a direita de quem olha
    return bd.Plane(origin=C + bd.Vector(0, 0, dz), x_dir=tx, z_dir=u)


def camadas_do_logo(lg):
    """{"formas": {cor: faces}, "apoios": {cor: faces}, "furo": faces} no plano do logo."""
    if "escudo" in lg:
        e = escudo(*lg["escudo"])
        return {"formas": {"escudo": [e]}, "apoios": {"escudo": [bd.offset(e, LOGO_APOIO)]},
                "furo": [bd.offset(e, LOGO_FOLGA)]}
    return desenho_do_logo(lg["arquivo"], lg["largura"], lg.get("faixas", ()), lg.get("faixas_geo"))


def caixa_2d(faces, mais=0.0):
    bb = bd.Compound(faces).bounding_box()
    return (bd.Pos(bb.center().X, bb.center().Y) *
            bd.RectangleRounded(bb.size.X + 2 * mais, bb.size.Y + 2 * mais, 2.0 + mais))


def _ext(face_ou_sketch, z0, z1):
    # direcao fixa (+z): a normal de uma face depende do sentido do contorno
    return bd.extrude(bd.Pos(0, 0, z0) * face_ou_sketch, z1 - z0, dir=(0, 0, 1))


@memo
def geometria_logo(i):
    """(pecas locais por cor, furos locais, reforco local, area a evitar local, d_in)."""
    lg = LOGOS[i]
    camadas = camadas_do_logo(lg)
    formas = camadas["formas"]
    todas = [f for fs in formas.values() for f in fs]
    bb = bd.Compound(todas).bounding_box()
    # canto mais longe do centro da bola (o desenho pode nao estar centrado: as faixas ficam embaixo)
    x2 = max(bb.min.X ** 2, bb.max.X ** 2) + 8 * max(abs(bb.min.X), abs(bb.max.X)) + 16
    y2 = max((bb.min.Y + lg["dz"] - 4) ** 2, (bb.max.Y + lg["dz"] + 4) ** 2)
    d_in = math.sqrt(R ** 2 - x2 - y2) - 4.0
    esf = bd.Pos(0, -lg["dz"], 0) * bd.Sphere(R)       # a esfera da bola, no plano do logo
    pecas = {}
    for cor, fs in formas.items():
        apoio = _une([_ext(a, d_in - LOGO_APOIO, d_in) for a in camadas["apoios"][cor]])
        colunas = _une([_ext(f, d_in - LOGO_APOIO, R + 2) for f in fs]) & esf
        pecas[cor] = apoio + colunas
    furos = _une([_ext(f, d_in - 0.5, R + 5) for f in camadas["furo"]])
    reforco = bd.extrude(bd.Pos(0, 0, d_in) * caixa_2d(todas, LOGO_APOIO + 2.5), R - d_in, taper=-44)
    evitar = _ext(caixa_2d(todas, 6.0), 0, R + 5)
    return pecas, furos, reforco, evitar, d_in


def no_lugar(i, shape_local):
    lg = LOGOS[i]
    return plano_lateral(lg["azimute"], lg["dz"]).location * shape_local


def logo_peca(i, cor):
    lg = LOGOS[i]
    s = no_lugar(i, geometria_logo(i)[0][cor])
    s.label = f"logo_{lg['nome']}_{cor}" if cor != "escudo" else f"logo_{lg['nome']}"
    s.color = lg["cores"][cor]
    return s


@model
def logo_rio_novo_azul():
    return logo_peca(0, "azul")


@model
def logo_rio_novo_verde():
    return logo_peca(0, "verde")


@model
def logo_rio_novo_faixa_verde():
    return logo_peca(0, "faixa_verde")


@model
def logo_rio_novo_faixa_amarela():
    return logo_peca(0, "faixa_amarela")


@model
def logo_fmt():
    return logo_peca(1, "escudo")


# ------------------------------------------------------------------ ENCOSTO (moldura em U)
def forma_encosto_local(folga=0.0):
    """No plano do canal: fundo de z = 0 a ENC_ESP, abas laterais encostadas nas paredes do canal,
    nervura atras (z < 0). Extrudado ao longo da rampa (y), cortado pela esfera e pelo topo."""
    f = folga
    w = CANAL_LARG / 2 + f
    y0, y1 = y_local(ENC_Z0) - f, y_local(Z_TOPO) + 30
    fundo = bd.Pos(0, 0, -f) * bd.Rectangle(2 * w, ENC_ESP + 2 * f, align=(bd.Align.CENTER, bd.Align.MIN))
    abas = [bd.Pos(s * (w - (ABA_LAT + 2 * f) / 2), -f) *
            bd.Rectangle(ABA_LAT + 2 * f, 80, align=(bd.Align.CENTER, bd.Align.MIN)) for s in (-1, 1)]
    nervura = bd.Pos(0, f) * bd.Rectangle(NERVURA_L + 2 * f, NERVURA_P + 2 * f, align=(bd.Align.CENTER, bd.Align.MAX))
    def ao_longo(perfil):                                 # perfil no XY (y = z local) -> de y0 a y1
        return bd.Pos(0, y1, 0) * (bd.Plane.XZ.location * bd.extrude(perfil, y1 - y0))

    esf = bd.Pos(0, 0, -D_APOIO) * bd.Sphere(R + f)       # a esfera da bola, no plano do canal
    abas_3d = ao_longo(abas[0] + abas[1]) & esf           # as abas acompanham a superficie da bola
    corpo = ao_longo(fundo + nervura) + abas_3d
    topo = bd.Plane(origin=(0, (Z_TOPO + f - (C + N * D_APOIO).Z) / math.sin(_a), 0),
                    z_dir=(0, math.sin(_a), math.cos(_a)))
    return bd.split(corpo, topo, keep=bd.Keep.BOTTOM)


def forma_encosto(folga=0.0):
    return plano_apoio().location * forma_encosto_local(folga)


def fenda_nervura():
    """A fenda da bola por onde a nervura desce (aberta no topo)."""
    f = FOLGA
    b = bd.Box(NERVURA_L + 2 * f, 600, NERVURA_P + 2 * f, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
    b = bd.Pos(0, 300 + y_local(ENC_Z0) - 1, 0.01) * b
    return plano_apoio().location * b


@model
def encosto():
    """2) Moldura verde em U do canal do celular."""
    e = forma_encosto()
    e.label = "encosto"
    return e


# ------------------------------------------------------------------ CORPO
def cavidade():
    z_c, r_c, r_top = boca()
    teto = cone(r_c, r_top - 1.0, z_c, Z_TOPO + 1)
    z_f = BASE_H + PAREDE
    r_b = r_esfera_em(R - PAREDE, Z_FUNDO_CONE)
    r_v = r_b - (Z_FUNDO_CONE - z_f)
    # fundo em "V": parede a 45 graus por fora e um cone (45 graus) no meio; nenhum teto plano
    # quando a metade de baixo imprime de boca para baixo; as canetas apoiam no anel do V
    fundo = cone(r_v, r_b, z_f, Z_FUNDO_CONE + 0.01)
    meio = abaixo(acima(esfera(R - PAREDE), Z_FUNDO_CONE), z_c)
    centro = cone(r_v, 0.0, z_f - 0.01, z_f + r_v)       # o cone do meio inteiro, com ponta
    return fundo + meio + teto - centro - canal(PAREDE, PAREDE + NERVURA_P)


def oco_do_pe():
    """Por baixo do cone do meio a bola e oca (cone aberto para baixo): menos plastico."""
    z_f = BASE_H + PAREDE
    r_b = r_esfera_em(R - PAREDE, Z_FUNDO_CONE)
    r_v = r_b - (Z_FUNDO_CONE - z_f)
    z_a = z_f + r_v - PAREDE * math.sqrt(2)
    z_0 = BASE_H - PE_H - 0.01
    return cone(z_a - z_0, 0.0, z_0, z_a)


def ressalto(folga=0.0):
    """Anel que desce da metade de cima e entra na de baixo."""
    r0 = r_esfera_em(R - PAREDE, Z_CORTE) - 0.6
    a = anel(r0 - (3.0 if folga else 0.0), r0 + RESSALTO_ESP + folga, Z_CORTE - RESSALTO_H - folga,
             Z_CORTE + (1.0 if folga else 0.0))
    return a - canal(PAREDE + 1.0 - folga, PAREDE + NERVURA_P + 1.0 - folga)


def _evitar_gomos():
    """Onde nao vai gomo: em volta dos logos e na emenda das metades (o encaixe por dentro deixaria
    a parede fina demais atras do gomo)."""
    evitar = [no_lugar(i, geometria_logo(i)[3]) for i in range(len(LOGOS))]
    evitar.append(cilindro(R + 2, Z_CORTE - RESSALTO_H - 1.5, Z_CORTE + 1.5))
    return evitar


@memo
def corpo_inteiro():
    """A bola inteira, com canal, cavidade, logos, gomos e fenda (antes de dividir)."""
    bola = abaixo(acima(esfera(R), BASE_H), Z_TOPO) - canal(FOLGA)
    bola = bola - cavidade()
    for i in range(len(LOGOS)):
        bola = bola + acima(no_lugar(i, geometria_logo(i)[2]) & esfera(R - 0.5), Z_CORTE) - canal(FOLGA)
    bola = bola + cilindro(PE_R, BASE_H - PE_H, BASE_H + 0.5) - oco_do_pe()
    gomos = pentagonos(_evitar_gomos())
    if gomos:
        bola = bola - bd.Compound(gomos)
    for i in range(len(LOGOS)):
        bola = bola - no_lugar(i, geometria_logo(i)[1])
    return bola - fenda_nervura()


@model
def corpo_inferior():
    """1a) Metade de baixo da bola."""
    c = _maior(abaixo(corpo_inteiro(), Z_CORTE) - ressalto(FOLGA))
    c.label = "corpo_inferior"
    return c


@model
def corpo_superior():
    """1b) Metade de cima, com o ressalto de encaixe e os furos dos logos."""
    c = _maior(acima(corpo_inteiro(), Z_CORTE) + ressalto())
    c.label = "corpo_superior"
    return c


# ------------------------------------------------------------------ GOMOS PRETOS
@memo
def gomos_na_bola():
    """Os pentagonos pretos que preenchem os rebaixos dos gomos, rentes a superficie da bola.
    Impressao: junto com a metade da bola, em multicor (AMS), ou pintar o rebaixo e dispensar."""
    gomos = pentagonos(_evitar_gomos())
    fora = abaixo(acima(esfera(R), BASE_H), Z_TOPO) - canal(FOLGA) - fenda_nervura()
    return bd.Compound(gomos) & fora


def _gomos(metade, nome):
    g = metade(gomos_na_bola(), Z_CORTE)
    solidos = [x for x in g.solids() if x.volume > 1.0]
    c = bd.Compound(solidos)
    c.label = nome
    c.color = CORES[nome]
    return c


@model
def gomos_inferior():
    """Gomos pretos da metade de baixo."""
    return _gomos(abaixo, "gomos_inferior")


@model
def gomos_superior():
    """Gomos pretos da metade de cima."""
    return _gomos(acima, "gomos_superior")


# ------------------------------------------------------------------ SUPORTE (bandeja)
def envoltoria_bola(f):
    """O volume da bola por fora (sem a cavidade), alargado de `f`."""
    return acima(esfera(R + f), BASE_H - PE_H - f) - canal(-f, -f)


def medidas_suporte():
    p = plano_apoio()
    frente = (p.location * bd.Pos(0, y_local(PISO_Z), ENC_ESP)).position.Y
    y_aba = frente - CELULAR_ESP
    return y_aba, y_aba - ABA_ESP


def forma_suporte(folga=0.0):
    """Planta da bandeja (bloco cheio, antes dos recortes); tambem e o recorte da base."""
    y_aba, y_frente = medidas_suporte()
    w = CANAL_LARG / 2 + SUP_MARGEM + folga
    y_tras = (plano_apoio().location * bd.Pos(0, y_local(BASE_H), 0)).position.Y + 12.0
    bloco = caixa(-w, w, y_frente - folga, y_tras, 0, PISO_Z, 8.0)
    return bd.split(bloco, plano_apoio(5.0 + folga), keep=bd.Keep.TOP)


def emblema_plano():
    _, y_frente = medidas_suporte()
    return bd.Plane(origin=(0, y_frente, PISO_Z / 2), x_dir=(1, 0, 0), z_dir=(0, -1, 0))


@model
def suporte():
    """3) Bandeja do celular: piso, duas orelhas na frente com vao no meio, canal do encosto,
    rebaixo do emblema na frente."""
    y_aba, y_frente = medidas_suporte()
    w = CANAL_LARG / 2 + SUP_MARGEM
    orelhas = [caixa(s * w - (ORELHA_L if s > 0 else 0), s * w + (ORELHA_L if s < 0 else 0),
                     y_frente, y_aba, 0, PISO_Z + ORELHA_H, 2.0) for s in (-1, 1)]
    s = forma_suporte() + orelhas[0] + orelhas[1]
    s = s - envoltoria_bola(FOLGA) - forma_encosto(FOLGA)
    s = s - emblema_plano().location * bd.Cylinder(EMBLEMA_R + FOLGA, 2 * EMBLEMA_ESP)
    s = _maior(s)
    s.label = "suporte"
    return s


def emblema_local():
    disco = bd.Pos(0, 0, -EMBLEMA_ESP) * bd.Cylinder(EMBLEMA_R, EMBLEMA_ESP, align=CIMA)
    pent = bd.RegularPolygon(3.4, 5)
    return disco, bd.extrude(pent, 0.8)


@model
def emblema_bola():
    """Disco de bola da frente da bandeja: branco com pentagono preto em relevo."""
    disco, pent = emblema_local()
    loc = emblema_plano().location
    d, p = loc * disco, loc * pent
    d.label, d.color = "disco", "#F4F4F2"
    p.label, p.color = "pentagono", "#1A1A1A"
    c = bd.Compound(children=[d, p])
    c.label = "emblema_bola"
    return c


# ------------------------------------------------------------------ ARO E BASE
@model
def aro():
    """4) Anel fino da boca, com espiga conica; interrompido no canal; trava o encosto."""
    _, _, r_boca = boca()
    r_int = r_boca - FOLGA - 2.6
    r_ext = r_esfera_em(R, Z_TOPO) + 1.0
    a = cilindro(r_ext, Z_TOPO, ALTURA) - cilindro(r_int, Z_TOPO - 1, ALTURA + 1)
    a = bd.fillet(a.edges().filter_by(bd.GeomType.CIRCLE).sort_by(bd.Axis.Z)[-2:], 2.0)
    f = FOLGA * 1.42
    espiga = cone(r_boca + 5.0 - f, r_boca - f, Z_TOPO - 5.0, Z_TOPO) + cilindro(r_boca - f, Z_TOPO - 0.01, Z_TOPO + 0.5)
    espiga = espiga - cilindro(r_int, Z_TOPO - 6, Z_TOPO + 1) - canal(PAREDE + FOLGA, PAREDE + NERVURA_P + FOLGA)
    a = _maior(a - canal(FOLGA, 0.0) + espiga)
    a.label = "aro"
    return a


@model
def base():
    """5) Disco verde de 120 mm; rebaixo do pe da bola e recorte da bandeja."""
    b = cilindro(BASE_R, 0, BASE_H)
    b = bd.fillet(b.edges().filter_by(bd.GeomType.CIRCLE).sort_by(bd.Axis.Z)[-1], 3.0)
    b = b - cilindro(PE_R + FOLGA, BASE_H - PE_H - FOLGA, BASE_H + 1)
    b = _maior(b - forma_suporte(FOLGA))
    b.label = "base"
    return b


PECAS = [("corpo_inferior", corpo_inferior), ("corpo_superior", corpo_superior),
         ("gomos_inferior", gomos_inferior), ("gomos_superior", gomos_superior), ("encosto", encosto),
         ("suporte", suporte), ("aro", aro), ("base", base),
         ("logo_rio_novo_azul", logo_rio_novo_azul), ("logo_rio_novo_verde", logo_rio_novo_verde),
         ("logo_rio_novo_faixa_verde", logo_rio_novo_faixa_verde),
         ("logo_rio_novo_faixa_amarela", logo_rio_novo_faixa_amarela),
         ("logo_fmt", logo_fmt)]


# ------------------------------------------------------------------ MONTAGEM
@model
def bola_5_pecas():
    from bd_materials import plastics
    from bd_materials.processes import fdm

    pla = plastics.pla(process=fdm(layer_height_mm=0.2))
    partes = []
    for nome, m in PECAS:
        s = m().shape
        cor = s.color
        s.label = nome
        s.material = pla            # o material antes da cor: atribuir o material troca a cor
        s.color = CORES.get(nome, cor)
        partes.append(s)
    em = emblema_bola().shape
    for filho in em.children:
        cor = filho.color
        filho.material = pla
        filho.color = cor
    partes.append(em)
    montagem = bd.Compound(children=partes)
    montagem.label = "bola_5_pecas"
    bb = montagem.bounding_box()
    assert abs(bb.max.Z - ALTURA) < 0.5, bb.max.Z
    return montagem


if __name__ == "__main__":
    bola_5_pecas()
