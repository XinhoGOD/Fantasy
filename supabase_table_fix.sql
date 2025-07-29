-- SQL para actualizar tabla EXISTENTE nfl_fantasy_trends en Supabase
-- Ejecutar este código en el SQL Editor de Supabase

-- Primero verificar qué columnas existen actualmente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'nfl_fantasy_trends' 
ORDER BY ordinal_position;

-- Agregar columna timestamp si no existe (para tablas existentes)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'nfl_fantasy_trends' 
                   AND column_name = 'timestamp') THEN
        ALTER TABLE nfl_fantasy_trends ADD COLUMN timestamp TIMESTAMPTZ DEFAULT NOW();
        RAISE NOTICE 'Columna timestamp agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna timestamp ya existe';
    END IF;
END $$;

-- Agregar columna semana si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'nfl_fantasy_trends' 
                   AND column_name = 'semana') THEN
        ALTER TABLE nfl_fantasy_trends ADD COLUMN semana INTEGER DEFAULT 1;
        RAISE NOTICE 'Columna semana agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna semana ya existe';
    END IF;
END $$;

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_nfl_trends_player_time ON nfl_fantasy_trends(player_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_nfl_trends_semana ON nfl_fantasy_trends(semana);
CREATE INDEX IF NOT EXISTS idx_nfl_trends_timestamp ON nfl_fantasy_trends(timestamp);

-- Verificar la estructura FINAL de la tabla después de los cambios
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'nfl_fantasy_trends' 
ORDER BY ordinal_position;

-- Mostrar un mensaje de confirmación
SELECT 'Tabla nfl_fantasy_trends actualizada exitosamente!' as mensaje;
