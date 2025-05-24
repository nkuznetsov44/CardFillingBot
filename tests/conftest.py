import sys
import os
from datetime import datetime
import pytest

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entities import User, FillScope, Currency, Income
from parsers.income import IncomeMessageParser


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        id=123456,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="en"
    )


@pytest.fixture
def private_scope():
    """Create a private scope for testing"""
    return FillScope(
        scope_id=1,
        scope_type="PRIVATE",
        chat_id=123456
    )


@pytest.fixture
def group_scope():
    """Create a group scope for testing"""
    return FillScope(
        scope_id=1,
        scope_type="GROUP",
        chat_id=123456
    )


@pytest.fixture
def sample_income(sample_user, private_scope):
    """Create a sample income for testing"""
    return Income(
        id=1,
        user=sample_user,
        income_date=datetime.now(),
        amount=5000.0,
        description="Test salary",
        scope=private_scope,
        currency=Currency.RUB,
        original_amount=5500.0,
        original_currency=Currency.RUB
    )


@pytest.fixture
def sample_incomes(sample_user, private_scope):
    """Create multiple sample incomes for testing"""
    return [
        Income(
            id=1,
            user=sample_user,
            income_date=datetime.now(),
            amount=5000.0,
            description="Salary",
            scope=private_scope,
        ),
        Income(
            id=2,
            user=sample_user,
            income_date=datetime.now(),
            amount=1500.0,
            description="Freelance",
            scope=private_scope,
        )
    ]


class MockUser:
    def __init__(self):
        self.id = 123
        self.is_bot = False
        self.first_name = "Test"
        self.last_name = "User"
        self.username = "testuser"
        self.language_code = "en"


class MockChat:
    def __init__(self):
        self.id = 456


class MockMessage:
    def __init__(self, text):
        self.text = text
        self.from_user = MockUser()
        self.chat = MockChat()
        self.date = datetime(2024, 5, 24, 15, 30, 45)  # Fixed date for testing


class MockCardFillService:
    def get_scope(self, chat_id):
        return FillScope(scope_id=1, scope_type="PRIVATE", chat_id=chat_id)


@pytest.fixture
def mock_message():
    """Create a mock message factory"""
    return MockMessage


@pytest.fixture
def income_parser():
    """Create an income parser with mock service"""
    return IncomeMessageParser(MockCardFillService()) 