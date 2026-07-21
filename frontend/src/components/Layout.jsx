import { NavLink, Outlet } from "react-router-dom";

const linkler = [
  { yol: "/", etiket: "Değerleme", end: true },
  { yol: "/ilanlar", etiket: "İlanlar" },
  { yol: "/gecmis", etiket: "Geçmiş" },
  { yol: "/yonetim", etiket: "Yönetim" },
];

export default function Layout() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand" end>
            <span className="k">K</span>
            <span className="dot">·</span>
            <span>EMLAK</span>
          </NavLink>
          <nav className="nav">
            {linkler.map((l) => (
              <NavLink key={l.yol} to={l.yol} end={l.end}>
                {l.etiket}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
