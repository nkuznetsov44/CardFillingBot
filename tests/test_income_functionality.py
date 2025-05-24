#!/usr/bin/env python3
"""
Test suite for income functionality
Uses pytest framework for better test organization and reporting
"""

import pytest
from datetime import datetime

from parsers.income import income_command_regexp
from entities import Income, Currency, UserSumOverPeriod, Month
from formatters import (
    format_income_confirmed, 
    format_income_list_as_table, 
    format_by_user_income_block, 
    format_user_income,
    get_max_income_table_desc_width
)
from callbacks import Callback


class TestIncomeRegex:
    """Test income command regex pattern matching"""
    
    @pytest.mark.regex
    @pytest.mark.parametrize("command,should_match,expected_groups", [
        # Basic commands (existing functionality)
        ("/income 1000 salary", True, ("1000", "", None, "salary")),
        ("/income 1500e freelance", True, ("1500", "e", None, "freelance")),
        ("/income 2000r bonus", True, ("2000", "r", None, "bonus")),
        ("/income 500.50 part time", True, ("500.50", "", None, "part time")),
        ("/income 1,500 consulting", True, ("1,500", "", None, "consulting")),
        ("/income 3000", True, ("3000", "", None, None)),
        
        # Commands with dates (new functionality)
        ("/income 1000 2025-01-01 salary", True, ("1000", "", "2025-01-01", "salary")),
        ("/income 1500e 2024-12-25 freelance", True, ("1500", "e", "2024-12-25", "freelance")),
        ("/income 2000r 2023-06-15 bonus", True, ("2000", "r", "2023-06-15", "bonus")),
        ("/income 500.50 2025-03-10", True, ("500.50", "", "2025-03-10", None)),
        
        # Invalid commands
        ("income 1000", False, None),  # Missing /
        ("/expense 1000", False, None),  # Wrong command
        ("/income", False, None),  # Missing amount
        ("/income 1000 25-01-01 bad date", True, ("1000", "", None, "25-01-01 bad date")),  # Invalid date format
    ])
    def test_income_command_regex(self, command, should_match, expected_groups):
        """Test that income command regex matches correctly"""
        match = income_command_regexp.match(command)
        
        if should_match:
            assert match is not None, f"Command '{command}' should match but didn't"
            amount, currency, date_str, desc = match.groups()
            expected_amount, expected_currency, expected_date, expected_desc = expected_groups
            
            assert amount == expected_amount
            # Convert empty strings to empty for comparison (regex returns empty string for unmatched optional groups)
            assert currency == expected_currency
            assert date_str == expected_date  
            assert desc == expected_desc
        else:
            assert match is None, f"Command '{command}' should not match but did"

    @pytest.mark.regex
    @pytest.mark.parametrize("amount_str,expected_currency", [
        ("1000r", Currency.RUB),
        ("1000р", Currency.RUB),
        ("1000e", Currency.EUR),
        ("1000е", Currency.EUR),
        ("1000R", Currency.RUB),
        ("1000E", Currency.EUR),
    ])
    def test_currency_parsing(self, amount_str, expected_currency):
        """Test currency parsing from income commands"""
        test_command = f"/income {amount_str} test"
        match = income_command_regexp.match(test_command)
        
        assert match is not None, f"Command '{test_command}' should match"
        amount, currency_alias, date_str, desc = match.groups()
        
        assert currency_alias and currency_alias.strip(), f"Currency should be parsed from '{amount_str}'"
        parsed_currency = Currency.get_by_alias(currency_alias.lower())
        assert parsed_currency == expected_currency


