import { Outlet, Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export default function DashboardLayout() {
  const { logout, user } = useContext(AuthContext);

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-4">Menú</h2>
        <nav className="flex flex-col space-y-3">
          <Link to="/" className="hover:bg-gray-700 p-2 rounded">🏠 Inicio</Link>
        </nav>
        <div className="mt-auto">
          <p className="text-sm mb-2">Bienvenido, {user?.nombre}</p>
          <button onClick={logout} className="bg-red-500 w-full py-1 rounded hover:bg-red-600">
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="flex-1 p-6 bg-gray-100">
        <Outlet />
      </main>
    </div>
  );
}
