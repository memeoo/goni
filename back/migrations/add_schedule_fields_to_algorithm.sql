-- Migration: Add update_time and issue_time fields to algorithm table
-- Created: 2025-11-27
-- Purpose: Add scheduling information to algorithms

ALTER TABLE algorithm
ADD COLUMN update_time VARCHAR(5) DEFAULT NULL,
ADD COLUMN issue_time VARCHAR(5) DEFAULT NULL;

-- Add comment to columns
COMMENT ON COLUMN algorithm.update_time IS '업데이트 시간 (HH:MM 형식, 예: "18:10")';
COMMENT ON COLUMN algorithm.issue_time IS '발행 시간 (HH:MM 형식, 추가 정보용)';