class TestIncomeDateParsing:
    """Test date parsing functionality in income commands"""
    
    @pytest.mark.parsing
    @pytest.mark.parametrize("command,exp_year,exp_month,exp_day,exp_desc", [
        ("/income 1000 salary", 2024, 5, 24, "salary"),  # No date specified
        ("/income 1500 2025-01-01 new year bonus", 2025, 1, 1, "new year bonus"),  # Valid date
        ("/income 2000e 2023-12-31 end of year", 2023, 12, 31, "end of year"),  # Valid date with currency
        ("/income 1200r 2024-06-15", 2024, 6, 15, None),  # Date only, no description
        ("/income 800 25-01-01 invalid date", 2024, 5, 24, "25-01-01 invalid date"),  # Invalid date format
    ])
    def test_date_parsing(self, income_parser, mock_message, command, exp_year, exp_month, exp_day, exp_desc):
        """Test date parsing functionality"""
        message = mock_message(command)
        parsed = income_parser.parse(message)
        
        assert parsed is not None, f"Command '{command}' should parse successfully"
        
        income = parsed.data
        actual_date = income.income_date
        
        assert actual_date.year == exp_year
        assert actual_date.month == exp_month
        assert actual_date.day == exp_day
        assert income.description == exp_desc


class TestIncomeEntity:
    """Test income entity creation and properties"""
    
    @pytest.mark.unit
    def test_income_creation(self, sample_user, private_scope):
        """Test basic income entity creation"""
        income = Income(
            id=None,
            user=sample_user,
            income_date=datetime.now(),
            amount=5000.0,
            description="Test salary",
            scope=private_scope,
            currency=Currency.RUB,
            original_amount=5000.0,
            original_currency=Currency.RUB
        )
        
        assert income.amount == 5000.0
        assert income.currency == Currency.RUB
        assert income.user.username == "testuser"
        assert income.description == "Test salary"
        assert income.scope.scope_type == "PRIVATE"

    @pytest.mark.unit
    def test_income_without_currency(self, sample_user, private_scope):
        """Test income creation without currency (base currency)"""
        income = Income(
            id=None,
            user=sample_user,
            income_date=datetime.now(),
            amount=3000.0,
            description="Base currency income",
            scope=private_scope,
            currency=None,
        )
        
        assert income.amount == 3000.0
        assert income.currency is None
        assert income.description == "Base currency income"


class TestIncomeFormatting:
    """Test income formatting functions"""
    
    @pytest.mark.formatting
    def test_income_confirmation_format(self, sample_income):
        """Test income confirmation message formatting"""
        confirmation = format_income_confirmed(sample_income)
        
        assert "Доход 5000.0 дин. от @testuser: Test salary" in confirmation
        assert "(Оригинал: 5500.0 RUB)" in confirmation

    @pytest.mark.formatting
    def test_income_table_format(self, sample_income, group_scope):
        """Test income table formatting"""
        incomes = [sample_income]
        table = format_income_list_as_table(incomes, group_scope)
        
        assert "Дата" in table
        assert "Сумма" in table
        assert "Описание" in table
        assert "5000" in table
        assert "Test salary" in table

    @pytest.mark.formatting
    def test_user_income_block_format(self, sample_user, group_scope):
        """Test user income block formatting"""
        user_sum = UserSumOverPeriod(user=sample_user, amount=5000.0)
        block = format_by_user_income_block([user_sum], group_scope)
        
        assert "@testuser: 5000" in block
        assert "Всего доходов: 5000" in block

    @pytest.mark.formatting
    def test_user_income_format(self, sample_incomes, sample_user, private_scope):
        """Test format_user_income function"""
        months = [Month.january]
        year = 2024
        
        formatted_text = format_user_income(sample_incomes, sample_user, months, year, private_scope)
        
        assert "Доходы @testuser за Январь 2024:" in formatted_text
        assert "5000" in formatted_text
        assert "1500" in formatted_text


class TestIncomeTableColumnWidths:
    """Test income table column width functionality"""
    
    @pytest.mark.formatting
    def test_description_width_helper_functions(self):
        """Test helper functions for description column widths"""
        private_width = get_max_income_table_desc_width("PRIVATE")
        group_width = get_max_income_table_desc_width("GROUP")
        
        assert private_width == 15, "Private scope description width should be 15"
        assert group_width == 11, "Group scope description width should be 11"

    @pytest.mark.formatting
    def test_large_amount_display(self, sample_user, private_scope):
        """Test that large amounts display correctly in 7-character width"""
        large_income = Income(
            id=1,
            user=sample_user,
            income_date=datetime.now(),
            amount=999999.0,  # Large amount to test 7-char width
            description="Test large amount",
            scope=private_scope,
        )
        
        table = format_income_list_as_table([large_income], private_scope)
        assert "999999" in table, "Large amount should be displayed in table"

    @pytest.mark.formatting
    @pytest.mark.parametrize("scope_type,expected_width", [
        ("PRIVATE", 15),
        ("GROUP", 11),
    ])
    def test_scope_specific_widths(self, scope_type, expected_width):
        """Test that different scopes have correct description widths"""
        actual_width = get_max_income_table_desc_width(scope_type)
        assert actual_width == expected_width


