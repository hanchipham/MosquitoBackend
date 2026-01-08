-- ============================================================
-- IoT Larva Detection System - Database Schema
-- ============================================================
-- Sesuai dengan rancangan.md
-- Database: MySQL / MariaDB
-- ============================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS mosquito_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE mosquito_db;

-- ============================================================
-- Table: devices
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    id CHAR(36) PRIMARY KEY,
    device_code VARCHAR(255) NOT NULL UNIQUE,
    location VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_code (device_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: device_auth
-- ============================================================
CREATE TABLE IF NOT EXISTS device_auth (
    id CHAR(36) PRIMARY KEY,
    device_id CHAR(36) NOT NULL,
    device_code VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    INDEX idx_device_code (device_code),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: images
-- ============================================================
CREATE TABLE IF NOT EXISTS images (
    id CHAR(36) PRIMARY KEY,
    device_id CHAR(36) NOT NULL,
    device_code VARCHAR(255) NOT NULL,
    image_type VARCHAR(50),
    image_path VARCHAR(500),
    width INT,
    height INT,
    checksum VARCHAR(64),
    captured_at TIMESTAMP NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_code (device_code),
    INDEX idx_device_id (device_id),
    INDEX idx_uploaded_at (uploaded_at),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: inference_results
-- ============================================================
CREATE TABLE IF NOT EXISTS inference_results (
    id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    device_id CHAR(36) NOT NULL,
    device_code VARCHAR(255) NOT NULL,
    inference_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_prediction JSON,
    total_objects INT DEFAULT 0,
    total_jentik INT DEFAULT 0,
    total_non_jentik INT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    parsing_version VARCHAR(50),
    status VARCHAR(50),
    error_message TEXT,
    INDEX idx_device_code (device_code),
    INDEX idx_device_id (device_id),
    INDEX idx_inference_at (inference_at),
    INDEX idx_status (status),
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id CHAR(36) PRIMARY KEY,
    device_id CHAR(36) NOT NULL,
    device_code VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100),
    alert_message TEXT,
    alert_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_device_code (device_code),
    INDEX idx_device_id (device_id),
    INDEX idx_created_at (created_at),
    INDEX idx_resolved_at (resolved_at),
    INDEX idx_alert_level (alert_level),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Create simplified device_controls table
-- ============================================================
CREATE TABLE device_controls (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    device_id INT UNIQUE NOT NULL,
    device_code VARCHAR(50) UNIQUE NOT NULL,
    control_command ENUM('ACTIVATE', 'SLEEP', 'ACTIVATE_SERVO', 'STOP_SERVO') NOT NULL,
    status ENUM('PENDING', 'EXECUTED', 'FAILED') NOT NULL DEFAULT 'PENDING',
    message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (device_code) REFERENCES devices(device_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Selesai
-- ============================================================
