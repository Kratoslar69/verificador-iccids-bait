-- Script de configuración de base de datos para Sistema Verificador de ICCIDs BAIT
-- Ejecutar en Supabase SQL Editor

-- Eliminar tabla si existe (para reinstalación limpia)
DROP TABLE IF EXISTS verificacion_iccids CASCADE;

-- Crear tabla principal
CREATE TABLE verificacion_iccids (
  id BIGSERIAL PRIMARY KEY,
  iccid_completo VARCHAR(20) NOT NULL UNIQUE,      -- ICCID original (19-20 dígitos)
  ultimos_13_digitos VARCHAR(13),                  -- Para portal BAIT (sin F)
  estatus VARCHAR(20) DEFAULT 'PENDIENTE',         -- PENDIENTE/ACTIVA/INACTIVA/ERROR
  numero_asignado VARCHAR(10),                     -- Número telefónico si activa
  fecha_verificacion TIMESTAMP WITH TIME ZONE,     -- Timestamp de verificación
  lote VARCHAR(50),                                -- Identificador del batch
  observaciones TEXT,                              -- Notas adicionales/errores
  intentos INTEGER DEFAULT 0,                      -- Número de intentos de verificación
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para optimización de consultas
CREATE INDEX idx_iccid ON verificacion_iccids(iccid_completo);
CREATE INDEX idx_estatus ON verificacion_iccids(estatus);
CREATE INDEX idx_lote ON verificacion_iccids(lote);
CREATE INDEX idx_fecha_verificacion ON verificacion_iccids(fecha_verificacion);

-- Crear función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger para actualizar updated_at
CREATE TRIGGER update_verificacion_iccids_updated_at
    BEFORE UPDATE ON verificacion_iccids
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilitar Row Level Security (RLS) - opcional pero recomendado
ALTER TABLE verificacion_iccids ENABLE ROW LEVEL SECURITY;

-- Crear política para permitir todas las operaciones con service_role
CREATE POLICY "Permitir todas las operaciones para service_role"
ON verificacion_iccids
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Crear política para permitir lectura con anon key (opcional)
CREATE POLICY "Permitir lectura para usuarios anónimos"
ON verificacion_iccids
FOR SELECT
TO anon
USING (true);

-- Comentarios en la tabla
COMMENT ON TABLE verificacion_iccids IS 'Tabla para almacenar resultados de verificación de ICCIDs del portal BAIT';
COMMENT ON COLUMN verificacion_iccids.iccid_completo IS 'ICCID completo de 19-20 dígitos';
COMMENT ON COLUMN verificacion_iccids.ultimos_13_digitos IS 'Últimos 13 dígitos sin F para el portal BAIT';
COMMENT ON COLUMN verificacion_iccids.estatus IS 'Estado: PENDIENTE, ACTIVA, INACTIVA, ERROR';
COMMENT ON COLUMN verificacion_iccids.numero_asignado IS 'Número telefónico asignado si la SIM está activa';
