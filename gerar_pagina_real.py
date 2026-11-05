# Gera index.html (pagina REAL de Presentes 3D) a partir da pagina de teste, trocando os dados fixos pela leitura da API.
# Rode uma vez; depois edite o index.html diretamente.
import os, re, shutil, json
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(AQUI), "giftforma-site")
src = open(os.path.join(SITE, "presentes-teste.src.html"), encoding="utf-8").read().replace("\r\n", "\n")
log = {}


def regex(nome, pad, novo, flags=re.S):
    global src
    m = re.search(pad, src, flags)
    log[nome] = bool(m)
    if m:
        src = src[:m.start()] + novo + src[m.end():]


def troca(nome, de, para):
    global src
    log[nome] = de in src
    src = src.replace(de, para, 1)


# ---------- cabecalho da pagina (indexavel, com compartilhamento) ----------
regex("titulo", r'<title>.*?</title>\n<meta name="robots" content="noindex">',
      '<title>Presentes de Natal em 3D | GiftForma</title>\n'
      '<meta name="description" content="Presentes de Natal impressos em 3D: monte seu kit de 5, 7 ou 9 peças e personalize com nome e dedicatória. Papai Noel, rena, pinguim, árvore e mais. Enviamos para todo o Brasil.">\n'
      '<link rel="canonical" href="https://presentes.giftforma.com.br/">\n'
      '<meta property="og:type" content="website"><meta property="og:url" content="https://presentes.giftforma.com.br/">\n'
      '<meta property="og:title" content="Presentes de Natal em 3D | GiftForma">\n'
      '<meta property="og:description" content="Monte seu kit de Natal com 5, 7 ou 9 peças e personalize com nome e dedicatória.">\n'
      '<meta property="og:image" content="https://presentes.giftforma.com.br/assets/og-natal.jpg">\n'
      '<link rel="icon" type="image/png" href="assets/favicon.png">')
regex("faixa_teste", r'<div class="teste">.*?</div>\n', '')
regex("bastidores", r'<section class="bast".*?</section>\n', '')
troca("vazio", "Nenhum presente de Natal nesta área ainda. Escolha o destino dos produtos no painel (veja “Bastidores” abaixo).",
      "Os presentes de Natal estão chegando. Fale com a gente pelo WhatsApp que avisamos assim que estiverem prontos.")
troca("rodape", "<span>GiftForma · Natal em impressão 3D</span>",
      '<span>GiftForma · Natal em impressão 3D · <a href="https://giftforma.com.br">Brindes para empresas</a></span>')

# ---------- dados: vem da API, nada fixo na pagina ----------
novo_dados = r"""  var ZAP_NUM=ZAP;
  var API_PADRAO='https://giftforma-api.onrender.com';
  var API=(/^(localhost|127\.0\.0\.1)$/.test(location.hostname)&&new URLSearchParams(location.search).get('api'))||API_PADRAO;
  var IMG={}, IMGG={}, P=[];
  var GRUPOS={personagens:'Personagens',decoracao:'Decoração',base:'Bandeja',outros:'Mais presentes'};
  var GRUPO_POR_PECA={'papai-noel':'personagens','boneco-de-neve':'personagens','rena':'personagens','pinguim':'personagens','boneco-de-gengibre':'personagens','urso-polar':'personagens','arvore-de-natal':'decoracao','placa-feliz-natal':'decoracao','bandeja':'base'};
  var DESTAQUE='';
  var $=function(id){return document.getElementById(id);};
  var pad=function(n){return (n<10?'0':'')+n;};
  var fmt=function(d){return pad(d.getDate())+'/'+pad(d.getMonth()+1)+'/'+d.getFullYear();};
  var brl=function(v){v=Number(v);return Number.isInteger(v)?String(v):v.toFixed(2).replace('.',',');};
  var slugar=function(t){return String(t||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');};
  var grupoAtivo='todos', kit={};
  var noPresentes=function(p){return !!p;};
  var porSlug=function(s){return P.filter(function(p){return p.slug===s;})[0];};
"""
regex("dados", r"  var IMG=/\*IMGS\*/\{\};.*?var porSlug=function\(s\)\{return P\.filter\(function\(p\)\{return p\.slug===s;\}\)\[0\];\};\n", novo_dados)
regex("tiers_vazio", r"var TIERS=\[\{n:5.*?\}\];", "var TIERS=[];")
regex("renderAdmin_chamada", r"\n    renderAdmin\(\);", "")
regex("renderAdmin_funcao", r"  // ---------- bastidores ----------.*?(?=  // ---------- kit:)", "")

# ---------- tamanhos de kit vindos do painel (pode nao haver nenhum) ----------
regex("ajustaAlvo", r"  function ajustaAlvo\(\)\{.*?\n",
      "  function ajustaAlvo(){ var n=nKit(); if(!TIERS.length){alvo=Math.max(5,n);return;} for(var i=0;i<TIERS.length;i++){ if(TIERS[i].n>=alvo&&TIERS[i].n>=n){alvo=TIERS[i].n;return;} } alvo=TIERS[TIERS.length-1].n; }\n")
troca("renderTiers", "  function renderTiers(){\n", "  function renderTiers(){\n    $('tiers').hidden=!TIERS.length; $('tiers').previousElementSibling.hidden=!TIERS.length;\n")
troca("kpTit", "$('kpTit').textContent='Kit com '+alvo+' peças'; $('kpCont').textContent=n+' de '+alvo+' peças selecionadas';",
      "$('kpTit').textContent=TIERS.length?'Kit com '+alvo+' peças':'Seus presentes'; $('kpCont').textContent=TIERS.length?n+' de '+alvo+' peças selecionadas':n+(n===1?' peça selecionada':' peças selecionadas');")
