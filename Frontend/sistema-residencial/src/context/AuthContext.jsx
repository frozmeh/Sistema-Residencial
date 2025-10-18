import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = async (usuario, contrasena) => {
    try {
      const respuesta = await axios.post("http://127.0.0.1:8000/auth/login", {
        nombre_usuario: usuario,
        contrasena: contrasena,
      });

      const datos = respuesta.data;
      setUser({
        id: datos.id,
        nombre: datos.nombre,
        rol: datos.rol,
        correo: datos.correo,
      });

      localStorage.setItem("user", JSON.stringify(datos));
      return datos;
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
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, registrarUsuario }}>
      {children}
    </AuthContext.Provider>
  );
}
