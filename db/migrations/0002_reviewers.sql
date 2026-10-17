-- Who may use the app. Neon Auth (neon_auth.user) proves identity; this table grants access.
-- Emails are stored lowercased, and access also requires the account's email to be verified.

CREATE TABLE reviewers (
  email    text        PRIMARY KEY CHECK (email = lower(email) AND position('@' IN email) > 1),
  role     text        NOT NULL CHECK (role IN ('admin', 'reviewer')),
  added_by text        NOT NULL,
  added_at timestamptz NOT NULL DEFAULT now()
);
