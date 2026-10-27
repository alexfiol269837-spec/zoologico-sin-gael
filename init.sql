CREATE DATABASE IF NOT EXISTS zoologico
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE zoologico;

CREATE TABLE IF NOT EXISTS animales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(100) NOT NULL,
    color VARCHAR(50) NOT NULL,
    edad INT NULL,
    sexo VARCHAR(30) NULL,
    habitat VARCHAR(150) NULL,
    descripcion TEXT NULL,
    imagen_url TEXT NULL,
    video_url TEXT NULL
);