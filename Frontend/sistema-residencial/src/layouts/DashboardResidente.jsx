// src/layouts/DashboardResidente.jsx
import { Outlet, Link } from "react-router-dom";

export default function DashboardResidente() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-4">Residente Dashboard</h2>
        <nav className="flex flex-col space-y-3">
          <Link to="/residente/mis-pagos" className="hover:bg-gray-700 p-2 rounded">Mis Pagos</Link>
          <Link to="/residente/reservas" className="hover:bg-gray-700 p-2 rounded">Reservas</Link>
        </nav>
      </aside>
      <main className="flex-1 p-6 bg-gray-100">
        <Outlet /> {/* Aquí se renderizan las rutas hijas */}
      </main>
    </div>
  );
}
