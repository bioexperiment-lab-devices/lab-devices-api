from lab_devices.core.history import DeviceHistory


class TestDeviceHistory:
    def test_initial_state_is_none(self) -> None:
        history = DeviceHistory()
        assert history.current_state() is None

    def test_start_state(self) -> None:
        history = DeviceHistory()
        state = history.start_state("rotating", {"direction": "left", "speed": 5.0})
        assert state.name == "rotating"
        assert state.params["direction"] == "left"
        assert state.ended_at is None
        assert history.current_state() == state

    def test_start_new_state_ends_previous(self) -> None:
        history = DeviceHistory()
        first = history.start_state("rotating")
        second = history.start_state("idle")
        assert first.ended_at is not None
        assert second.ended_at is None
        assert history.current_state() == second

    def test_end_current_state(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.end_current_state()
        assert history.current_state() is None

    def test_end_current_state_when_none(self) -> None:
        history = DeviceHistory()
        history.end_current_state()  # Should not raise

    def test_record_event(self) -> None:
        history = DeviceHistory()
        event = history.record_event("get_temperature", {"temperature_c": 23.5})
        assert event.name == "get_temperature"
        assert event.params["temperature_c"] == 23.5

    def test_get_states_all(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.start_state("idle")
        assert len(history.get_states()) == 2

    def test_get_states_by_name(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating")
        history.start_state("idle")
        history.start_state("rotating")
        assert len(history.get_states("rotating")) == 2

    def test_get_events_all(self) -> None:
        history = DeviceHistory()
        history.record_event("get_temperature")
        history.record_event("get_od")
        assert len(history.get_events()) == 2

    def test_get_events_by_name(self) -> None:
        history = DeviceHistory()
        history.record_event("get_temperature")
        history.record_event("get_od")
        history.record_event("get_temperature")
        assert len(history.get_events("get_temperature")) == 2

    def test_export(self) -> None:
        history = DeviceHistory()
        history.start_state("rotating", {"speed": 5.0})
        history.record_event("get_temperature", {"temperature_c": 23.5})
        exported = history.export()
        assert "states" in exported
        assert "events" in exported
        assert len(exported["states"]) == 1
        assert len(exported["events"]) == 1
