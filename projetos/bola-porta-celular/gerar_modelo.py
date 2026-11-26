# Bola porta-celular + porta-canetas (brinde Rio Novo) -- gerador do modelo 3D.
#
# Gera um STL por cor (para impressao multicor: AMS / MMU) e um 3MF com todas as partes juntas.
# Rodar:  python3 gerar_modelo.py
# Precisa: pip install manifold3d trimesh numpy opencv-python-headless shapely lxml networkx
#
# Todas as medidas em milimetros. Eixo Z para cima; a FRENTE da peca (onde fica o celular) e -Y.
import json, math, os
import numpy as np
import cv2
import trimesh
from manifold3d import Manifold, CrossSection, FillRule, OpType

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "saida")
os.makedirs(SAIDA, exist_ok=True)

# ------------------------------------------------------------------ PARAMETROS (ajuste aqui)
R = 55.0            # raio da bola (110 mm de diametro)
PAREDE = 3.0        # espessura da parede
BASE_H = 5.0        # altura da base verde redonda
BASE_R = 44.0       # raio da base verde
ZC = BASE_H + 44.0  # altura do centro da bola (a bola e cortada embaixo, onde encosta na base)
TOPO = ZC + 41.0    # altura do corte do topo (abertura das canetas)
ANG_APOIO = 78.0    # inclinacao do celular em graus (90 = em pe, 70 = bem deitado)
D_APOIO = 24.0      # quanto a face plana de apoio "entra" na bola (maior = face maior)
INLAY = 0.8         # profundidade das cores embutidas (pentagonos e logos) - ficam lisas
CELULAR_ESP = 14.0  # largura do encaixe do celular (celular + capinha)
BANDEJA_LARG = 76.0 # largura da bandeja da frente
BANDEJA_Z = 8.0     # altura do piso onde o celular apoia
ABA_H = 10.0        # altura da aba que segura o celular
ABA_ESP = 4.0       # espessura da aba
VAO_CABO = 24.0     # vao no meio da aba (cabo do carregador / som)
LOGOS = [           # logo, largura (mm), angulo em volta da bola (0 = frente, 90 = lado esquerdo), altura relativa ao centro
    dict(arquivo="logos/rio-novo.png", largura=50.0, azimute=100.0, dz=4.0),
    # Quando chegar o logo oficial da FMT, salve em logos/fmt.png e descomente:
    # dict(arquivo="logos/fmt.png", largura=34.0, azimute=-100.0, dz=4.0),
]
SEG = 160           # resolucao das curvas
# ------------------------------------------------------------------

C = np.array([0.0, 0.0, ZC])
a = math.radians(ANG_APOIO)
N = np.array([0.0, -math.sin(a), math.cos(a)])   # normal da face de apoio (aponta para a frente/cima)
OFF_APOIO = D_APOIO + float(N @ C)               # plano: N.p = OFF_APOIO


def esfera(r):
    return Manifold.sphere(r, SEG).translate(C.tolist())


def corta(m, normal, off, manter_lado_positivo=True):
    """Mantem N.p >= off (ou <= off)."""
    if manter_lado_positivo:
        return m.trim_by_plane(list(map(float, normal)), float(off))
    return m.trim_by_plane([-float(x) for x in normal], -float(off))


def caixa_arredondada(x0, x1, y0, y1, z0, z1, r):
    pts = [(x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)]
    cil = [Manifold.cylinder(z1 - z0, r, r, 48).translate([px, py, z0]) for px, py in pts]
    return Manifold.batch_hull(cil)


# ------------------------------------------------------------------ CORPO (bola branca)
bola = esfera(R)
bola = corta(bola, [0, 0, 1], BASE_H)            # piso
bola = corta(bola, [0, 0, 1], TOPO, False)       # abertura do topo
bola = corta(bola, N, OFF_APOIO, False)          # face plana de apoio do celular

cavidade = esfera(R - PAREDE)
cavidade = corta(cavidade, [0, 0, 1], BASE_H + PAREDE)
cavidade = corta(cavidade, N, OFF_APOIO - PAREDE, False)
envelope = bola - cavidade

# ------------------------------------------------------------------ PENTAGONOS (bola de futebol)
phi = (1 + 5 ** 0.5) / 2
ico = []
for s1 in (-1, 1):
    for s2 in (-1, 1):
        ico += [(0, s1, s2 * phi), (s1, s2 * phi, 0), (s2 * phi, 0, s1)]
