Feature: Monitoramento de preços
  Como usuário do Zoiou
  Quero ser notificado quando o preço de um produto muda
  Para aproveitar as melhores ofertas

  Background:
    Given um produto monitorado com id "prod-001"
    And o usuário "user-001" tem Telegram conectado e notificações ativas

  Scenario: Preço cai - notificação enviada
    Given o último preço registrado é R$ 1920,00
    When o scraper captura o preço R$ 1850,00
    Then o sistema registra o novo preço no histórico
    And envia notificação via Telegram com "📉"
    And não inclui badge de preço histórico

  Scenario: Preço sobe - notificação enviada
    Given o último preço registrado é R$ 1850,00
    When o scraper captura o preço R$ 1920,00
    Then o sistema registra o novo preço no histórico
    And envia notificação via Telegram com "📈"

  Scenario: Preço não muda - sem notificação
    Given o último preço registrado é R$ 1850,00
    When o scraper captura o preço R$ 1850,00
    Then o sistema NÃO registra novo preço
    And NÃO envia notificação

  Scenario: Variação menor que R$ 0,01 - sem notificação
    Given o último preço registrado é R$ 1850,00
    When o scraper captura o preço R$ 1850,005
    Then o sistema NÃO registra novo preço
    And NÃO envia notificação

  Scenario: Preço bate mínimo histórico - badge especial
    Given o histórico dos últimos 12 meses tem mínimo de R$ 99,90
    And o último preço registrado é R$ 110,00
    When o scraper captura o preço R$ 89,90
    Then o sistema registra o novo preço no histórico
    And envia notificação via Telegram com "🏆"
    And a notificação contém "PREÇO HISTÓRICO"

  Scenario: Scraper falha - sem registro nem notificação
    Given o último preço registrado é R$ 1850,00
    When o scraper não consegue capturar o preço (retorna None)
    Then o sistema NÃO registra novo preço
    And NÃO envia notificação

  Scenario: Usuário sem Telegram configurado - sem notificação Telegram
    Given o usuário "user-002" não tem Telegram conectado
    And o último preço registrado é R$ 1850,00
    When o scraper captura o preço R$ 1700,00
    Then o sistema registra o novo preço no histórico
    And NÃO envia notificação via Telegram para "user-002"

  Scenario: Notificação Telegram desativada - sem envio
    Given o usuário "user-003" tem Telegram conectado mas notificações desativadas
    And o último preço registrado é R$ 1850,00
    When o scraper captura o preço R$ 1700,00
    Then o sistema registra o novo preço no histórico
    And NÃO envia notificação via Telegram para "user-003"
