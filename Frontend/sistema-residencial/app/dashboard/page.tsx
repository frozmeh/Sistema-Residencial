import { getServerSession } from "next-auth/next";
import { authOptions } from "../api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  // Obtener sesión del usuario
  const session = await getServerSession(authOptions);

  // Redirigir si no hay sesión
  if (!session) {
    redirect("/login");
  }

  const { user } = session;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Bienvenido, {user.name}</p>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="font-semibold text-lg mb-2">ID de Usuario</h2>
          <p>{user.id}</p>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="font-semibold text-lg mb-2">Correo</h2>
          <p>{user.email}</p>
        </div>

        <div className="bg-white p-6 rounded shadow">
          <h2 className="font-semibold text-lg mb-2">Rol</h2>
          <p>{user.role}</p>
        </div>
      </main>

      <footer className="mt-8">
        <form action="/api/auth/signout" method="post">
          <button
            type="submit"
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
          >
            Cerrar Sesión
          </button>
        </form>
      </footer>
    </div>
  );
}
