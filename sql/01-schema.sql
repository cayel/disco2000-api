-- Table: artists
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    discogs_id INTEGER,
    CONSTRAINT artists_name_unique UNIQUE (name)
);

-- Table: labels
CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    discogs_id INTEGER UNIQUE,
    catno VARCHAR,
    CONSTRAINT labels_discogs_id_unique UNIQUE (discogs_id)
);

-- Table: albums
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    discogs_master_id INTEGER UNIQUE,
    year INTEGER,
    genre VARCHAR[],
    style VARCHAR[],
    cover_url VARCHAR,
    type VARCHAR DEFAULT 'Studio',
    artist_id INTEGER REFERENCES artists(id),
    label_id INTEGER REFERENCES labels(id)
);
