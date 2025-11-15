-- Migration: Ajout du champ country à la table artists
-- Date: 2025-11-15

-- Ajout de la colonne country à la table artists (code ISO 3166-1 alpha-2)
ALTER TABLE artists 
ADD COLUMN IF NOT EXISTS country CHAR(2);

-- Commentaire pour documentation
COMMENT ON COLUMN artists.country IS 'Pays d''origine de l''artiste (code ISO 3166-1 alpha-2 : FR, US, GB, etc.)';
