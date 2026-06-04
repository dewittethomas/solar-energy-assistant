import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function MiniTooltip({ active, label, payload, unit }) {
  if (!active || !payload?.length) {
    return null
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      <strong>{Number(payload[0].value).toFixed(1)} {unit}</strong>
    </div>
  )
}

export function ProductionMiniChart({ data, height = 260, unit = 'kWh', xAxisLabel, yAxisLabel = `Productie (${unit})` }) {
  return (
    <div className="mini-chart-wrap">
      <ResponsiveContainer height={height} width="100%">
        <BarChart data={data} margin={{ top: 18, right: 14, bottom: xAxisLabel ? 26 : 8, left: 6 }}>
          <CartesianGrid stroke="rgba(15, 61, 94, .08)" vertical={false} />
          <XAxis
            axisLine={false}
            dataKey="label"
            label={
              xAxisLabel
                ? {
                    value: xAxisLabel,
                    position: 'insideBottom',
                    offset: -18,
                    fill: 'var(--text-muted)',
                    fontSize: 12,
                    fontWeight: 600,
                  }
                : undefined
            }
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickLine={false}
          />
          <YAxis
            axisLine={false}
            label={{
              value: yAxisLabel,
              angle: -90,
              position: 'insideLeft',
              fill: 'var(--text-muted)',
              fontSize: 12,
              fontWeight: 600,
            }}
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<MiniTooltip unit={unit} />} cursor={{ fill: 'rgba(245, 166, 35, .08)' }} />
          <Bar dataKey="value" fill="var(--color-solar)" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
