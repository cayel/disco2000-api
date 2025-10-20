-- Supprime le champ catno de la table labels
ALTER TABLE labels DROP COLUMN IF EXISTS catno;

-- Ajoute le champ catno à la table albums
ALTER TABLE albums ADD COLUMN IF NOT EXISTS catno VARCHAR;
