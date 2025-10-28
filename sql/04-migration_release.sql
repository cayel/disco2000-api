ALTER TABLE albums
ADD COLUMN discogs_link_type VARCHAR DEFAULT 'master';

UPDATE albums SET discogs_link_type = 'master' WHERE discogs_link_type IS NULL;