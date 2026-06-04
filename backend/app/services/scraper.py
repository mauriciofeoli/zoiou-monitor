import json
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

_IMPERSONATE = ["chrome124", "chrome123", "chrome120"]
_SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
_CF_WORKER_URL = os.getenv("CF_WORKER_URL")
_CF_WORKER_TOKEN = os.getenv("CF_WORKER_TOKEN")

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


def _preco_pix_de_candidatos(candidatos: list[float]) -> float:
    """Dado uma lista de preços do mesmo elemento, retorna o PIX (menor válido, filtrando parcelas)."""
    maior = max(candidatos)
    validos = [c for c in candidatos if c >= maior * 0.2]
    return min(validos)


def _extrair_preco_de_sopa(sopa: BeautifulSoup) -> float | None:
    """Extrai preço PIX/à vista de um HTML parseado. Sempre prioriza o menor preço disponível."""

    # 0. PIX explícito — classe ou texto com menção direta a pix/à vista/boleto
    _SELETORES_PIX = [
        "[class*=pix]",
        "[class*=avista]",
        "[class*=boleto]",
        "[class*=vista]",
        "[class*=cash]",
    ]
    for sel in _SELETORES_PIX:
        for el in sopa.select(sel):
            candidatos = _candidatos_com_rs(el.get_text(strip=True))
            if candidatos:
                return _preco_pix_de_candidatos(candidatos)

    # 1. Padrão textual PIX/à vista — antes das meta tags para evitar preço parcelado
    _RE_PIX = re.compile(
        r"(?:pix|à vista|avista|boleto)[:\s]*R\$\s*([\d.]+,\d{2})"
        r"|R\$\s*([\d.]+,\d{2})\s*(?:no pix|pix|à vista|avista|no boleto)",
        re.IGNORECASE,
    )
    for el in sopa.select(".info-price, [class*=price], [class*=preco], [class*=valor]"):
        m = _RE_PIX.search(el.get_text())
        if m:
            val = m.group(1) or m.group(2)
            try:
                v = parsear_preco(val)
                if _PRECO_MIN < v < _PRECO_MAX:
                    return v
            except ValueError:
                pass

    # 2. JSON-LD lowPrice — reflete o menor preço disponível (geralmente PIX)
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
                    v = _preco_json(ofertas.get("lowPrice"))
                    if v is not None:
                        return v
        except Exception:
            continue

    # 3. Open Graph / meta tags
    meta_og = (
        sopa.find("meta", attrs={"name": "product:price:amount"})
        or sopa.find("meta", property="product:price:amount")
    )
    if meta_og and meta_og.get("content"):
        v = _preco_json(meta_og["content"])
        if v is not None:
            return v

    # 4. itemprop=price — schema.org visível
    el = sopa.find(attrs={"itemprop": "price"})
    if el:
        val = el.get("content") or el.get_text(strip=True)
        if val:
            v = _preco_json(val)
            if v is not None:
                return v

    # 5. Seletores CSS específicos de lojas BR — retorna o menor preço no elemento
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
                return _preco_pix_de_candidatos(candidatos)

    # 6. __NEXT_DATA__ — sites Next.js (Pichau, etc.) embebem dados no SSR
    next_tag = sopa.find("script", id="__NEXT_DATA__")
    if next_tag:
        try:
            next_data = json.loads(next_tag.string or "")
            props = next_data.get("props", {}).get("pageProps", {})
            produto = (
                props.get("product")
                or props.get("productData")
                or props.get("initialState", {}).get("product", {})
            )
            if isinstance(produto, dict):
                for campo in ("price", "priceRange", "specialPrice", "finalPrice", "sale_price"):
                    val = produto.get(campo)
                    if val is None and "price_range" in produto:
                        val = (
                            produto["price_range"]
                            .get("minimum_price", {})
                            .get("final_price", {})
                            .get("value")
                        )
                    if val is not None:
                        v = _preco_json(val)
                        if v is not None:
                            return v
        except Exception:
            pass

    # 8. JSON-LD price (fallback — pode ser parcelado)
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
                    v = _preco_json(ofertas.get("price"))
                    if v is not None:
                        return v
        except Exception:
            continue

    # 9. Fallback: menor preço com R$ explícito em elementos de preço
    for el in sopa.select(".info-price, [class*=price], [class*=preco]"):
        candidatos = _candidatos_com_rs(el.get_text())
        if candidatos:
            return _preco_pix_de_candidatos(candidatos)

    return None


