-- Add evaluation and evaluation_reason columns to recap table

ALTER TABLE recap
ADD COLUMN IF NOT EXISTS evaluation VARCHAR,
ADD COLUMN IF NOT EXISTS evaluation_reason TEXT;

-- Add comments for documentation
COMMENT ON COLUMN recap.evaluation IS '평가 (good, so-so, bad)';
COMMENT ON COLUMN recap.evaluation_reason IS '평가 이유';