class TestMyIncomeCallback:
    """Test MY_INCOME callback functionality"""
    
    @pytest.mark.unit
    def test_my_income_callback_exists(self):
        """Test that MY_INCOME callback exists"""
        assert hasattr(Callback, 'MY_INCOME'), "MY_INCOME callback should exist"
        assert Callback.MY_INCOME.value == "my_income"

    @pytest.mark.integration
    def test_format_user_income_integration(self, sample_incomes, sample_user, private_scope):
        """Test format_user_income function integration"""
        months = [Month.january]
        year = 2024
        
        formatted_text = format_user_income(sample_incomes, sample_user, months, year, private_scope)
        
        # Check that the formatted text contains expected elements
        assert len(formatted_text) > 0
        assert "Доходы" in formatted_text
        assert "@testuser" in formatted_text
        assert "2024" in formatted_text


class TestIncomeIntegration:
    """Integration tests for complete income workflow"""
    
    @pytest.mark.integration
    def test_complete_income_parsing_workflow(self, income_parser, mock_message):
        """Test complete workflow from command to income entity"""
        commands = [
            "/income 5000 salary",
            "/income 1500e 2025-01-01 new year bonus",
            "/income 2000r 2024-12-25 christmas bonus",
            "/income 800 2024-06-15",
        ]
        
        incomes = []
        for command in commands:
            message = mock_message(command)
            parsed = income_parser.parse(message)
            assert parsed is not None, f"Command '{command}' should parse successfully"
            incomes.append(parsed.data)
        
        # Verify we got all expected incomes
        assert len(incomes) == 4
        
        # Check specific properties
        assert incomes[0].amount == 5000.0
        assert incomes[0].description == "salary"
        
        assert incomes[1].amount == 1500.0
        assert incomes[1].currency == Currency.EUR
        assert incomes[1].income_date.year == 2025
        
        assert incomes[2].currency == Currency.RUB
        assert incomes[2].income_date.month == 12
        
        assert incomes[3].description is None  # No description provided

    @pytest.mark.integration
    def test_error_handling_integration(self, income_parser, mock_message):
        """Test error handling in parsing workflow"""
        invalid_commands = [
            "income 1000",  # Missing /
            "/expense 1000",  # Wrong command
            "/income",  # Missing amount
        ]
        
        for command in invalid_commands:
            message = mock_message(command)
            parsed = income_parser.parse(message)
            assert parsed is None, f"Invalid command '{command}' should not parse"

    @pytest.mark.integration
    def test_table_formatting_integration(self, income_parser, mock_message, private_scope, group_scope):
        """Test table formatting with parsed incomes"""
        commands = [
            "/income 50000 big salary",
            "/income 1500e 2025-01-01 bonus",
            "/income 999999 2024-06-15 huge amount",
        ]
        
        incomes = []
        for command in commands:
            message = mock_message(command)
            parsed = income_parser.parse(message)
            assert parsed is not None
            incomes.append(parsed.data)
        
        # Test both scope types
        private_table = format_income_list_as_table(incomes, private_scope)
        group_table = format_income_list_as_table(incomes, group_scope)
        
        # Verify tables contain expected data
        for table in [private_table, group_table]:
            assert "50000" in table
            assert "1500" in table
            assert "999999" in table
            assert "big salary" in table
            assert "bonus" in table
        
        # Verify different widths for different scopes
        assert len(private_table.split('\n')[0]) >= len(group_table.split('\n')[0]) 