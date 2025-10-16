"""
Calendar utilities for GEDCOM date parsing.
Extracted from parser to reduce cyclomatic complexity while preserving OCaml compatibility.
"""
from typing import Dict, Tuple, Optional
from ..common.base_models import BaseDate, DatePrecision


class CalendarUtils:
    """Utility class for calendar system conversions and month parsing."""
    
    # Calendar month mappings
    GREGORIAN_MONTHS = {
        "JAN": 1, "JANUARY": 1,
        "FEB": 2, "FEBRUARY": 2,
        "MAR": 3, "MARCH": 3,
        "APR": 4, "APRIL": 4,
        "MAY": 5,
        "JUN": 6, "JUNE": 6,
        "JUL": 7, "JULY": 7,
        "AUG": 8, "AUGUST": 8,
        "SEP": 9, "SEPTEMBER": 9, "SEPT": 9,
        "OCT": 10, "OCTOBER": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DEC": 12, "DECEMBER": 12
    }
    
    FRENCH_MONTHS = {
        "VEND": 1, "VENDÉMIAIRE": 1, "VENDEMIAIRE": 1,
        "BRUM": 2, "BRUMAIRE": 2,
        "FRIM": 3, "FRIMAIRE": 3,
        "NIVO": 4, "NIVÔSE": 4, "NIVOSE": 4,
        "PLUV": 5, "PLUVIÔSE": 5, "PLUVIOSE": 5,
        "VENT": 6, "VENTÔSE": 6, "VENTOSE": 6,
        "GERM": 7, "GERMINAL": 7,
        "FLOR": 8, "FLORÉAL": 8, "FLOREAL": 8,
        "PRAI": 9, "PRAIRIAL": 9,
        "MESS": 10, "MESSIDOR": 10,
        "THER": 11, "THERMIDOR": 11,
        "FRUC": 12, "FRUCTIDOR": 12,
        "COMP": 13, "SANSCULOTTIDES": 13  # Complementary days
    }
    
    HEBREW_MONTHS = {
        "TSH": 1, "TISHREI": 1,
        "CSH": 2, "CHESHVAN": 2, "HESHVAN": 2,
        "KSL": 3, "KISLEV": 3,
        "TVT": 4, "TEVET": 4,
        "SHV": 5, "SHEVAT": 5,
        "ADR": 6, "ADAR": 6,
        "ADS": 7, "ADAR_II": 7,  # Leap month
        "NSN": 7, "NISAN": 7,   # Spring
        "IYR": 8, "IYAR": 8,
        "SVN": 9, "SIVAN": 9,
        "TMZ": 10, "TAMMUZ": 10,
        "AAV": 11, "AV": 11,
        "ELL": 12, "ELUL": 12
    }
    
    @staticmethod
    def parse_month(month_str: str) -> int:
        """Parse month string to number with enhanced calendar system support."""
        if not month_str:
            return 0
            
        month_str = month_str.upper()
        
        # Try Gregorian/Julian first (most common)
        if month_str in CalendarUtils.GREGORIAN_MONTHS:
            return CalendarUtils.GREGORIAN_MONTHS[month_str]
            
        # Try French Republican
        if month_str in CalendarUtils.FRENCH_MONTHS:
            return CalendarUtils.FRENCH_MONTHS[month_str]
            
        # Try Hebrew
        if month_str in CalendarUtils.HEBREW_MONTHS:
            return CalendarUtils.HEBREW_MONTHS[month_str]
            
        # Try numeric
        if month_str.isdigit():
            month_num = int(month_str)
            return month_num if 1 <= month_num <= 13 else 0  # 13 for leap months/complementary days
        
        # Unknown month
        return 0
    
    @staticmethod
    def julian_day_number(day: int, month: int, year: int) -> int:
        """Convert date to Julian Day Number for calendar calculations."""
        if month <= 2:
            month += 12
            year -= 1
        
        a = year // 100
        b = 2 - a + (a // 4)
        
        # Handle Julian vs Gregorian calendar switch
        if year < 1582 or (year == 1582 and month < 10) or (year == 1582 and month == 10 and day < 15):
            b = 0  # Julian calendar
        
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
    
    @staticmethod
    def jdn_to_gregorian(jdn: int) -> Tuple[int, int, int]:
        """Convert Julian Day Number to Gregorian date."""
        a = jdn + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        
        day = e - (153 * m + 2) // 5 + 1
        month = m + 3 - (12 * (m // 10))
        year = 100 * b + d - 4800 + (m // 10)
        
        return day, month, year
    
    @staticmethod
    def jdn_to_julian(jdn: int) -> Tuple[int, int, int]:
        """Convert Julian Day Number to Julian date."""
        a = jdn + 1402
        b = (a - 1) // 1461
        c = a - 1461 * b
        d = (c - 1) // 365
        e = c - 365 * d
        month = (5 * e + 308) // 153 - 2
        day = e - (153 * month + 3) // 5 + 1
        year = 4 * b + d - 4716
        
        if month > 12:
            month -= 12
            year += 1
            
        return day, month, year
    
    @staticmethod
    def gregorian_to_julian(day: int, month: int, year: int) -> Tuple[int, int, int]:
        """Convert Gregorian date to Julian date."""
        jdn = CalendarUtils.julian_day_number(day, month, year)
        return CalendarUtils.jdn_to_julian(jdn)
    
    @staticmethod
    def julian_to_gregorian(day: int, month: int, year: int) -> Tuple[int, int, int]:
        """Convert Julian date to Gregorian date."""
        # Calculate Julian Day Number for Julian date
        if month <= 2:
            month += 12
            year -= 1
        jdn = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day - 1524
        return CalendarUtils.jdn_to_gregorian(jdn)
    
    @staticmethod
    def french_republican_to_gregorian(day: int, month: int, year: int) -> Tuple[int, int, int]:
        """
        Convert French Republican date to Gregorian date.
        
        The French Republican calendar was used from 1793-1805.
        Year 1 began on September 22, 1792 (Gregorian).
        Each year has 12 months of 30 days + 5-6 complementary days.
        """
        if year < 1 or month < 1 or month > 13 or day < 1:
            return day, month, year  # Invalid date, return as-is
        
        # Republican epoch: September 22, 1792 (Gregorian) = 1 Vendémiaire An I
        epoch_jdn = CalendarUtils.julian_day_number(22, 9, 1792)
        
        # Calculate days since epoch
        if month <= 12:
            days_in_year = (month - 1) * 30 + day - 1
        else:
            # Complementary days (month 13)
            days_in_year = 360 + day - 1
        
        # Add years (accounting for leap years)
        total_days = days_in_year
        for y in range(1, year):
            if CalendarUtils.is_french_leap_year(y):
                total_days += 366
            else:
                total_days += 365
        
        result_jdn = epoch_jdn + total_days
        return CalendarUtils.jdn_to_gregorian(result_jdn)
    
    @staticmethod
    def is_french_leap_year(french_year: int) -> bool:
        """Determine if a French Republican year is a leap year."""
        # Simplified leap year calculation
        # In reality, this follows the same pattern as Gregorian
        return french_year % 4 == 0 and (french_year % 100 != 0 or french_year % 400 == 0)
    
    @staticmethod
    def hebrew_to_gregorian(day: int, month: int, year: int) -> Tuple[int, int, int]:
        """
        Convert Hebrew date to Gregorian date.
        
        This is a simplified approximation. Full Hebrew calendar conversion
        requires complex astronomical calculations and leap month handling.
        """
        if year < 1 or month < 1 or month > 13 or day < 1:
            return day, month, year  # Invalid date, return as-is
        
        # Hebrew months (approximate lengths)
        hebrew_months = [29, 29, 29, 29, 30, 29, 30, 29, 30, 29, 30, 29]
        
        # Approximate conversion (Hebrew year 1 ≈ 3761 BCE)
        approx_gregorian_year = year - 3761
        if month <= len(hebrew_months):
            approx_month = ((month - 1) * 12 // 12) + 1
            return day, approx_month, approx_gregorian_year
        
        return day, month, approx_gregorian_year
    
    @staticmethod
    def recover_date_calendar(date: BaseDate, target_calendar: str) -> BaseDate:
        """Convert date between calendar systems."""
        if not date or date.calendar == target_calendar:
            return date
            
        converted_date = BaseDate()
        converted_date.text = date.text
        converted_date.precision = date.precision
        converted_date.calendar = target_calendar
        
        try:
            if date.calendar == "JULIAN" and target_calendar == "GREGORIAN":
                day, month, year = CalendarUtils.julian_to_gregorian(date.day, date.month, date.year)
            elif date.calendar == "GREGORIAN" and target_calendar == "JULIAN":
                day, month, year = CalendarUtils.gregorian_to_julian(date.day, date.month, date.year)
            elif date.calendar == "FRENCH" and target_calendar == "GREGORIAN":
                day, month, year = CalendarUtils.french_republican_to_gregorian(date.day, date.month, date.year)
            elif date.calendar == "HEBREW" and target_calendar == "GREGORIAN":
                day, month, year = CalendarUtils.hebrew_to_gregorian(date.day, date.month, date.year)
            else:
                # Unsupported conversion
                return date
                
            converted_date.day = day
            converted_date.month = month
            converted_date.year = year
            return converted_date
            
        except Exception:
            # If conversion fails, return original
            return date
