// src/components/RootLayout.tsx
import { Outlet, NavLink } from "react-router";

export function RootLayout() {
  const navItems = [
    { path: "/", label: "Dashboard", icon: "📊" },
    { path: "/train", label: "Face Training", icon: "👤" },
    { path: "/organize", label: "Organize", icon: "📂" },
    { path: "/locations", label: "Locations", icon: "📍" },
    { path: "/events", label: "Events", icon: "✨" },
    { path: "/unidentified", label: "Unidentified", icon: "❓" },
  ];

  return (
    <div className="flex h-screen w-full bg-background text-foreground">
      <aside className="w-64 border-r border-sidebar-border bg-sidebar flex flex-col">
        <div className="p-8">
          <h1 className="text-xl font-bold text-sidebar-primary">PhotoSorter AI</h1>
        </div>
        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:bg-sidebar-accent/50"}
              `}
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-10">
        <Outlet />
      </main>
    </div>
  );
}