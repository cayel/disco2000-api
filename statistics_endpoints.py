from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.sql import text
from db import SessionLocal
from models import Album
import logging

logger = logging.getLogger("disco2000")

router = APIRouter()


@router.get("/api/statistics/genres-styles")
async def get_genres_and_styles_statistics():
    """
    Récupère les statistiques par genre et par style pour tous les albums.
    Accessible à tous les utilisateurs (authentifiés ou non).
    
    Returns:
        Dictionnaire contenant :
        - genres: Liste des genres avec leur nombre d'occurrences
        - styles: Liste des styles avec leur nombre d'occurrences
        - total_albums: Nombre total d'albums
    """
    async with SessionLocal() as session:
        # Récupère tous les albums avec leurs genres et styles
        stmt = select(Album.genre, Album.style)
        result = await session.execute(stmt)
        albums = result.all()
        
        # Compte le nombre total d'albums
        count_stmt = select(func.count()).select_from(Album)
        total_result = await session.execute(count_stmt)
        total_albums = total_result.scalar()
        
        # Dictionnaires pour compter les occurrences
        genre_counts = {}
        style_counts = {}
        
        # Parcourt tous les albums et compte les genres et styles
        for album_genre, album_style in albums:
            # Compte les genres (peut être un tableau)
            if album_genre:
                for genre in album_genre:
                    if genre:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Compte les styles (peut être un tableau)
            if album_style:
                for style in album_style:
                    if style:
                        style_counts[style] = style_counts.get(style, 0) + 1
        
        # Convertit en listes triées par nombre d'occurrences (décroissant)
        genres = [
            {"name": name, "count": count}
            for name, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        styles = [
            {"name": name, "count": count}
            for name, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        logger.info(f"Statistiques générées : {len(genres)} genres, {len(styles)} styles, {total_albums} albums")
        
        return {
            "total_albums": total_albums,
            "total_genres": len(genres),
            "total_styles": len(styles),
            "genres": genres,
            "styles": styles
        }


@router.get("/api/statistics/genres")
async def get_genres_statistics():
    """
    Récupère uniquement les statistiques par genre.
    Accessible à tous les utilisateurs (authentifiés ou non).
    
    Returns:
        Liste des genres avec leur nombre d'occurrences, triée par popularité
    """
    async with SessionLocal() as session:
        # Récupère tous les genres
        stmt = select(Album.genre)
        result = await session.execute(stmt)
        albums = result.scalars().all()
        
        # Compte les occurrences
        genre_counts = {}
        for album_genres in albums:
            if album_genres:
                for genre in album_genres:
                    if genre:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Convertit en liste triée
        genres = [
            {"name": name, "count": count}
            for name, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            "total": len(genres),
            "genres": genres
        }


@router.get("/api/statistics/styles")
async def get_styles_statistics():
    """
    Récupère uniquement les statistiques par style.
    Accessible à tous les utilisateurs (authentifiés ou non).
    
    Returns:
        Liste des styles avec leur nombre d'occurrences, triée par popularité
    """
    async with SessionLocal() as session:
        # Récupère tous les styles
        stmt = select(Album.style)
        result = await session.execute(stmt)
        albums = result.scalars().all()
        
        # Compte les occurrences
        style_counts = {}
        for album_styles in albums:
            if album_styles:
                for style in album_styles:
                    if style:
                        style_counts[style] = style_counts.get(style, 0) + 1
        
        # Convertit en liste triée
        styles = [
            {"name": name, "count": count}
            for name, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            "total": len(styles),
            "styles": styles
        }


@router.get("/api/statistics/overview")
async def get_overview_statistics():
    """
    Récupère des statistiques générales sur la collection complète.
    Accessible à tous les utilisateurs (authentifiés ou non).
    
    Returns:
        Statistiques générales : nombre d'albums, d'artistes, de labels, etc.
    """
    from models import Artist, Label
    
    async with SessionLocal() as session:
        # Compte total d'albums
        albums_count_stmt = select(func.count()).select_from(Album)
        albums_result = await session.execute(albums_count_stmt)
        total_albums = albums_result.scalar()
        
        # Compte total d'artistes
        artists_count_stmt = select(func.count()).select_from(Artist)
        artists_result = await session.execute(artists_count_stmt)
        total_artists = artists_result.scalar()
        
        # Compte total de labels
        labels_count_stmt = select(func.count()).select_from(Label)
        labels_result = await session.execute(labels_count_stmt)
        total_labels = labels_result.scalar()
        
        # Récupère la plage d'années
        years_stmt = select(func.min(Album.year), func.max(Album.year)).where(Album.year.isnot(None))
        years_result = await session.execute(years_stmt)
        min_year, max_year = years_result.one()
        
        # Compte les albums par décennie
        decades_stmt = select(
            func.floor(Album.year / 10) * 10,
            func.count()
        ).where(Album.year.isnot(None)).group_by(func.floor(Album.year / 10) * 10).order_by(func.floor(Album.year / 10) * 10)
        decades_result = await session.execute(decades_stmt)
        decades = [
            {"decade": int(decade), "count": count}
            for decade, count in decades_result.all()
        ]
        
        return {
            "total_albums": total_albums,
            "total_artists": total_artists,
            "total_labels": total_labels,
            "year_range": {
                "min": min_year,
                "max": max_year
            } if min_year and max_year else None,
            "albums_by_decade": decades
        }