troca("kpTotal", "$('kpTotal').textContent='R$ '+brl(n===0?tA.preco:vk.total);",
      "$('kpTotal').textContent='R$ '+brl(n===0?(tA?tA.preco:0):vk.total); if(!TIERS.length&&n>0) $('kpMsg').textContent='Pronto: finalize pelo WhatsApp ou continue escolhendo.';")
troca("kpEco", "(falta>0?'Complete '", "(falta>0&&tA?'Complete '")

# ---------- prato: recorte quando existe, foto redonda quando nao ----------
troca("fig", "'<button type=\"button\" class=\"fig'+(sl===ultimo?' novo':'')+'\"",
      "'<button type=\"button\" class=\"fig'+(sl===ultimo?' novo':'')+(IMG[sl+'_r']?'':' redondo')+'\"")
troca("pFoto", "$('pFoto').innerHTML=IMG[p.slug]?'<img src=\"'+IMG[p.slug]+'\" alt=\"'+p.titulo+'\">'",
      "$('pFoto').innerHTML=(IMGG[p.slug]||IMG[p.slug])?'<img src=\"'+(IMGG[p.slug]||IMG[p.slug])+'\" alt=\"'+p.titulo+'\">'")

# ---------- carregar da API ----------
carrega = r"""
  // ---------- dados do painel (GET /publico/presentes) ----------
  function carrega(){
    $('grid').innerHTML='<p class="carregando">Carregando os presentes…</p>';
    fetch(API+'/publico/presentes').then(function(r){ if(!r.ok) throw new Error('http '+r.status); return r.json(); }).then(function(d){
      var prods=d.produtos||[];
      P=prods.map(function(x){ var s=slugar(x.nome); return {id:x.id,slug:s,titulo:x.nome,preco:x.preco,descricao:x.descricao||'',medidas:'',grupo:GRUPO_POR_PECA[s]||'outros',peca:true}; });
      prods.forEach(function(x){ var s=slugar(x.nome); if(x.foto_mini||x.foto_url) IMG[s]=x.foto_mini||x.foto_url; if(x.foto_url) IMGG[s]=x.foto_url; if(ESC[s]) IMG[s+'_r']='assets/recortes/'+s+'.webp'; });
      TIERS=(d.kits||[]).map(function(k){ return {n:k.qtd_pecas,preco:Number(k.preco),nome:'Kit com '+k.qtd_pecas+' peças',sub:''}; });
      alvo=TIERS.length?TIERS[0].n:5;
      render();
      $('vazio').hidden=P.length>0;
    }).catch(function(){
      $('grid').innerHTML=''; $('vazio').textContent='Não conseguimos carregar os presentes agora. Fale com a gente pelo WhatsApp que ajudamos.'; $('vazio').hidden=false;
    });
  }
"""
i = src.rfind("  render();\n})();")
log["render_final"] = i >= 0
if i >= 0:
    src = src[:i] + carrega + "  carrega();\n})();" + src[i + len("  render();\n})();"):]

# ---------- estilos novos ----------
css = """
.prato .fig.redondo img{height:calc(15cqw*var(--h));width:calc(15cqw*var(--h));min-width:46px;min-height:46px;border-radius:50%;object-fit:cover;border:2px solid #fff;filter:drop-shadow(0 4px 4px rgba(60,35,10,.35))}
.carregando{grid-column:1/-1;color:var(--muted);padding:30px;text-align:center}
"""
troca("css", ".rever{flex-basis:100%;", css + ".rever{flex-basis:100%;")

open(os.path.join(AQUI, "index.html"), "w", encoding="utf-8").write(src)

# ---------- arquivos (imagens como arquivo, nao embutidas) ----------
A = os.path.join(AQUI, "assets"); os.makedirs(os.path.join(A, "recortes"), exist_ok=True)
for n in ("hero-natal-fundo.webp", "hero-natal-cena.webp", "gar-esq.webp", "gar-dir.webp", "papai-noel-treno.webp", "favicon.png"):
    shutil.copy(os.path.join(SITE, "assets", n), os.path.join(A, n))
for n in ("logo.png", "logo-dark.png"):
    im = Image.open(os.path.join(SITE, "assets", n)).convert("RGBA"); h = 96; w = round(im.width * h / im.height)
    im.resize((w, h), Image.LANCZOS).save(os.path.join(A, n), optimize=True)
for f in os.listdir(os.path.join(SITE, "assets", "pecas")):
    if f.endswith("-recorte.webp"):
        shutil.copy(os.path.join(SITE, "assets", "pecas", f), os.path.join(A, "recortes", f.replace("-recorte", "")))
fundo = Image.open(os.path.join(SITE, "assets", "hero-natal-fundo.webp")).convert("RGB")
w, h = fundo.size; cw = int(h * 1200 / 630); og = fundo.crop((w - cw, 0, w, h)).resize((1200, 630), Image.LANCZOS)
og.save(os.path.join(A, "og-natal.jpg"), quality=86)
open(os.path.join(AQUI, "CNAME"), "w").write("presentes.giftforma.com.br")
open(os.path.join(AQUI, ".nojekyll"), "w").write("")
open(os.path.join(AQUI, "robots.txt"), "w").write("User-agent: *\nAllow: /\nSitemap: https://presentes.giftforma.com.br/sitemap.xml\n")
open(os.path.join(AQUI, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://presentes.giftforma.com.br/</loc></url></urlset>\n')
print(json.dumps(log, ensure_ascii=False))
print("faltando:", [k for k, v in log.items() if not v])
