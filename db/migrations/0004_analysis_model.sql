-- Which model produced each analysis, so reviews can be traced to the model they judge.
ALTER TABLE analyses ADD COLUMN model text NOT NULL DEFAULT 'unknown';