ico = np.array(ico, float)
ico /= np.linalg.norm(ico, axis=1)[:, None]
# gira o padrao para nao ficar um pentagono bem no meio dos logos
rot = trimesh.transformations.euler_matrix(math.radians(18), math.radians(31), math.radians(7))[:3, :3]
ico = ico @ rot.T

casca = esfera(R + 1) - esfera(R - INLAY)
pentagonos = []
for v in ico:
    viz = [w for w in ico if 0.4 < v @ w < 0.5]             # os 5 vizinhos no icosaedro
    pts = [C.tolist()]
    for w in viz:
        d = v + (w - v) / 3.0                                 # vertice do icosaedro truncado
        d /= np.linalg.norm(d)
        pts.append((C + d * (R * 1.25)).tolist())             # longe o bastante p/ o meio do pentagono passar da superficie
    pentagonos.append(Manifold.hull_points(pts))
pent = Manifold.batch_boolean(pentagonos, OpType.Add) ^ casca


# ------------------------------------------------------------------ LOGOS (vetoriza o PNG por cor)
def cores_do_logo(caminho):
    img = cv2.imread(os.path.join(AQUI, caminho), cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4:  # transparente -> fundo branco
        alfa = img[:, :, 3:4] / 255.0
        img = (img[:, :, :3] * alfa + 255 * (1 - alfa)).astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    colorido = (s > 70) & (v > 50)
    mascaras = {
        "azul": colorido & (h >= 90) & (h <= 130),
        "verde": colorido & (h >= 35) & (h < 90),
    }
    return img.shape[1], img.shape[0], mascaras


def secao(mascara, escala, w, hpx):
    m = (mascara.astype(np.uint8) * 255)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    conts, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    for c in conts:
        if cv2.contourArea(c) < 12:
            continue
        c = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2).astype(float)
        if len(c) < 3:
            continue
        pts = [((x - w / 2) * escala, (hpx / 2 - y) * escala) for x, y in c]
        polys.append(pts)
    return CrossSection(polys, FillRule.EvenOdd) if polys else None


def coloca_no_lado(sec, azimute, dz):
    """Projeta a figura 2D na superficie da bola, olhando de fora para dentro."""
    sol = sec.extrude(R + 4).translate([0, 0, -2])         # ao longo de +Z, do centro para fora
    az = math.radians(azimute)
    u = np.array([-math.sin(az), -math.cos(az), 0.0])      # direcao para fora (0 = frente -Y)
    up = np.array([0.0, 0.0, 1.0])
    tx = np.cross(up, u)                                   # eixo X do logo (da esquerda p/ direita de quem olha)
    M = np.zeros((3, 4))
    M[:, 0], M[:, 1], M[:, 2] = tx, up, u
    M[:, 3] = C + np.array([0, 0, dz])
    return sol.transform(M.tolist())


cores = {"preto": pent, "verde": Manifold(), "azul": Manifold()}
reserva_logos = Manifold()
for lg in LOGOS:
    if not os.path.exists(os.path.join(AQUI, lg["arquivo"])):
        print("AVISO: logo nao encontrado:", lg["arquivo"])
        continue
    w, hpx, masc = cores_do_logo(lg["arquivo"])
    esc = lg["largura"] / w
    for cor, mk in masc.items():
        sc = secao(mk, esc, w, hpx)
        if sc is not None:
            cores[cor] = cores[cor] + (coloca_no_lado(sc, lg["azimute"], lg["dz"]) ^ casca)
    # area branca em volta do logo (tira os pentagonos dali)
    margem = 5.0
    ret = CrossSection.square([lg["largura"] + 2 * margem, hpx * esc + 2 * margem], True)
    reserva_logos = reserva_logos + coloca_no_lado(ret, lg["azimute"], lg["dz"])

cores["preto"] = cores["preto"] - reserva_logos

