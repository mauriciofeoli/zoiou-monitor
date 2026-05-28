import json
import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

_IMPERSONATE = ["chrome124", "chrome123", "chrome120"]

# Padrão de preço BR: 1.099,99 ou 999,99
_RE_PRECO_BR = re.compile(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b")
# Preço BR com R$ obrigatório antes — muito mais conservador
_RE_PRECO_COM_RS = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})\b")

_TIMEOUT_HTTP = 20
_TIMEOUT_MS = 20_000

# Limite razoável para preços de produtos de consumo
_PRECO_MAX = 100_000.0
_PRECO_MIN = 0.99


def parsear_preco(texto: str) -> float:
    """Converte string de preço BR para float. Ex: '1.099,99' → 1099.99"""
    limpo = str(texto).strip().replace(".", "").replace(",", ".")
    limpo = re.sub(r"[^\d.]", "", limpo)
    return float(limpo)


def _preco_json(valor) -> float | None:
    """Converte valor de meta/JSON-LD para float, suportando formatos BR e US."""
    if isinstance(valor, (int, float)):
        v = float(valor)
        return v if _PRECO_MIN < v < _PRECO_MAX else None
    if isinstance(valor, str):
        s = valor.strip()
        has_comma = "," in s
        has_dot = "." in s
        try:
            if has_comma and has_dot:
                # Ambos presentes — o separador mais à direita é o decimal.
                # "R$ 30,407.19" (US/híbrido) → ponto mais à direita → milhar=vírgula, decimal=ponto
                # "30.407,19" (BR)             → vírgula mais à direita → milhar=ponto, decimal=vírgula
                if s.rfind(".") > s.rfind(","):
                    clean = re.sub(r"[^\d.]", "", s.replace(",", ""))
                else:
                    clean = re.sub(r"[^\d.]", "", s.replace(".", "").replace(",", "."))
            elif has_comma:
                # Só vírgula — BR sem separador de milhar (ex: "30407,19")
                clean = re.sub(r"[^\d.]", "", s.replace(",", "."))
            elif re.match(r"^\d{1,3}(\.\d{3})+\.\d{2}$", s):
                # BR malformado: ponto como milhar E decimal (ex: "30.407.19")
                digits = re.sub(r"[^\d]", "", s)
                clean = digits[:-2] + "." + digits[-2:]
            elif re.match(r"^\d{1,3}(\.\d{3})+$", s):
                # BR sem centavos, ponto como milhar (ex: "30.407")
                clean = re.sub(r"[^\d]", "", s)
            else:
                # US/numérico direto (ex: "30407.19", "699.98")
                clean = re.sub(r"[^\d.]", "", s)
            v = float(clean)
            return v if _PRECO_MIN < v < _PRECO_MAX else None
        except ValueError:
            return None
    return None


def _candidatos_com_rs(texto: str) -> list[float]:
    """Extrai preços que têm 'R$' explícito antes — muito mais confiáveis."""
    resultado = []
    for m in _RE_PRECO_COM_RS.findall(texto):
        try:
            v = parsear_preco(m)
            if _PRECO_MIN < v < _PRECO_MAX:
                resultado.append(v)
        except ValueError:
            pass
    return resultado


