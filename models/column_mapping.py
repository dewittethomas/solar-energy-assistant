from dataclasses import dataclass

@dataclass
class ColumnMapping:
    date_column: str
    time_column: str | None
    measurement_column: str
    unit: str

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> 'ColumnMapping':
        date_column = payload.get('date_column')
        time_column = payload.get('time_column')
        measurement_column = payload.get('measurement_column')
        unit = payload.get('unit')

        missing_fields = [
            field
            for field, value in {
                'date_column': date_column,
                'measurement_column': measurement_column,
                'unit': unit
            }.items()
            if not value
        ]

        if missing_fields:
            raise ValueError(
                f'Missing mapping field(s): {", ".join(missing_fields)}'
            )

        return cls(
            date_column=str(date_column),
            time_column=str(time_column) if time_column else None,
            measurement_column=str(measurement_column),
            unit=str(unit)
        )
