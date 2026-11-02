from config.settings import Settings


def test_oidc_defaults_are_external_reviewer_configuration():
    settings = Settings()

    assert settings.OIDC_ROLE_CLAIM == "roles"
    assert settings.OIDC_REVIEWER_ROLE == "reviewer"
    assert settings.OIDC_ISSUER_URL is None


def test_environment_values_are_validated_and_parsed(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example.com")
    monkeypatch.setenv("OIDC_AUDIENCE", "rag-api")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://app.example.com")
    monkeypatch.setenv("DEFAULT_TOP_K", "8")

    # from_environment reads only the supported application variables and keeps
    # secrets out of source-controlled configuration.
    monkeypatch.setenv("OIDC_ROLE_CLAIM", "groups")
    settings = Settings.from_environment()

    assert settings.OIDC_ISSUER_URL == "https://issuer.example.com"
    assert settings.OIDC_AUDIENCE == "rag-api"
    assert settings.OIDC_ROLE_CLAIM == "groups"
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://app.example.com"]
    assert settings.DEFAULT_TOP_K == 8
