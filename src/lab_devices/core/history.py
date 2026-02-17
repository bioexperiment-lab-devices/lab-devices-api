from datetime import datetime

from lab_devices.models.events import InstantEvent, StateRecord


class DeviceHistory:
    def __init__(self) -> None:
        self._states: list[StateRecord] = []
        self._events: list[InstantEvent] = []

    def start_state(self, name: str, params: dict[str, float | str] | None = None) -> StateRecord:
        self.end_current_state()
        state = StateRecord(name=name, params=params or {})
        self._states.append(state)
        return state

    def end_current_state(self) -> None:
        current = self.current_state()
        if current is not None:
            current.ended_at = datetime.now()

    def record_event(self, name: str, params: dict[str, float | str] | None = None) -> InstantEvent:
        event = InstantEvent(name=name, params=params or {})
        self._events.append(event)
        return event

    def current_state(self) -> StateRecord | None:
        if self._states and self._states[-1].ended_at is None:
            return self._states[-1]
        return None

    def get_states(self, name: str | None = None) -> list[StateRecord]:
        if name is None:
            return list(self._states)
        return [s for s in self._states if s.name == name]

    def get_events(self, name: str | None = None) -> list[InstantEvent]:
        if name is None:
            return list(self._events)
        return [e for e in self._events if e.name == name]

    def export(self) -> dict[str, list[dict[str, object]]]:
        return {
            "states": [s.model_dump() for s in self._states],
            "events": [e.model_dump() for e in self._events],
        }
