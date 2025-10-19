from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from db import Base

class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    discogs_id = Column(Integer, index=True, nullable=True)
    albums = relationship("Album", back_populates="artist")

class Label(Base):
    __tablename__ = "labels"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    discogs_id = Column(Integer, index=True, unique=True)
    catno = Column(String, nullable=True)
    albums = relationship("Album", back_populates="label")

class Album(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    discogs_master_id = Column(Integer, index=True, unique=True)
    year = Column(Integer)
    genre = Column(ARRAY(String))
    style = Column(ARRAY(String))
    cover_url = Column(String)
    type = Column(String, default="Studio")
    artist_id = Column(Integer, ForeignKey("artists.id"))
    label_id = Column(Integer, ForeignKey("labels.id"))
    artist = relationship("Artist", back_populates="albums")
    label = relationship("Label", back_populates="albums")
