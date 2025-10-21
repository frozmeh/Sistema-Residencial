// src/components/ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export function ProtectedRoute({ allowedRoles }) {
  const { user, loading } = useContext(AuthContext);

  if (loading) return <div>Cargando...</div>; // Mostrar indicador de carga

  if (!user) return <Navigate to="/login" replace />; // No logueado

  if (!allowedRoles.includes(user.rol)) {
    return <Navigate to="/unauthorized" replace />; // Rol no permitido
  }

  return <Outlet />; // Esto permite renderizar las rutas hijas
}
