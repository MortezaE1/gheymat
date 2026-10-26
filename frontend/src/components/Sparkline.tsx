interface Props {
  values: number[]
  width?: number
  height?: number
  trend: 'up' | 'down' | 'flat'
}

export function Sparkline({ values, width = 96, height = 32, trend }: Props) {
  if (values.length < 2) {
    return <svg className="spark" width={width} height={height} aria-hidden="true" />
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const step = width / (values.length - 1)
  const points = values.map((v, i) => [i * step, height - 3 - ((v - min) / range) * (height - 6)])
  const line = points.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const area = `${line} L${width},${height} L0,${height} Z`

  return (
    <svg
      className={`spark spark--${trend}`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
    >
      <path d={area} className="spark__area" />
      <path d={line} className="spark__line" />
    </svg>
  )
}