# moldura verde em volta da face de apoio do celular (camada de 1 mm, centro fica branco)
MOLDURA = 6.0
face = corta(Manifold.cube([300, 300, 300], True).translate(C.tolist()), N, OFF_APOIO - 1.0)
r_face = math.sqrt(R ** 2 - D_APOIO ** 2) - MOLDURA
miolo = Manifold.cylinder(40, r_face, r_face, SEG, True)
eixo_z, alvo = np.array([0, 0, 1.0]), N
ang = math.degrees(math.acos(float(eixo_z @ alvo)))
miolo = miolo.rotate([ang, 0, 0]).translate((C + N * D_APOIO).tolist())   # gira o cilindro ate o eixo ficar na normal da face
cores["verde"] = cores["verde"] + (face - miolo)

# recorta tudo pela forma final da bola e define prioridade (verde > azul > preto > branco)
cores = {k: v ^ envelope for k, v in cores.items()}
cores["azul"] = cores["azul"] - cores["verde"]
cores["preto"] = cores["preto"] - cores["verde"] - cores["azul"]
branco = envelope - cores["verde"] - cores["azul"] - cores["preto"]

# ------------------------------------------------------------------ BASE + BANDEJA (verde)
y_plano = (OFF_APOIO - N[2] * BANDEJA_Z) / N[1]                 # onde a face encontra o piso do celular
y_aba = y_plano - CELULAR_ESP
base = Manifold.cylinder(BASE_H, BASE_R, BASE_R - 1.0, SEG)
bandeja = caixa_arredondada(-BANDEJA_LARG / 2, BANDEJA_LARG / 2, y_aba - ABA_ESP, y_plano + 12, 0, BANDEJA_Z, 6)
aba = caixa_arredondada(-BANDEJA_LARG / 2, BANDEJA_LARG / 2, y_aba - ABA_ESP, y_aba, 0, BANDEJA_Z + ABA_H, 2)
aba = aba - Manifold.cube([VAO_CABO, 40, 40], True).translate([0, y_aba, BANDEJA_Z + 20])
# encosto entre o piso e a face (o celular nao escorrega para dentro da bola)
encosto = corta(Manifold.cube([BANDEJA_LARG - 8, 30, 30], True).translate([0, y_plano + 10, BANDEJA_Z + 10]), N, OFF_APOIO, False)
encosto = encosto ^ Manifold.cube([BANDEJA_LARG - 8, 60, BANDEJA_Z + 14], True).translate([0, y_plano, (BANDEJA_Z + 14) / 2])
verde_base = (base + bandeja + aba + encosto) - (envelope - cores["verde"])
cores["verde"] = cores["verde"] + verde_base
cores["branco"] = branco


def sem_farelos(m, minimo=1.0):
    """Remove pedacinhos soltos menores que `minimo` mm3 (sobras de corte que atrapalham o fatiador)."""
    partes = [p for p in m.decompose() if p.volume() >= minimo]
    return Manifold.compose(partes) if partes else Manifold()

cores = {k: sem_farelos(v) for k, v in cores.items()}


# ------------------------------------------------------------------ EXPORTA
def para_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=True)

CORES_RGB = {"branco": [245, 245, 245, 255], "preto": [25, 25, 25, 255], "verde": [40, 140, 60, 255], "azul": [0, 120, 200, 255]}
cena = trimesh.Scene()
info = {}
for nome in ["branco", "preto", "verde", "azul"]:
    m = cores[nome]
    if m.is_empty():
        continue
    tm = para_trimesh(m)
    tm.visual.face_colors = CORES_RGB[nome]
    tm.export(os.path.join(SAIDA, f"bola-{nome}.stl"))
    cena.add_geometry(tm, node_name=nome, geom_name=nome)
    info[nome] = dict(volume_cm3=round(m.volume() / 1000, 1), estanque=bool(tm.is_watertight),
                      gramas_PLA_se_macico=round(m.volume() / 1000 * 1.24, 1))
cena.export(os.path.join(SAIDA, "bola-porta-celular.3mf"))
tudo = sum((cores[k] for k in cores), Manifold())
bb = tudo.bounding_box()
info["medidas_mm"] = dict(largura=round(bb[3] - bb[0], 1), profundidade=round(bb[4] - bb[1], 1), altura=round(bb[5] - bb[2], 1))
info["piso_do_celular_y"] = round(y_plano, 1)
json.dump(info, open(os.path.join(SAIDA, "resumo.json"), "w"), indent=2, ensure_ascii=False)
print(json.dumps(info, indent=2, ensure_ascii=False))
