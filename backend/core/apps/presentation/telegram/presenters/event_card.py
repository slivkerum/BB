from dataclasses import dataclass
from backend.core.apps.domain.entities.event import Event
from zoneinfo import ZoneInfo
from backend.core.apps.config.settings import settings


@dataclass
class EventCardPresenter:
    def render(
        self,
        event: Event,
        going: list[tuple[int, str]],
        declined: list[tuple[int, str]],
    ) -> str:
        def mention(uid: int, name: str) -> str:
            safe = name.replace("<", "").replace(">", "")
            return f'<a href="tg://user?id={uid}">{safe}</a>'

        going_lines = [f"{mention(uid, name)} — красавчик" for uid, name in going]
        declined_lines = [f"{mention(uid, name)} — черт" for uid, name in declined]

        local = event.starts_at.astimezone(ZoneInfo(settings.TZ))
        starts = local.strftime("%Y-%m-%d %H:%M")

        parts = [
            f"<b>Событие:</b> {event.title} ({event.category})",
            f"<b>Где:</b> {event.place}",
            f"<b>Когда:</b> {starts}",
        ]
        if event.notes:
            parts.append(event.notes)

        parts.append(f"\n<b>Идут ({len(going_lines)}):</b>")
        parts.append("\n".join(going_lines) if going_lines else "—")

        parts.append(f"\n<b>Не идут ({len(declined_lines)}):</b>")
        parts.append("\n".join(declined_lines) if declined_lines else "—")

        return "\n".join(parts)
