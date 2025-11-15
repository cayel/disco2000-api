"""
Tests pour la validation et normalisation des codes pays.
"""
import pytest
from country_utils import (
    is_valid_country_code,
    normalize_country_code,
    get_country_name,
    get_all_countries,
    VALID_COUNTRY_CODES
)


class TestCountryValidation:
    """Tests de validation des codes pays."""
    
    def test_valid_country_codes(self):
        """Vérifie que les codes pays valides sont acceptés."""
        assert is_valid_country_code("FR") is True
        assert is_valid_country_code("US") is True
        assert is_valid_country_code("GB") is True
        assert is_valid_country_code("DE") is True
        assert is_valid_country_code("JP") is True
    
    def test_lowercase_codes_are_valid(self):
        """Les codes en minuscules doivent être considérés valides après normalisation."""
        # La fonction is_valid_country_code accepte les minuscules
        assert is_valid_country_code("fr") is True
        assert is_valid_country_code("us") is True
    
    def test_invalid_country_codes(self):
        """Vérifie que les codes pays invalides sont rejetés."""
        assert is_valid_country_code("XX") is False
        assert is_valid_country_code("ZZ") is False
        assert is_valid_country_code("FRA") is False  # 3 lettres
        assert is_valid_country_code("F") is False    # 1 lettre
        assert is_valid_country_code("123") is False
    
    def test_none_is_valid(self):
        """NULL/None doit être accepté (pays optionnel)."""
        assert is_valid_country_code(None) is True


class TestCountryNormalization:
    """Tests de normalisation des codes pays."""
    
    def test_normalize_uppercase(self):
        """Vérifie que les codes sont mis en majuscules."""
        assert normalize_country_code("fr") == "FR"
        assert normalize_country_code("us") == "US"
        assert normalize_country_code("Gb") == "GB"
    
    def test_normalize_strips_whitespace(self):
        """Vérifie que les espaces sont supprimés."""
        assert normalize_country_code("  FR  ") == "FR"
        assert normalize_country_code(" us ") == "US"
    
    def test_normalize_none(self):
        """None doit rester None."""
        assert normalize_country_code(None) is None


class TestCountryName:
    """Tests de récupération des noms de pays."""
    
    def test_get_country_name(self):
        """Vérifie que les noms de pays sont corrects."""
        assert get_country_name("FR") == "France"
        assert get_country_name("US") == "États-Unis"
        assert get_country_name("GB") == "Royaume-Uni"
        assert get_country_name("DE") == "Allemagne"
        assert get_country_name("JP") == "Japon"
    
    def test_get_country_name_lowercase(self):
        """Les codes en minuscules doivent fonctionner."""
        assert get_country_name("fr") == "France"
        assert get_country_name("us") == "États-Unis"
    
    def test_get_country_name_invalid(self):
        """Un code invalide doit retourner None."""
        assert get_country_name("XX") is None
        assert get_country_name("ZZZ") is None


class TestCountryList:
    """Tests de la liste complète des pays."""
    
    def test_get_all_countries_structure(self):
        """Vérifie la structure de la liste des pays."""
        countries = get_all_countries()
        assert isinstance(countries, list)
        assert len(countries) > 0
        
        # Vérifie la structure du premier élément
        first = countries[0]
        assert "code" in first
        assert "name" in first
        assert isinstance(first["code"], str)
        assert isinstance(first["name"], str)
        assert len(first["code"]) == 2
    
    def test_get_all_countries_count(self):
        """Vérifie qu'on a bien tous les pays."""
        countries = get_all_countries()
        assert len(countries) == len(VALID_COUNTRY_CODES)
    
    def test_get_all_countries_sorted(self):
        """Vérifie que la liste est triée par nom."""
        countries = get_all_countries()
        names = [c["name"] for c in countries]
        assert names == sorted(names)
    
    def test_get_all_countries_contains_major_countries(self):
        """Vérifie la présence des principaux pays."""
        countries = get_all_countries()
        codes = [c["code"] for c in countries]
        
        major_countries = ["FR", "US", "GB", "DE", "ES", "IT", "JP", "CA", "AU", "BR"]
        for code in major_countries:
            assert code in codes
