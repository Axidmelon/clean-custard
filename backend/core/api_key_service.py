# API Key generation and management service
import secrets
import string
from typing import Tuple
from passlib.context import CryptContext

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class APIKeyService:
    """Service for generating and managing API keys for Custard agents."""

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate a new API key and its hashed version.

        Returns:
            Tuple[str, str]: (plain_api_key, hashed_api_key)
        """
        # Generate a secure random API key
        # Format: custard_agent_<random_string>
        random_part = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )
        plain_api_key = f"custard_agent_{random_part}"

        # Hash the API key for secure storage
        hashed_api_key = pwd_context.hash(plain_api_key)

        return plain_api_key, hashed_api_key

    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """
        Verify if a plain API key matches its hashed version.

        Args:
            plain_key: The plain text API key
            hashed_key: The hashed API key stored in database

        Returns:
            bool: True if the keys match, False otherwise
        """
        return pwd_context.verify(plain_key, hashed_key)

    @staticmethod
    def generate_agent_key() -> str:
        """
        Generate a shorter agent identifier key.
        This is used for agent identification in WebSocket connections.

        Returns:
            str: A short agent key
        """
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
