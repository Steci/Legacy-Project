"""
Date grammar parser for GEDCOM dates.
Extracted from main parser to reduce cyclomatic complexity while preserving OCaml compatibility.
"""
from typing import List, Tuple, Optional
from ..common.base_models import BaseDate, DatePrecision
from .calendar_utils import CalendarUtils


class DateGrammarParser:
    """Handles grammar-based parsing of GEDCOM date strings following OCaml EXTEND logic."""
    
    @staticmethod
    def tokenize_date(date_str: str) -> List[Tuple[str, str]]:
        """Tokenize date string following OCaml lexing_date logic."""
        tokens = []
        i = 0
        date_str = date_str.strip().upper()
        
        while i < len(date_str):
            if date_str[i].isspace():
                i += 1
                continue
                
            # Handle slashes and dashes
            if date_str[i] in ['/', '-']:
                tokens.append(("SLASH", date_str[i]))
                i += 1
                continue
                
            # Handle parentheses  
            if date_str[i] == '(':
                tokens.append(("LPAR", "("))
                i += 1
                continue
            if date_str[i] == ')':
                tokens.append(("RPAR", ")"))
                i += 1
                continue
                
            # Handle numbers (including Roman numerals)
            if date_str[i].isdigit():
                num_str = ""
                while i < len(date_str) and date_str[i].isdigit():
                    num_str += date_str[i]
                    i += 1
                tokens.append(("INT", num_str))
                continue
                
            # Handle Roman numerals
            if date_str[i:i+3] in ["III", "VII", "VIII"]:
                tokens.append(("INT", str(DateGrammarParser._roman_to_int(date_str[i:i+3]))))
                i += 3
                continue
            elif date_str[i:i+2] in ["II", "IV", "VI", "IX", "XI", "XII"]:
                tokens.append(("INT", str(DateGrammarParser._roman_to_int(date_str[i:i+2]))))
                i += 2
                continue
            elif date_str[i] in ["I", "V", "X"]:
                # Check if it's part of a longer sequence
                roman_str = ""
                j = i
                while j < len(date_str) and date_str[j] in "IVXLCDM":
                    roman_str += date_str[j]
                    j += 1
                if len(roman_str) > 1 or (len(roman_str) == 1 and date_str[i] in ["I", "V", "X"]):
                    roman_val = DateGrammarParser._roman_to_int(roman_str)
                    if roman_val > 0:
                        tokens.append(("INT", str(roman_val)))
                        i = j
                        continue
                        
            # Handle identifiers (words, calendar prefixes, etc.)
            if date_str[i].isalpha() or date_str[i] == '@':
                word = ""
                while i < len(date_str) and (date_str[i].isalpha() or date_str[i] in ['@', '_']):
                    word += date_str[i]
                    i += 1
                tokens.append(("ID", word))
                continue
                
            # Skip unknown characters
            i += 1
            
        return tokens
    
    @staticmethod
    def _roman_to_int(roman: str) -> int:
        """Convert Roman numeral to integer."""
        roman_values = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }
        
        total = 0
        prev_value = 0
        
        for char in reversed(roman):
            value = roman_values.get(char, 0)
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value
            
        return total if total <= 12 else 0  # Only return valid month values
    
    @staticmethod
    def parse_date_grammar(tokens: List[Tuple[str, str]]) -> Optional[BaseDate]:
        """Parse date using grammar rules following OCaml EXTEND date_value logic."""
        if not tokens:
            return None
            
        parser = DateGrammarParser._GrammarState(tokens)
        return parser.parse_date_or_text()
    
    class _GrammarState:
        """Internal state for grammar parsing."""
        
        def __init__(self, tokens: List[Tuple[str, str]]):
            self.tokens = tokens
            self.pos = 0
        
        def peek(self) -> Tuple[str, str]:
            return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOI", "")
        
        def consume(self) -> Tuple[str, str]:
            if self.pos < len(self.tokens):
                token = self.tokens[self.pos]
                self.pos += 1
                return token
            return ("EOI", "")
        
        def parse_date_or_text(self) -> Optional[BaseDate]:
            """Parse date_or_text production."""
            token_type, token_value = self.peek()
            
            # Handle date intervals and modifiers
            if token_type == "ID":
                return self._parse_date_modifier(token_value)
            
            # Handle calendar prefixes
            if token_value in ["@#DJULIAN@", "@#DGREGORIAN@", "@#DFRENCH@", "@#DHEBREW@"]:
                return self._parse_calendar_date()
            
            # Handle simple date patterns
            return self._parse_simple_date()
        
        def _parse_date_modifier(self, modifier: str) -> Optional[BaseDate]:
            """Parse date modifiers (BEF, AFT, ABT, etc.)."""
            if modifier == "BEF":
                self.consume()
                date = self.parse_date_or_text()
                if date:
                    date.precision = DatePrecision.BEFORE
                return date
            elif modifier == "AFT":
                self.consume()
                date = self.parse_date_or_text()
                if date:
                    date.precision = DatePrecision.AFTER
                return date
            elif modifier in ["ABT", "ABOUT", "CAL", "EST"]:
                self.consume()
                date = self.parse_date_or_text()
                if date:
                    date.precision = DatePrecision.ABOUT
                return date
            elif modifier == "BET":
                return self._parse_between_dates()
            elif modifier in ["FROM", "TO"]:
                return self._parse_range_dates()
            else:
                # Regular date parsing
                return self._parse_simple_date()
        
        def _parse_calendar_date(self) -> Optional[BaseDate]:
            """Parse calendar-prefixed dates."""
            calendar_token = self.consume()
            _, calendar_value = calendar_token
            
            # Extract calendar type
            calendar = "GREGORIAN"  # Default
            if "JULIAN" in calendar_value:
                calendar = "JULIAN"
            elif "FRENCH" in calendar_value:
                calendar = "FRENCH"
            elif "HEBREW" in calendar_value:
                calendar = "HEBREW"
            
            # Parse the actual date
            date = self._parse_simple_date()
            if date:
                date.calendar = calendar
            return date
        
        def _parse_simple_date(self) -> Optional[BaseDate]:
            """Parse simple date patterns (day/month/year combinations)."""
            date = BaseDate()
            
            # Try to parse day, month, year in various combinations
            token_type, token_value = self.peek()
            
            if token_type == "INT":
                # Could be day, month, or year
                first_num = int(self.consume()[1])
                
                token_type, token_value = self.peek()
                if token_type == "ID":
                    # Pattern: number month [year]
                    month_str = self.consume()[1]
                    month = CalendarUtils.parse_month(month_str)
                    if month > 0:
                        date.day = first_num
                        date.month = month
                        
                        # Check for year
                        token_type, token_value = self.peek()
                        if token_type == "INT":
                            date.year = int(self.consume()[1])
                        return date
                        
                elif token_type == "SLASH":
                    # Pattern: day/month/year or month/day/year
                    self.consume()  # consume slash
                    token_type, token_value = self.peek()
                    if token_type == "INT":
                        second_num = int(self.consume()[1])
                        
                        # Check for third number
                        token_type, token_value = self.peek()
                        if token_type == "SLASH":
                            self.consume()  # consume second slash
                            token_type, token_value = self.peek()
                            if token_type == "INT":
                                third_num = int(self.consume()[1])
                                
                                # Determine if it's DD/MM/YYYY or MM/DD/YYYY
                                if first_num <= 12 and second_num <= 31:
                                    # Ambiguous - use MM/DD/YYYY (US format)
                                    date.month = first_num
                                    date.day = second_num
                                    date.year = third_num
                                else:
                                    # DD/MM/YYYY
                                    date.day = first_num
                                    date.month = second_num
                                    date.year = third_num
                                return date
                        else:
                            # Just MM/DD or DD/MM
                            if first_num <= 12:
                                date.month = first_num
                                date.day = second_num
                            else:
                                date.day = first_num
                                date.month = second_num
                            return date
                            
                elif token_type == "INT":
                    # Two or three numbers in sequence
                    second_num = int(self.consume()[1])
                    token_type, token_value = self.peek()
                    if token_type == "INT":
                        third_num = int(self.consume()[1])
                        # Assume DD MM YYYY format
                        date.day = first_num
                        date.month = second_num
                        date.year = third_num
                        return date
                    else:
                        # Just two numbers - assume MM YYYY
                        date.month = first_num
                        date.year = second_num
                        return date
                else:
                    # Just a single number - could be year
                    if first_num > 31:
                        date.year = first_num
                    else:
                        date.day = first_num
                    return date
                    
            elif token_type == "ID":
                # Month name first
                month_str = self.consume()[1]
                month = CalendarUtils.parse_month(month_str)
                if month > 0:
                    date.month = month
                    
                    # Check for day/year
                    token_type, token_value = self.peek()
                    if token_type == "INT":
                        num = int(self.consume()[1])
                        if num <= 31:
                            date.day = num
                            # Check for year
                            token_type, token_value = self.peek()
                            if token_type == "INT":
                                date.year = int(self.consume()[1])
                        else:
                            date.year = num
                    return date
            
            # If we get here, couldn't parse - return empty date
            return date if date.day or date.month or date.year else None
        
        def _parse_between_dates(self) -> Optional[BaseDate]:
            """Parse BET date1 AND date2 pattern."""
            self.consume()  # consume BET
            
            start_date = self.parse_date_or_text()
            
            # Look for AND
            token_type, token_value = self.peek()
            if token_type == "ID" and token_value == "AND":
                self.consume()  # consume AND
                end_date = self.parse_date_or_text()
                
                if start_date:
                    start_date.precision = DatePrecision.BETWEEN
                    # Could store end_date in a range field if needed
                    return start_date
            
            return start_date
        
        def _parse_range_dates(self) -> Optional[BaseDate]:
            """Parse FROM/TO date patterns."""
            range_type = self.consume()[1]  # FROM or TO
            
            date = self.parse_date_or_text()
            if date:
                if range_type == "FROM":
                    date.precision = DatePrecision.AFTER
                else:  # TO
                    date.precision = DatePrecision.BEFORE
            
            return date
