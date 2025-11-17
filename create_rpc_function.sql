-- Función RPC para obtener lotes únicos de manera eficiente
-- Esto evita el límite de 1000 registros de Supabase

CREATE OR REPLACE FUNCTION get_lotes_unicos()
RETURNS TABLE (lote TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT verificacion_iccids.lote
  FROM verificacion_iccids
  ORDER BY verificacion_iccids.lote;
END;
$$ LANGUAGE plpgsql STABLE;

-- Dar permisos de ejecución
GRANT EXECUTE ON FUNCTION get_lotes_unicos() TO anon, authenticated, service_role;
