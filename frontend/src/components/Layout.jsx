import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/Auth";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/categories", label: "Categories" },
  { to: "/departments", label: "Departments" },
  { to: "/query", label: "Ask the Data" },
];

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { username, roleLabel, logout } = useAuth();

  async function onLogout() {
    await logout();
    window.location.href = "/login";
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header-inner">
          <button
            type="button"
            className={`menu-toggle${menuOpen ? " open" : ""}`}
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            aria-controls="main-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="bar" aria-hidden="true" />
          </button>
          <div className="brand-mark" aria-hidden="true">TCE</div>
          <h1 className="brand">TCE Activity Intelligence</h1>
          <nav id="main-nav" className={`nav-menu${menuOpen ? " open" : ""}`} aria-label="Main navigation">
            <ul>
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) => (isActive ? "active" : "")}
                    onClick={() => setMenuOpen(false)}
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="user-area">
            <span className="muted">{username} &middot; Role: {roleLabel}</span>
            <button type="button" className="ghost" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}