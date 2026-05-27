import logging

import resend

from app.core.config import configuracoes

logger = logging.getLogger(__name__)


def _montar_html(
    nome: str,
    loja: str,
    preco_anterior: float,
    preco_atual: float,
    url: str,
    eh_historico: bool,
) -> str:
    """Gera o corpo HTML do e-mail de notificação."""
    diferenca = preco_atual - preco_anterior
    percentual = abs(diferenca / preco_anterior * 100) if preco_anterior else 0
    cor = "#16a34a" if diferenca < 0 else "#dc2626"
    sinal = "↓" if diferenca < 0 else "↑"
    destaque = ""

    if eh_historico:
        destaque = "<p style='color:#ca8a04;font-weight:bold;'>🏆 Menor preço dos últimos 12 meses!</p>"

    return f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#111">{nome}</h2>
      <p style="color:#6b7280">{loja}</p>
      {destaque}
      <p style="font-size:2rem;font-weight:bold;color:{cor}">
        R$ {preco_atual:,.2f}
      </p>
      <p style="color:#6b7280;text-decoration:line-through">
        Antes: R$ {preco_anterior:,.2f}
      </p>
      <p style="color:{cor}">
        {sinal} R$ {abs(diferenca):,.2f} ({percentual:.1f}%)
      </p>
      <a href="{url}" style="display:inline-block;margin-top:16px;padding:10px 20px;
         background:#111;color:#fff;border-radius:6px;text-decoration:none">
        Ver produto
      </a>
      <p style="margin-top:24px;font-size:0.75rem;color:#9ca3af">
        Zoiou · zoiou.com.br — Para cancelar notificações, acesse Preferências.
      </p>
    </div>
    """


async def enviar_notificacao_email(
    destinatario: str,
    nome: str,
    loja: str,
    preco_anterior: float,
    preco_atual: float,
    url: str,
    eh_historico: bool = False,
) -> bool:
    """Envia e-mail de variação de preço via Resend. Retorna True se enviou."""
    if not configuracoes.resend_api_key:
        logger.warning("RESEND_API_KEY não configurado.")
        return False

    resend.api_key = configuracoes.resend_api_key
    assunto = f"🏆 Preço histórico: {nome}" if eh_historico else f"Variação de preço: {nome}"
    corpo_html = _montar_html(nome, loja, preco_anterior, preco_atual, url, eh_historico)

    try:
        resend.Emails.send({
            "from": "Zoiou <noreply@zoiou.com.br>",
            "to": [destinatario],
            "subject": assunto,
            "html": corpo_html,
        })
        return True
    except Exception as exc:
        logger.error("Falha ao enviar e-mail para %s: %s", destinatario, exc)
        return False
