type Page = "home" | "about";

interface HeaderProps {
  page: Page;
  onNavigate: (page: Page) => void;
}

export default function Header({ page, onNavigate }: HeaderProps) {
  return (
    <header className="hero">
      <div className="heroRow">
        <div>
          <h1 className="brandTitle">
            <span className="brandLogoBadge">
              <img className="brandLogo" src="/lookitup.svg" alt="Lookitup" />
            </span>
          </h1>
          <p className="subtitle">Having a doubt? Just Lookitup.</p>
        </div>
        <nav className="nav">
          <button
            type="button"
            className={page === "home" ? "navLink active" : "navLink"}
            onClick={() => onNavigate("home")}
          >
            Search
          </button>
          <button
            type="button"
            className={page === "about" ? "navLink active" : "navLink"}
            onClick={() => onNavigate("about")}
          >
            About
          </button>
          <a className="navLink" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API
          </a>
        </nav>
      </div>
      <p className="heroCopy">
        Google searches the open web. Lookitup searches your trusted world.
      </p>
    </header>
  );
}
