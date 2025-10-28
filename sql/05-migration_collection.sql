-- Migration : création de la table collection utilisateur/album/format
CREATE TABLE IF NOT EXISTS user_album_collection (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    cd BOOLEAN DEFAULT FALSE,
    vinyl BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, album_id)
);
