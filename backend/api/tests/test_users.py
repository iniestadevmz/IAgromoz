"""
Tests for the User model.

# Feature: api-refactor-expansion, Property 5: can_sell is always consistent with role
"""
import pytest
from unittest.mock import patch
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from api.models.users import User


# ---------------------------------------------------------------------------
# Property 5: can_sell is always consistent with role
# Validates: Requirements 3.4, 3.5
# ---------------------------------------------------------------------------

@given(st.sampled_from(['ADMIN', 'NORMAL', 'PRODUCER', 'SELLER']))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_can_sell_consistent_with_role(role):
    """
    # Feature: api-refactor-expansion, Property 5: can_sell is always consistent with role

    For any user, after calling save(), can_sell must be True if and only if
    role is PRODUCER or SELLER. For any other role (NORMAL, ADMIN), can_sell
    must be False.

    Validates: Requirements 3.4, 3.5
    """
    user = User(email=f"test_{role.lower()}@example.com", role=role)

    # Patch the parent save() to avoid DB writes while still exercising the
    # save() override logic that sets can_sell.
    with patch("django.db.models.Model.save", return_value=None):
        user.save()

    expected = role in ('PRODUCER', 'SELLER')
    assert user.can_sell == expected, (
        f"Expected can_sell={expected} for role={role}, got can_sell={user.can_sell}"
    )
