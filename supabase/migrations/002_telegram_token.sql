alter table usuarios
  add column if not exists telegram_token text,
  add column if not exists telegram_token_expira_em timestamptz;