def _extrair_preco_de_sopa(sopa: BeautifulSoup) -> float | None:
    """Extrai preço de um HTML parseado com múltiplas estratégias."""

    # 1. Open Graph / meta tags — refletem o preço exibido na página (mais confiável para promoções)
    # Alguns sites usam name=, outros property= para o mesmo campo
    meta_og = (
        sopa.find("meta", attrs={"name": "product:price:amount"})
        or sopa.find("meta", property="product:price:amount")
    )
    if meta_og and meta_og.get("content"):
        v = _preco_json(meta_og["content"])
        if v is not None:
            return v

    # 2. itemprop=price — schema.org visível
    el = sopa.find(attrs={"itemprop": "price"})
    if el:
        val = el.get("content") or el.get_text(strip=True)
        if val:
            v = _preco_json(val)
            if v is not None:
                return v

    # 3. Seletores CSS específicos de lojas BR com R$ explícito
    seletores_especificos = [
        ".prod-new-price",     # Terabyte, Pichau
        ".price__selling",     # Kabum
        ".preco-avista",
        ".preco-por",
        ".a-price-whole",      # Amazon
        ".a-offscreen",        # Amazon
        "[data-testid*=price]",
        "[class*=finalPrice]",
        "[class*=selling-price]",
        "[class*=best-price]",
    ]
    for sel in seletores_especificos:
        el = sopa.select_one(sel)
        if el:
            candidatos = _candidatos_com_rs(el.get_text(strip=True))
            if candidatos:
                # Ignora parcelas (valores pequenos) — pega o maior como preço à vista
                return max(candidatos)

    # 4. Padrão "por R$X" ou "à vista R$X" — específico, baixo risco de falso positivo
    for el in sopa.select(".info-price, [class*=price], [class*=preco]"):
        texto = el.get_text()
        for padrao in [
            r"(?:por|à vista|avista)[:\s]+R\$\s*([\d.]+,\d{2})",
            r"R\$\s*([\d.]+,\d{2})\s*(?:à vista|avista)",
        ]:
            m = re.search(padrao, texto, re.IGNORECASE)
            if m:
                try:
                    v = parsear_preco(m.group(1))
                    if _PRECO_MIN < v < _PRECO_MAX:
                        return v
                except ValueError:
                    pass

    # 5. JSON-LD (Product.offers.price) — pode ter preço sem desconto; usado como fallback
    for tag in sopa.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(tag.string or "")
            itens = dados if isinstance(dados, list) else [dados]
            for item in itens:
                if "@graph" in item:
                    itens.extend(item["@graph"])
                if item.get("@type") in ("Product", "IndividualProduct"):
                    ofertas = item.get("offers") or item.get("offer") or {}
                    if isinstance(ofertas, list):
                        ofertas = min(ofertas, key=lambda o: float(o.get("price", 0) or 0), default={})
                    for campo in ("lowPrice", "price"):
                        v = _preco_json(ofertas.get(campo))
                        if v is not None:
                            return v
        except Exception:
            continue

    # 6. Fallback conservador: só aceita R$ explícito em elementos de preço
    for el in sopa.select(".info-price, [class*=price], [class*=preco]"):
        candidatos = _candidatos_com_rs(el.get_text())
        if candidatos:
            maior = max(candidatos)
            candidatos = [c for c in candidatos if c >= maior * 0.1]
            return max(candidatos)

    return None


def _extrair_metadados_de_sopa(sopa: BeautifulSoup, url: str) -> dict:
    """Extrai nome, loja e imagem de um HTML parseado."""
    loja = urlparse(url).netloc.replace("www.", "")
    nome = ""
    imagem = ""

    # Nome: og:title > itemprop=name > h1
    for tentativa in [
        lambda: sopa.find("meta", property="og:title"),
        lambda: sopa.find(attrs={"itemprop": "name"}),
        lambda: sopa.find("h1"),
    ]:
        el = tentativa()
        if el:
            val = (el.get("content") or el.get_text(strip=True)).strip()
            if val:
                nome = val
                break

    # Imagem: og:image > itemprop=image > primeira img do produto
    meta_img = sopa.find("meta", property="og:image")
    if meta_img and meta_img.get("content"):
        imagem = str(meta_img["content"])
    else:
        el_img = sopa.find(attrs={"itemprop": "image"})
        if el_img:
            imagem = str(el_img.get("src") or el_img.get("content") or "")

    return {"nome": nome, "loja": loja, "imagem": imagem}


_HEADERS_BR = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


