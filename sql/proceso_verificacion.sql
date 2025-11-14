-- Tabla para controlar el estado de los procesos de verificación
CREATE TABLE IF NOT EXISTS proceso_verificacion (
    id BIGSERIAL PRIMARY KEY,
    lote VARCHAR(255) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'DETENIDO', -- EJECUTANDO, PAUSADO, DETENIDO, COMPLETADO
    progreso_actual INT DEFAULT 0,
    progreso_total INT DEFAULT 0,
    activas INT DEFAULT 0,
    inactivas INT DEFAULT 0,
    errores INT DEFAULT 0,
    fecha_inicio TIMESTAMP DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP DEFAULT NOW(),
    UNIQUE(lote)
);

-- Índice para búsquedas rápidas por lote
CREATE INDEX IF NOT EXISTS idx_proceso_lote ON proceso_verificacion(lote);

-- Índice para búsquedas por estado
CREATE INDEX IF NOT EXISTS idx_proceso_estado ON proceso_verificacion(estado);
