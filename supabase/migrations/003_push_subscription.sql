alter table usuarios
  add column if not exists push_subscription jsonb;
