from models.installation_configuration import ConsumingActivity


class ConsumingActivityCatalog:
    def list_defaults(self) -> list[ConsumingActivity]:
        return [
            ConsumingActivity(
                id='washing_machine',
                name='Washing machine',
                consumption_kwh=1.1,
                duration_minutes=90,
                category='laundry',
                is_custom=False
            ),
            ConsumingActivity(
                id='dishwasher',
                name='Dishwasher',
                consumption_kwh=1.2,
                duration_minutes=90,
                category='kitchen',
                is_custom=False
            ),
            ConsumingActivity(
                id='dryer',
                name='Dryer',
                consumption_kwh=2.5,
                duration_minutes=120,
                category='laundry',
                is_custom=False
            ),
            ConsumingActivity(
                id='boiler',
                name='Boiler',
                consumption_kwh=3.0,
                duration_minutes=180,
                category='heating',
                is_custom=False
            ),
            ConsumingActivity(
                id='ev_charging',
                name='EV charging',
                consumption_kwh=7.0,
                duration_minutes=180,
                category='mobility',
                is_custom=False
            ),
        ]
