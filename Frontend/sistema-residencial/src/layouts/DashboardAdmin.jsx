// src/layouts/DashboardAdmin.jsx
import { Outlet, Link } from "react-router-dom";

export default function DashboardAdmin() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-4">Admin Dashboard</h2>
        <nav className="flex flex-col space-y-3">
          <Link to="/admin/usuarios" className="hover:bg-gray-700 p-2 rounded">Usuarios</Link>
          <Link to="/admin/reportes" className="hover:bg-gray-700 p-2 rounded">Reportes</Link>
        </nav>
      </aside>
      <main className="flex-1 p-6 bg-gray-100">
        <Outlet /> {/* Aquí se renderizan las rutas hijas */}
      </main>
    </div>
  );
}