def _nome_parece_dominio(nome: str) -> bool:
    """True quando o nome extraído parece ser o domínio da loja, não o produto."""
    return bool(re.match(r"^[\w.-]+\.(com\.br|com|br|net|org|io)$", nome.lower().strip()))


def _nome_parece_homepage(nome: str, loja: str) -> bool:
    """True quando o nome parece ser o título da homepage da loja (ex: 'Shopee | Ofertas...')."""
    if " | " not in nome:
        return False
    marca = loja.split(".")[0].lower()
    prefixo = nome.split(" | ")[0].lower()
    return bool(marca) and marca in prefixo


def _extrair_metadados_de_sopa(sopa: BeautifulSoup, url: str) -> dict:
    """Extrai nome, loja e imagem de um HTML parseado."""
    loja = urlparse(url).netloc.replace("www.", "")
    nome = ""
    imagem = ""

    # 0. JSON-LD Product schema — mais confiável que og:title (contém o nome real do produto)
    for tag in sopa.find_all("script", type="application/ld+json"):
        try:
            dados_ld = json.loads(tag.string or "")
            itens = dados_ld if isinstance(dados_ld, list) else [dados_ld]
            for item in itens:
                if "@graph" in item:
                    itens.extend(item["@graph"])
                if item.get("@type") in ("Product", "IndividualProduct"):
                    if not nome and item.get("name"):
                        nome = str(item["name"]).strip()
                    if not imagem and item.get("image"):
                        img = item["image"]
                        if isinstance(img, list):
                            img = img[0]
                        if isinstance(img, dict):
                            img = img.get("url") or img.get("contentUrl") or ""
                        imagem = str(img).strip()
                    if nome and imagem:
                        break
        except Exception:
            continue

    # 1. Nome: og:title > itemprop=name > h1 (se JSON-LD não encontrou)
    if not nome:
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

    # 2. Imagem: og:image > itemprop=image (se JSON-LD não encontrou)
    if not imagem:
        meta_img = sopa.find("meta", property="og:image")
        if meta_img and meta_img.get("content"):
            imagem = str(meta_img["content"])
        else:
            el_img = sopa.find(attrs={"itemprop": "image"})
            if el_img:
                imagem = str(el_img.get("src") or el_img.get("content") or "")

    if imagem.startswith("http://"):
        imagem = "https://" + imagem[7:]
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


async def _buscar_html_worker(url: str) -> str | None:
    """Busca HTML via Cloudflare Worker — bypassa bloqueios de IP de data center."""
    if not _CF_WORKER_URL or not _CF_WORKER_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                _CF_WORKER_URL,
                params={"url": url, "token": _CF_WORKER_TOKEN},
            )
            logger.info("CF Worker → HTTP %d para %s", r.status_code, url)
            if r.status_code == 200:
                return r.text
    except Exception as exc:
        logger.warning("CF Worker falhou para %s: %s", url, exc)
    return None


async def _buscar_html_scraper_api(url: str) -> str | None:
    """Busca HTML via ScraperAPI — bypassa bloqueios de IP de data center."""
    if not _SCRAPER_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://api.scraperapi.com",
                params={"api_key": _SCRAPER_API_KEY, "url": url, "country_code": "br"},
            )
            logger.info("ScraperAPI → HTTP %d para %s", r.status_code, url)
            if r.status_code == 200:
                return r.text
    except Exception as exc:
        logger.warning("ScraperAPI falhou para %s: %s", url, exc)
    return None


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
            _SELS_PRECO = [
                ".prod-new-price",    # Terabyte, Pichau
                ".price__selling",    # Kabum
                "[itemprop='price']",
                "[class*=finalPrice]",
                "[class*=selling-price]",
                "[class*=best-price]",
                ".a-price-whole",     # Amazon
                ".info-price",
                ".price",
            ]
            for sel in _SELS_PRECO:
                try:
                    await page.wait_for_selector(sel, timeout=4_000)
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


