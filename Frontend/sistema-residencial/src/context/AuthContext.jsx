import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const AuthContext = createContext();

// Función para capitalizar cada palabra
function capitalizarCadaPalabra(nombre) {
  if (!nombre) return "";
  return nombre
    .split(" ")
    .map((palabra) => palabra.charAt(0).toUpperCase() + palabra.slice(1))
    .join(" ");
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Estado de carga

  const login = async (usuario, contrasena) => {
    try {
      const respuesta = await axios.post("http://127.0.0.1:8000/auth/login", {
        nombre_usuario: usuario,
        contrasena: contrasena,
      });

      const datosUsuario = respuesta.data.usuario; // <-- aquí está el objeto correcto

      setUser({
        id: datosUsuario.id,
        nombre: capitalizarCadaPalabra(datosUsuario.nombre),
        rol: datosUsuario.id_rol,
        correo: datosUsuario.email,
      });

      localStorage.setItem("user", JSON.stringify({
        id: datosUsuario.id,
        nombre: datosUsuario.nombre,
        rol: datosUsuario.id_rol,
        correo: datosUsuario.email,
        token: respuesta.data.access_token, // opcional, útil para usarlo en axios
      }));

      return datosUsuario;
    } catch (error) {
      throw error;
    }
  };

  // === NUEVA FUNCIÓN PARA REGISTRAR USUARIOS ===
  const registrarUsuario = async (nombre, email, contrasena) => {
    try {
      const respuesta = await axios.post("http://127.0.0.1:8000/usuarios/", {
        nombre,
        email,
        password: contrasena,
        id_rol: 2, // 2 = Residente por defecto
      });

      return respuesta.data; // puedes devolver los datos del nuevo usuario si quieres
    } catch (error) {
      throw error; // para que el componente LoginRegister pueda manejarlo
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false); // Finalizar carga
  }, []);

  useEffect(() => {
    console.log("Estado de carga:", loading);
    console.log("Usuario:", user);
  }, [loading, user]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, registrarUsuario }}>
      {children}
    </AuthContext.Provider>
  );
}
