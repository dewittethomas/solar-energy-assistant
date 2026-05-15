export function PageHeading({ eyebrow, title }) {
  return (
    <div className="dashboard-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="dashboard-title">{title}</h2>
      </div>
    </div>
  )
}
