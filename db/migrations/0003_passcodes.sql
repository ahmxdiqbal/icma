-- Sign-in is an email plus a per-reviewer passcode, stored only as a scrypt hash.
ALTER TABLE reviewers ADD COLUMN passcode_hash text;
