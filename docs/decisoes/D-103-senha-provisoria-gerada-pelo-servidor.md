# D-103 — Usuário de organização real nasce com senha provisória gerada pelo servidor, mostrada uma vez, e troca obrigatória

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

Convite por e-mail exige envio de e-mail, que não existe — nem hospedagem decidida.

## Decisão

A administradora cria o usuário, e o servidor gera uma **senha provisória** (16 caracteres, por
`secrets`, que passa nos validadores), devolvida **uma vez** a quem pediu e nunca guardada em claro
nem registrada. O usuário nasce com `must_change_password`, e só `me`, `password`, `logout` e `csrf`
servem até a troca. A administradora pode gerar senha provisória nova para outro usuário da
organização, o que derruba as sessões dele.

## Consequências

- A senha trafega fora do sistema, da administradora para a pessoa: é o preço de não haver e-mail.
- Quem esquece a senha da organização **pessoal** fica sem saída até existir e-mail — dívida
  registrada no ESTADO.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
