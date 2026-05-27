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
    """Converte valor de JSON-LD para float sem destruir números US-format.
    JSON-LD usa float padrão (699.98), não BR (699,98). parsear_preco quebraria isso.
    """
    if isinstance(valor, (int, float)):
        v = float(valor)
        return v if _PRECO_MIN < v < _PRECO_MAX else None
    if isinstance(valor, str):
        s = valor.strip()
        if "," in s:
            # Formato BR — pode usar parsear_preco
            try:
                v = parsear_preco(s)
                return v if _PRECO_MIN < v < _PRECO_MAX else None
            except ValueError:
                return None
        else:
            # Formato US/numérico — converte direto
            try:
                v = float(re.sub(r"[^\d.]", "", s))
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


async def _buscar_html_cffi(url: str) -> str | None:
    """Busca HTML usando curl_cffi com fingerprint de Chrome — bypassa Cloudflare."""
    for perfil in _IMPERSONATE:
        try:
            async with AsyncSession(impersonate=perfil) as s:
                r = await s.get(url, timeout=_TIMEOUT_HTTP)
                if r.status_code == 200:
                    return r.text
        except Exception as exc:
            logger.debug("curl_cffi [%s] falhou para %s: %s", perfil, url, exc)
    return None


async def _buscar_html_playwright(url: str) -> str | None:
    """Busca HTML via Playwright — fallback para sites com JS pesado."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(locale="pt-BR")
            page = await ctx.new_page()
            await page.goto(url, timeout=_TIMEOUT_MS, wait_until="domcontentloaded")
            # Aguarda até 5s por algum elemento de preço
            for sel in [".prod-new-price", ".info-price", "[itemprop='price']", ".price"]:
                try:
                    await page.wait_for_selector(sel, timeout=5_000)
                    break
                except Exception:
                    continue
            return await page.content()
        except Exception as exc:
            logger.debug("Playwright falhou para %s: %s", url, exc)
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
