from models.installation_configuration import ConsumingActivity
from services.consuming_activity_catalog import ConsumingActivityCatalog


class ConsumingActivitySeeder:
    def __init__(
        self,
        activity_catalog: ConsumingActivityCatalog | None = None,
    ) -> None:
        self.activity_catalog = activity_catalog or ConsumingActivityCatalog()

    def seed(
        self,
        activities: list[dict[str, object]] | None,
    ) -> tuple[list[ConsumingActivity], bool]:
        defaults = self.activity_catalog.list_defaults()
        default_by_id = {
            str(activity.id): activity
            for activity in defaults
            if activity.id
        }
        default_by_name = {
            self._normalize_key(activity.name): activity
            for activity in defaults
        }

        if not activities:
            return defaults, True

        changed = False
        seeded: list[ConsumingActivity] = []

        for raw_activity in activities:
            key = str(raw_activity.get('id') or '').strip()
            name = str(raw_activity.get('name') or '').strip()
            normalized_key = self._normalize_key(key)
            normalized_name = self._normalize_key(name)
            default_activity = (
                default_by_id.get(key)
                or default_by_id.get(normalized_key)
                or default_by_name.get(normalized_name)
            )

            seeded_activity = ConsumingActivity(
                id=key or (default_activity.id if default_activity else None),
                name=name or (
                    default_activity.name if default_activity else 'Activity'
                ),
                consumption_kwh=float(
                    raw_activity.get('consumption_kwh')
                    or (
                        default_activity.consumption_kwh
                        if default_activity else 0
                    )
                ),
                duration_minutes=(
                    int(raw_activity['duration_minutes'])
                    if raw_activity.get('duration_minutes') is not None
                    else (
                        default_activity.duration_minutes
                        if default_activity else 60
                    )
                ),
                category=str(
                    raw_activity.get('category')
                    or (
                        default_activity.category
                        if default_activity else 'custom'
                    )
                ),
                is_custom=bool(raw_activity.get('is_custom', not default_activity)),
            )
            seeded.append(seeded_activity)

            if (
                seeded_activity.id != raw_activity.get('id')
                or seeded_activity.name != raw_activity.get('name')
                or seeded_activity.duration_minutes
                != raw_activity.get('duration_minutes')
                or seeded_activity.category != raw_activity.get('category')
            ):
                changed = True

        existing_ids = {
            str(activity.id)
            for activity in seeded
            if activity.id
        }

        for default_activity in defaults:
            if default_activity.id in existing_ids:
                continue

            seeded.append(default_activity)
            changed = True

        return seeded, changed

    def _normalize_key(self, value: str) -> str:
        normalized = value.strip().lower().replace('-', '_').replace(' ', '_')
        aliases = {
            'car': 'ev_charging',
            'electric_vehicle': 'ev_charging',
            'electric_car': 'ev_charging',
        }
        return aliases.get(normalized, normalized)
