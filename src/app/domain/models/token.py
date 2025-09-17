class Token:
    expires_at   : float      = 0.0
    access_token : str | None = None
    refresh_token: str | None = None
    person_urn   : str | None = None

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token)
