"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    nombre: "",
    email: "",
    password: "",
  });

  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCargando(true);
    setMensaje("");

    try {
      const res = await fetch("http://127.0.0.1:8000/usuarios/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, rol_id: 2 }), // rol_id 2 = residente
      });

      if (res.ok) {
        setMensaje("Usuario registrado con éxito.");
        router.push("/login");
      } else {
        const data = await res.json();
        setMensaje(data.detail || "Error al registrar usuario");
      }
    } catch (error) {
      console.error(error);
      setMensaje("Error de conexión con el servidor");
    }

    setCargando(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="bg-white shadow-md rounded-2xl p-8 w-full max-w-md"
      >
        <h1 className="text-2xl font-bold text-center mb-6">Registro</h1>

        <input
          type="text"
          name="nombre"
          placeholder="Nombre de usuario"
          value={formData.nombre}
          onChange={handleChange}
          required
          className="w-full mb-4 p-2 border rounded"
        />

        <input
          type="email"
          name="email"
          placeholder="Correo electrónico"
          value={formData.email}
          onChange={handleChange}
          required
          className="w-full mb-4 p-2 border rounded"
        />

        <input
          type="password"
          name="password"
          placeholder="Contraseña"
          value={formData.password}
          onChange={handleChange}
          required
          className="w-full mb-4 p-2 border rounded"
        />

        <button
          type="submit"
          disabled={cargando}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
        >
          {cargando ? "Registrando..." : "Registrarse"}
        </button>

        {mensaje && (
          <p className="text-center mt-4 text-sm text-gray-700">{mensaje}</p>
        )}
      </form>
    </div>
  );
}