async def _buscar_html_cffi(url: str) -> str | None:
    """Busca HTML usando curl_cffi com fingerprint de Chrome — bypassa Cloudflare."""
    for perfil in _IMPERSONATE:
        try:
            async with AsyncSession(impersonate=perfil) as s:
                r = await s.get(url, timeout=_TIMEOUT_HTTP, headers=_HEADERS_BR)
                logger.info("curl_cffi [%s] → HTTP %d para %s", perfil, r.status_code, url)
                if r.status_code == 200:
                    return r.text
        except Exception as exc:
            logger.warning("curl_cffi [%s] falhou para %s: %s", perfil, url, exc)
    return None


async def _buscar_html_playwright(url: str) -> str | None:
    """Busca HTML via Playwright — fallback para sites com JS pesado."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            ctx = await browser.new_context(
                locale="pt-BR",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                extra_http_headers={"Accept-Language": "pt-BR,pt;q=0.9"},
            )
            page = await ctx.new_page()
            await page.goto(url, timeout=_TIMEOUT_MS, wait_until="domcontentloaded")
            for sel in [".prod-new-price", ".info-price", "[itemprop='price']", ".price"]:
                try:
                    await page.wait_for_selector(sel, timeout=5_000)
                    break
                except Exception:
                    continue
            html = await page.content()
            logger.info("Playwright obteve %d bytes para %s", len(html), url)
            return html
        except Exception as exc:
            logger.warning("Playwright falhou para %s: %s", url, exc)
            return None
        finally:
            await browser.close()


async def extrair_preco(url: str) -> float | None:
    """Extrai o preço de um produto. Tenta curl_cffi primeiro, depois Playwright."""
    try:
        for buscar in [_buscar_html_cffi, _buscar_html_playwright]:
            html = await buscar(url)
            if html:
                preco = _extrair_preco_de_sopa(BeautifulSoup(html, "html.parser"))
                if preco is not None:
                    logger.info("Preço extraído — %s: R$ %.2f", url, preco)
                    return preco
        logger.warning("Preço não encontrado para %s", url)
        return None
    except Exception as exc:
        logger.error("Erro ao extrair preço de %s: %s", url, exc)
        return None


async def extrair_metadados_produto(url: str) -> dict:
    """Extrai nome, loja e imagem do produto."""
    for buscar in [_buscar_html_cffi, _buscar_html_playwright]:
        html = await buscar(url)
        if html:
            meta = _extrair_metadados_de_sopa(BeautifulSoup(html, "html.parser"), url)
            if meta["nome"]:
                return meta
    loja = urlparse(url).netloc.replace("www.", "")
    return {"nome": "", "loja": loja, "imagem": ""}


async def extrair_produto_completo(url: str, *, usar_playwright: bool = True) -> dict:
    """Faz fetch e retorna nome, loja, imagem e preço juntos.

    usar_playwright=False faz apenas curl_cffi (rápido, para o path síncrono).
    usar_playwright=True (padrão) complementa com Playwright se faltar algo.
    """
    loja = urlparse(url).netloc.replace("www.", "")
    meta: dict = {"nome": "", "loja": loja, "imagem": ""}
    preco: float | None = None

    # 1ª tentativa: curl_cffi (rápido, sem JS)
    html = await _buscar_html_cffi(url)
    if html:
        sopa = BeautifulSoup(html, "html.parser")
        meta = _extrair_metadados_de_sopa(sopa, url)
        preco = _extrair_preco_de_sopa(sopa)

    # 2ª tentativa: Playwright se ainda falta algo e foi permitido
    if usar_playwright and (not meta["nome"] or preco is None):
        html_pw = await _buscar_html_playwright(url)
        if html_pw:
            sopa_pw = BeautifulSoup(html_pw, "html.parser")
            if not meta["nome"]:
                meta = _extrair_metadados_de_sopa(sopa_pw, url)
            if preco is None:
                preco = _extrair_preco_de_sopa(sopa_pw)

    logger.info(
        "Produto extraído — %s | nome=%s preco=%s",
        url,
        (meta["nome"] or "—")[:50],
        preco,
    )
    return {**meta, "preco": preco}
