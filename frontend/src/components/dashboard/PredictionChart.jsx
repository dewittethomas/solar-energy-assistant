import { LineChart as LineChartIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function PredictionTooltip({ active, label, payload }) {
  if (!active || !payload?.length) {
    return null
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      <strong>{payload[0].value} kW</strong>
    </div>
  )
}

export function PredictionChart({ data }) {
  const { t } = useTranslation()

  return (
    <section className="chart-panel" aria-labelledby="prediction-title">
      <div className="chart-header">
        <div>
          <p className="eyebrow">{t('dashboard.prediction.eyebrow')}</p>
        </div>
        <span>
          <LineChartIcon size={17} strokeWidth={2.2} />
          {t('dashboard.prediction.meta')}
        </span>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer height={320} width="100%">
          <ComposedChart data={data} margin={{ top: 24, right: 26, bottom: 14, left: 0 }}>
            <defs>
              <linearGradient id="predictionRechartsGradient" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#004a7f" stopOpacity="0.1" />
                <stop offset="100%" stopColor="#004a7f" stopOpacity="0.01" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(0, 74, 127, .08)" vertical={false} />
            <XAxis
              axisLine={false}
              dataKey="label"
              interval={4}
              tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 600 }}
              tickLine={false}
              tickMargin={12}
            />
            <YAxis
              axisLine={false}
              domain={[0, 7]}
              tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 600 }}
              tickCount={5}
              tickLine={false}
              tickMargin={10}
              width={34}
            />
            <Tooltip content={<PredictionTooltip />} cursor={{ stroke: 'rgba(0, 74, 127, .16)' }} />
            <Area dataKey="value" fill="url(#predictionRechartsGradient)" stroke="none" type="monotone" />
            <Line
              activeDot={{ fill: '#004a7f', r: 4, stroke: 'white', strokeWidth: 2 }}
              dataKey="value"
              dot={false}
              stroke="#004a7f"
              strokeLinecap="round"
              strokeWidth={2}
              type="monotone"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
