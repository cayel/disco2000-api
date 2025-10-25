-- Migration : création de la table users avec gestion multi-rôles
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    identifier VARCHAR NOT NULL UNIQUE,
    roles VARCHAR[] NOT NULL
);
-- Rôles possibles : 'utilisateur', 'contributeur', 'administrateur'
