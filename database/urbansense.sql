CREATE DATABASE IF NOT EXISTS urbansense;
USE urbansense;

CREATE TABLE IF NOT EXISTS buses (
 id INT AUTO_INCREMENT PRIMARY KEY,
 bus_id VARCHAR(50) UNIQUE NOT NULL,
 registration_number VARCHAR(50),
 route_name VARCHAR(100),
 status VARCHAR(30) DEFAULT 'ACTIVE',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detections (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 bus_id VARCHAR(50) NOT NULL,
 cars INT DEFAULT 0,
 buses INT DEFAULT 0,
 trucks INT DEFAULT 0,
 motorcycles INT DEFAULT 0,
 bicycles INT DEFAULT 0,
 persons INT DEFAULT 0,
 total_vehicles INT DEFAULT 0,
 traffic_level VARCHAR(20),
 latitude DECIMAL(10,7),
 longitude DECIMAL(10,7),
 confidence DECIMAL(5,4),
 detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 bus_id VARCHAR(50) NOT NULL,
 event_type VARCHAR(50) NOT NULL,
 severity VARCHAR(20) DEFAULT 'MEDIUM',
 confidence DECIMAL(5,4),
 latitude DECIMAL(10,7),
 longitude DECIMAL(10,7),
 description VARCHAR(500),
 status VARCHAR(30) DEFAULT 'NEW',
 detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO buses(bus_id,registration_number,route_name)
VALUES
('BUS-101','TN38AB1001','Coimbatore - Tiruppur'),
('BUS-102','TN38AB1002','Coimbatore - Erode'),
('BUS-103','TN38AB1003','Coimbatore - Mettupalayam');
