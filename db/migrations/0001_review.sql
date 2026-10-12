-- Review data for model ICMA analyses. Reviews are append-only: the full history of who accepted,
-- rejected, or revised each model judgement is the training signal, so nothing is updated in place.

CREATE TABLE analyses (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  package_id     text        NOT NULL,
  prompt_version text        NOT NULL,
  content_sha256 text        NOT NULL UNIQUE,
  payload        jsonb       NOT NULL,
  imported_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX analyses_package ON analyses (package_id, imported_at DESC);

-- One reviewable unit of model output.
CREATE TABLE judgements (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  analysis_id  bigint NOT NULL REFERENCES analyses (id) ON DELETE CASCADE,
  kind         text   NOT NULL CHECK (kind IN (
                 'convergence_point', 'common_link', 'partial_common_link', 'dive',
                 'matn_cluster', 'correlation', 'reconstruction', 'dating', 'upper_isnad',
                 'chain_matn', 'matn_element', 'variant_reading')),
  item_key     text   NOT NULL,  -- node key, chain id, variant id, element id, cluster label, or ''
  position     int    NOT NULL,  -- display order within the analysis
  model_output jsonb  NOT NULL,
  UNIQUE (analysis_id, kind, item_key)
);

CREATE TABLE reviews (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  judgement_id   bigint      NOT NULL REFERENCES judgements (id) ON DELETE CASCADE,
  reviewer       text        NOT NULL CHECK (length(reviewer) > 0),
  decision       text        NOT NULL CHECK (decision IN ('accept', 'reject', 'revise')),
  revised_output jsonb,
  note           text        NOT NULL DEFAULT '',
  created_at     timestamptz NOT NULL DEFAULT now(),
  CHECK ((decision = 'revise') = (revised_output IS NOT NULL))
);

CREATE INDEX reviews_by_judgement ON reviews (judgement_id, created_at DESC, id DESC);

-- The latest review of each judgement.
CREATE VIEW current_reviews AS
  SELECT DISTINCT ON (judgement_id) *
  FROM reviews
  ORDER BY judgement_id, created_at DESC, id DESC;
