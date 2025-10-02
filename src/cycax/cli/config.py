from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    cycax_config: Path = Path("~/.config/cycax/config.json")
    model_config = SettingsConfigDict(validate_assignment=True, extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        cycax_config = init_settings.init_kwargs.get("cycax_config")
        return (
            env_settings,
            init_settings,
            JsonConfigSettingsSource(settings_cls=settings_cls, json_file=cycax_config),
        )

    def save(self):
        """A convenience method on the setting module to save the config."""
        self.cycax_config.parent.mkdir(parents=True, exist_ok=True)
        self.cycax_config.write_text(self.model_dump_json())