def _ml_item_id(url: str) -> str | None:
    """Extrai o ID de item MLB de uma URL do Mercado Livre (vários formatos)."""
    from urllib.parse import parse_qs, unquote

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # /up/ com item_id nos pdp_filters: pdp_filters=item_id%3AMLB4133477319
    pdp = unquote(qs.get("pdp_filters", [""])[0])
    m = re.search(r"item_id[:%=]+(MLB\d+)", pdp)
    if m:
        return m.group(1)

    # /p/MLB4133477319 ou /p/MLBU3314664137 (catálogo → tenta mesmo)
    m = re.search(r"/p/(MLB\d+)", parsed.path)
    if m:
        return m.group(1)

    # /produto-nome/MLB-4133477319- ou /{slug}#MLB4133477319
    m = re.search(r"/MLB-?(\d+)", parsed.path)
    if m:
        return f"MLB{m.group(1)}"

    return None


async def _extrair_dados_mercadolivre(url: str) -> dict | None:
    """Extrai nome, imagem e preço via API pública do Mercado Livre."""
    item_id = _ml_item_id(url)
    if not item_id:
        return None
    api_url = f"https://api.mercadolibre.com/items/{item_id}"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(api_url, headers={"Accept": "application/json"})
            logger.info("ML API → HTTP %d para %s (item %s)", r.status_code, url, item_id)
            if r.status_code != 200:
                return None
            data = r.json()
            preco_raw = data.get("price")
            preco: float | None = None
            if preco_raw is not None:
                v = float(preco_raw)
                preco = v if _PRECO_MIN < v < _PRECO_MAX else None
            nome = (data.get("title") or "").strip()
            pictures = data.get("pictures") or []
            thumbnail = (data.get("thumbnail") or "").replace("http://", "https://")
            imagem = pictures[0].get("url", thumbnail).replace("http://", "https://") if pictures else thumbnail
            return {"nome": nome, "loja": "mercadolivre.com.br", "imagem": imagem, "preco": preco}
    except Exception as exc:
        logger.warning("ML API falhou para %s: %s", url, exc)
        return None


def _shopee_ids(url: str) -> tuple[str, str] | None:
    """Extrai (shopid, itemid) do path da URL da Shopee (-i.shopid.itemid)."""
    m = re.search(r"-i\.(\d+)\.(\d+)", urlparse(url).path)
    return (m.group(1), m.group(2)) if m else None


def _nome_de_slug_shopee(url: str) -> str:
    """Extrai o nome do produto do slug da URL da Shopee como último recurso."""
    from urllib.parse import unquote
    slug = urlparse(url).path.split("/")[-1]
    slug = re.sub(r"-i\.\d+\.\d+$", "", slug)
    return re.sub(r"\s{2,}", " ", unquote(slug).replace("-", " ")).strip()


async def _extrair_dados_shopee(url: str) -> dict | None:
    """Extrai nome, imagem e preço via API interna da Shopee (sem scraping HTML)."""
    ids = _shopee_ids(url)
    if not ids:
        return None
    shopid, itemid = ids
    api_url = f"https://shopee.com.br/api/v4/item/get?itemid={itemid}&shopid={shopid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://shopee.com.br/",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "X-Api-Source": "pc",
    }
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(api_url, headers=headers)
            logger.info("Shopee API → HTTP %d para %s", r.status_code, url)
            if r.status_code != 200:
                return None
            item = (r.json().get("data") or {})
            nome = (item.get("name") or "").strip()
            if not nome:
                return None
            preco_raw = item.get("price_min") or item.get("price")
            preco = None
            if preco_raw:
                v = round(preco_raw / 100000, 2)
                preco = v if _PRECO_MIN < v < _PRECO_MAX else None
            imagens = item.get("images") or []
            imagem = f"https://cf.shopee.com.br/file/{imagens[0]}" if imagens else ""
            return {"nome": nome, "loja": "shopee.com.br", "imagem": imagem, "preco": preco}
    except Exception as exc:
        logger.warning("Shopee API falhou para %s: %s", url, exc)
        return None


