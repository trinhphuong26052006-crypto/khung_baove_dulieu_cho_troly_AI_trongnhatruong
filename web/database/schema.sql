-- =============================================================
-- AI_ASSISTANTB — DATABASE SCHEMA
-- File: database/schema.sql
-- Chạy file này để tạo toàn bộ cấu trúc bảng.
-- Chỉ cần chạy MỘT LẦN khi cài đặt lần đầu.
-- Thay đổi sau này dùng file trong database/migrations/
-- =============================================================

CREATE DATABASE IF NOT EXISTS AI_ASSISTANT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AI_ASSISTANT;

-- -------------------------------------------------------------
-- BẢNG: users — Tài khoản người dùng
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100)  NOT NULL,
    email       VARCHAR(255)  NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,
    avatar_path VARCHAR(255)  NULL,
    role        ENUM('SinhVien', 'GiangVien', 'QuanTri') NOT NULL DEFAULT 'SinhVien',
    status      ENUM('active','locked') NOT NULL DEFAULT 'active',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;