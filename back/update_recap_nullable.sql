-- Make trading_plan_id nullable in recap table

ALTER TABLE recap
ALTER COLUMN trading_plan_id DROP NOT NULL;

-- Add comment
COMMENT ON COLUMN recap.trading_plan_id IS 'Trading plan ID (nullable for order_no based recap)';
