import { LineChart as LineChartIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function PredictionTooltip({ active, label, payload, labelText, unit }) {
  if (!active || !payload?.length) {
    return null
  }

  const forecast = payload.find((item) => item.dataKey === 'value')

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      {forecast && (
        <>
          <small>{labelText}</small>
          <strong>{Number(forecast.value).toFixed(unit === 'W' ? 0 : 1)} {unit}</strong>
        </>
      )}
    </div>
  )
}

export function PredictionChart({ className = '', data, unit = 'kW' }) {
  const { t } = useTranslation()
  const maxDisplayValue = unit === 'W' ? 50000 : 50
  const safeData = data
    .filter((entry) => Number.isFinite(Number(entry?.value)))
    .map((entry) => ({ ...entry, value: Number(entry.value) }))
    .filter((entry) => entry.value >= 0 && entry.value <= maxDisplayValue)

  return (
    <section className={className ? `chart-panel ${className}` : 'chart-panel'} aria-labelledby="prediction-title">
      <div className="chart-header">
        <div>
          <p className="eyebrow">{t('dashboard.prediction.eyebrow')}</p>
          <h2 id="prediction-title">{t('dashboard.prediction.chartTitle')}</h2>
        </div>
        <span>
          <LineChartIcon size={17} strokeWidth={2.2} />
          {unit}
        </span>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer height={386} width="100%">
          <ComposedChart data={safeData} margin={{ top: 22, right: 24, bottom: 38, left: 18 }}>
            <defs>
              <linearGradient id="predictionRechartsGradient" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="var(--color-solar)" stopOpacity="0.18" />
                <stop offset="100%" stopColor="var(--color-solar)" stopOpacity="0.02" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(17, 24, 39, .06)" vertical={false} />
            <XAxis
              axisLine={false}
              dataKey="label"
              interval="preserveStartEnd"
              label={{
                value: t('dashboard.prediction.xAxis'),
                position: 'insideBottom',
                offset: -18,
                fill: 'var(--text-muted)',
                fontSize: 12,
                fontWeight: 600,
              }}
              tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 500 }}
              tickFormatter={formatAxisLabel}
              tickLine={false}
              tickMargin={12}
            />
            <YAxis
              axisLine={false}
              domain={[0, (dataMax) => Math.max(1, Math.ceil(Number(dataMax || 0) + 0.5))]}
              label={{
                value: t('dashboard.prediction.yAxis', { unit }),
                angle: -90,
                position: 'insideLeft',
                fill: 'var(--text-muted)',
                fontSize: 12,
                fontWeight: 600,
              }}
              tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 500 }}
              tickCount={5}
              tickFormatter={(value) =>
                Number(value)
                  .toFixed(unit === 'W' || value >= 10 ? 0 : 1)
                  .replace(/\.0$/, '')
              }
              tickLine={false}
              tickMargin={10}
              width={44}
            />
            <Tooltip
              content={<PredictionTooltip labelText={t('dashboard.prediction.tooltipLabel')} unit={unit} />}
              cursor={{ stroke: 'rgba(216, 137, 0, .2)' }}
            />
            <Legend align="right" iconType="circle" verticalAlign="top" wrapperStyle={{ fontSize: 12, fontWeight: 600 }} />
            <Area dataKey="value" fill="url(#predictionRechartsGradient)" legendType="none" stroke="none" type="monotone" />
            <Line
              activeDot={{ fill: 'var(--color-solar)', r: 4, stroke: 'white', strokeWidth: 2 }}
              dataKey="value"
              dot={false}
              name={t('dashboard.prediction.forecast')}
              stroke="var(--color-solar-strong)"
              strokeLinecap="round"
              strokeWidth={2.2}
              type="monotone"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

function formatAxisLabel(label) {
  const parts = String(label).split(' ')
  if (parts.length <= 2) {
    return String(label)
  }

  return `${parts[0]} ${parts[1]}`
}
