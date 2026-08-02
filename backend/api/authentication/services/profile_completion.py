"""
ProfileCompletionService
========================
Verifica quais campos obrigatórios faltam para cada tipo de utilizador.
Escalável — basta adicionar uma entrada em REQUIRED_FIELDS_BY_ROLE.
"""


# Campos obrigatórios por role
REQUIRED_FIELDS_BY_ROLE = {
    'NORMAL': ['first_name', 'last_name'],
    'PRODUCER': ['first_name', 'last_name', 'district', 'phone'],
    'SELLER': ['first_name', 'last_name', 'district', 'phone'],
    'ADMIN': [],
}

# Campos obrigatórios nos sub-perfis
REQUIRED_SELLER_PROFILE_FIELDS = ['store_name', 'contact', 'seller_type', 'store_address']
REQUIRED_PRODUCER_PROFILE_FIELDS = ['contact', 'farm_address']


class ProfileCompletionService:

    @classmethod
    def check(cls, user) -> dict:
        """
        Retorna:
        {
            "profile_completed": bool,
            "missing_fields": [...],
            "required_profile": "NORMAL"|"PRODUCER"|"SELLER"|"ADMIN"
        }
        """
        missing = []
        role = user.role

        # Campos no modelo User
        for field in REQUIRED_FIELDS_BY_ROLE.get(role, []):
            value = getattr(user, field, None)
            if not value:
                missing.append(field)

        # Campos no sub-perfil
        if role == 'SELLER':
            try:
                profile = user.seller_profile
                for f in REQUIRED_SELLER_PROFILE_FIELDS:
                    if not getattr(profile, f, None):
                        missing.append(f'seller_profile.{f}')
            except Exception:
                missing.extend([f'seller_profile.{f}' for f in REQUIRED_SELLER_PROFILE_FIELDS])

        elif role == 'PRODUCER':
            try:
                profile = user.producer_profile
                for f in REQUIRED_PRODUCER_PROFILE_FIELDS:
                    if not getattr(profile, f, None):
                        missing.append(f'producer_profile.{f}')
            except Exception:
                missing.extend([f'producer_profile.{f}' for f in REQUIRED_PRODUCER_PROFILE_FIELDS])

        completed = len(missing) == 0

        # Persistir se mudou
        if user.profile_completed != completed:
            user.profile_completed = completed
            user.save(update_fields=['profile_completed', 'updated_at'])

        return {
            'profile_completed': completed,
            'missing_fields': missing,
            'required_profile': role,
        }
