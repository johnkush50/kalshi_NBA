"""
Supabase client initialization and connection management.

Provides a singleton Supabase client instance for database operations.
Uses async patterns for optimal performance.
"""

from supabase import create_client, Client
from typing import Optional
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Supabase Client Singleton
# ============================================================================

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create the Supabase client instance (singleton pattern).

    Returns:
        Client: The Supabase client instance.

    Raises:
        ValueError: If Supabase credentials are not configured.
    """
    global _supabase_client

    if _supabase_client is None:
        try:
            if not settings.supabase_url or not settings.supabase_service_key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file."
                )

            _supabase_client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_key
            )

            logger.info("Supabase client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}", exc_info=True)
            raise

    return _supabase_client


def reset_supabase_client() -> None:
    """
    Reset the Supabase client instance.

    Useful for testing or reconnection scenarios.
    """
    global _supabase_client
    _supabase_client = None
    logger.info("Supabase client reset")


# ============================================================================
# Database Helper Functions
# ============================================================================

async def check_connection() -> bool:
    """
    Check if the Supabase connection is working.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        client = get_supabase_client()
        # Try a simple query to verify connection
        result = client.table("games").select("id").limit(1).execute()
        logger.info("Supabase connection check successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}", exc_info=True)
        return False


async def get_table(table_name: str):
    """
    Get a reference to a Supabase table.

    Args:
        table_name: Name of the table to access.

    Returns:
        Table reference for querying.
    """
    client = get_supabase_client()
    return client.table(table_name)


# ============================================================================
# Export commonly used client
# ============================================================================

# For convenience, export the function to get client
supabase = get_supabase_client
