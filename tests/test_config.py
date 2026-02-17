import os
import tempfile

from lab_devices.config import AppConfig, DensitometerConfig, DevicesConfig, DiscoveryConfig


class TestDiscoveryConfig:
    def test_defaults(self) -> None:
        config = DiscoveryConfig()
        assert config.extra_ports == []
        assert config.timeout_s == 1.0
        assert config.baudrate == 9600


class TestDensitometerConfig:
    def test_defaults(self) -> None:
        config = DensitometerConfig()
        assert config.measurement_delay_s == 2.0


class TestDevicesConfig:
    def test_defaults(self) -> None:
        config = DevicesConfig()
        assert config.densitometer.measurement_delay_s == 2.0


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig(yaml_file="nonexistent.yaml")
        assert config.discovery.timeout_s == 1.0
        assert config.devices.densitometer.measurement_delay_s == 2.0

    def test_from_yaml(self) -> None:
        yaml_content = """
discovery:
  extra_ports:
    - /dev/ttyUSB0
  timeout_s: 0.5
  baudrate: 115200

devices:
  densitometer:
    measurement_delay_s: 3.0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            try:
                config = AppConfig(yaml_file=f.name)
                assert config.discovery.extra_ports == ["/dev/ttyUSB0"]
                assert config.discovery.timeout_s == 0.5
                assert config.discovery.baudrate == 115200
                assert config.devices.densitometer.measurement_delay_s == 3.0
            finally:
                os.unlink(f.name)
