export default function AboutPage() {
  return (
    <section className="panel aboutPanel">
      <div className="stepHeader">
        <div>
          <p className="eyebrow">About Lookitup</p>
          <h2>Search first. AI only when useful.</h2>
        </div>
      </div>

      <p className="aboutLead">
        Lookitup is not an AI truth machine. It helps journalists search faster inside
        sources they already trust.
      </p>

      <p className="aboutMantra">
        Search first. AI only when useful. Trusted sources only. Journalists decide.
      </p>

      <div className="aboutList">
        <h3>Important limitations</h3>
        <ul>
          <li>Lookitup is not a universal truth engine.</li>
          <li>
            The quality of results depends on the quality of the trusted sources selected by
            the journalist.
          </li>
          <li>No result found does not mean the claim is false.</li>
          <li>Lookitup does not search the open web by default.</li>
        </ul>
      </div>
    </section>
  );
}
