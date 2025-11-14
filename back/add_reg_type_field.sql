-- Add reg_type field to trading_stocks table
ALTER TABLE trading_stocks
ADD COLUMN reg_type VARCHAR DEFAULT 'manual';

-- Update existing records to have 'api' if they were created by the system
-- (This is a conservative approach - we'll assume existing records were from API)
-- Uncomment the line below if you want to update existing records:
-- UPDATE trading_stocks SET reg_type = 'api' WHERE created_at IS NOT NULL;

-- Add index on reg_type for better query performance
CREATE INDEX idx_trading_stocks_reg_type ON trading_stocks(reg_type);