async def extrair_preco(url: str) -> float | None:
    """Extrai o preço de um produto. Tenta API da Shopee/ML, Worker, ScraperAPI, curl_cffi, Playwright."""
    try:
        if "shopee.com.br" in url:
            dados = await _extrair_dados_shopee(url)
            if dados and dados.get("preco") is not None:
                logger.info("Shopee API: R$ %.2f para %s", dados["preco"], url)
                return dados["preco"]

        if "mercadolivre.com.br" in url or "mercadolibre.com.br" in url:
            dados = await _extrair_dados_mercadolivre(url)
            if dados and dados.get("preco") is not None:
                logger.info("ML API: R$ %.2f para %s", dados["preco"], url)
                return dados["preco"]

        for buscar in [_buscar_html_worker, _buscar_html_scraper_api, _buscar_html_cffi, _buscar_html_playwright]:
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
    """Extrai nome, loja e imagem do produto. Rejeita nomes que parecem domínios ou homepages."""
    loja = urlparse(url).netloc.replace("www.", "")

    if "shopee.com.br" in url:
        dados = await _extrair_dados_shopee(url)
        if dados and dados.get("nome"):
            return {"nome": dados["nome"], "loja": loja, "imagem": dados.get("imagem", "")}

    if "mercadolivre.com.br" in url or "mercadolibre.com.br" in url:
        dados = await _extrair_dados_mercadolivre(url)
        if dados and dados.get("nome"):
            return {"nome": dados["nome"], "loja": loja, "imagem": dados.get("imagem", "")}

    for buscar in [_buscar_html_worker, _buscar_html_scraper_api, _buscar_html_cffi, _buscar_html_playwright]:
        html = await buscar(url)
        if html:
            meta = _extrair_metadados_de_sopa(BeautifulSoup(html, "html.parser"), url)
            nome = meta["nome"]
            if (
                nome
                and nome != loja
                and not _nome_parece_dominio(nome)
                and not _nome_parece_homepage(nome, loja)
            ):
                return meta

    if "shopee.com.br" in url:
        slug_nome = _nome_de_slug_shopee(url)
        if slug_nome:
            return {"nome": slug_nome, "loja": loja, "imagem": ""}

    return {"nome": "", "loja": loja, "imagem": ""}


async def extrair_produto_completo(url: str, *, usar_playwright: bool = True) -> dict:
    """Faz fetch e retorna nome, loja, imagem e preço juntos.

    usar_playwright=False faz apenas curl_cffi (rápido, para o path síncrono).
    usar_playwright=True (padrão) complementa com Playwright se faltar algo.
    """
    loja = urlparse(url).netloc.replace("www.", "")
    meta: dict = {"nome": "", "loja": loja, "imagem": ""}
    preco: float | None = None

    if "shopee.com.br" in url:
        dados = await _extrair_dados_shopee(url)
        if dados:
            if dados.get("nome"):
                meta = {"nome": dados["nome"], "loja": loja, "imagem": dados.get("imagem", "")}
            preco = dados.get("preco")
        if meta["nome"] and preco is not None:
            logger.info("Shopee API — %s | nome=%s preco=%s", url, meta["nome"][:50], preco)
            return {**meta, "preco": preco}

    if "mercadolivre.com.br" in url or "mercadolibre.com.br" in url:
        dados = await _extrair_dados_mercadolivre(url)
        if dados:
            if dados.get("nome"):
                meta = {"nome": dados["nome"], "loja": loja, "imagem": dados.get("imagem", "")}
            preco = dados.get("preco")
        if meta["nome"] and preco is not None:
            logger.info("ML API — %s | nome=%s preco=%s", url, meta["nome"][:50], preco)
            return {**meta, "preco": preco}

    # 1ª tentativa: Worker > ScraperAPI > curl_cffi
    html = await _buscar_html_worker(url) or await _buscar_html_scraper_api(url) or await _buscar_html_cffi(url)
    if html:
        sopa = BeautifulSoup(html, "html.parser")
        meta_html = _extrair_metadados_de_sopa(sopa, url)
        if meta_html["nome"] and not _nome_parece_homepage(meta_html["nome"], loja):
            meta = meta_html
        if preco is None:
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

    # Shopee: usa slug da URL como fallback para o nome se tudo falhou
    if not meta["nome"] and "shopee.com.br" in url:
        slug_nome = _nome_de_slug_shopee(url)
        if slug_nome:
            meta["nome"] = slug_nome

    logger.info(
        "Produto extraído — %s | nome=%s preco=%s",
        url,
        (meta["nome"] or "—")[:50],
        preco,
    )
    return {**meta, "preco": preco}
