import { useState } from "react";
import { NavLink, Outlet, Link } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/categories", label: "Categories" },
  { to: "/reports", label: "Reports" },
  { to: "/query", label: "Ask the Data", end: true },
];

export default function LinkedinPublicLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header-inner">
          <button
            type="button"
            className={`menu-toggle${menuOpen ? " open" : ""}`}
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            aria-controls="public-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="bar" aria-hidden="true" />
          </button>
          <div className="brand-mark" aria-hidden="true">TCE</div>
          <h1 className="brand">TCE Institutional Activity Intelligence</h1>
          <nav id="public-nav" className={`nav-menu${menuOpen ? " open" : ""}`} aria-label="Main navigation">
            <ul>
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => (isActive ? "active" : "")}
                    onClick={() => setMenuOpen(false)}
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="public-footer">
        {/* No Source / Date Coverage provenance label here: it belongs on the
            Admin side, not on every user-facing page. */}
        <Link to="/admin/login">Staff login</Link>
      </footer>
    </div>
  );
}