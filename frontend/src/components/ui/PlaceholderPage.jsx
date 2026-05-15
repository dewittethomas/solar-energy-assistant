export function PlaceholderPage({ Icon, eyebrow, title, text }) {
  return (
    <section className="placeholder-page">
      <div className="placeholder-icon" aria-hidden="true">
        <Icon size={28} strokeWidth={2.1} />
      </div>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{text}</p>
    </section>
  )
}
