from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource


class DiscoveryConfig(BaseModel):
    extra_ports: list[str] = []
    timeout_s: float = 1.0
    baudrate: int = 9600


class DensitometerConfig(BaseModel):
    measurement_delay_s: float = 2.0


class DevicesConfig(BaseModel):
    densitometer: DensitometerConfig = DensitometerConfig()


class AppConfig(BaseSettings):
    discovery: DiscoveryConfig = DiscoveryConfig()
    devices: DevicesConfig = DevicesConfig()
    yaml_file: str = "config.yaml"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        init_kwargs = init_settings.init_kwargs
        yaml_file = Path(init_kwargs.get("yaml_file", "config.yaml"))
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file),
            env_settings,
        )
