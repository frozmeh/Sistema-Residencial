"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const registerSchema = z
  .object({
    nombre: z.string().min(3, "El nombre de usuario debe tener al menos 3 caracteres"),
    email: z.string().email("Correo electrónico no válido"),
    password: z.string().min(6, "La contraseña debe tener al menos 6 caracteres"),
    confirmarPassword: z.string().min(6, "Confirma tu contraseña"),
  })
  .refine((data) => data.password === data.confirmarPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmarPassword"],
  });

type RegisterInputs = z.infer<typeof registerSchema>;

export default function RegisterForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInputs>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterInputs) => {
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: data.nombre,
          email: data.email,
          password: data.password,
        }),
      });

      if (res.ok) {
        setSuccess("Usuario registrado exitosamente. Espera validación del administrador.");
        setTimeout(() => router.push("/login"), 2000);
      } else {
        const errorData = await res.json();
        setError(errorData.detail || "Ocurrió un error durante el registro");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm mx-auto mt-20"
    >
      <h2 className="text-2xl font-bold mb-6 text-center">Crear cuenta</h2>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Nombre de usuario</label>
        <input
          {...register("nombre")}
          className="w-full border border-gray-300 rounded px-3 py-2"
          placeholder="Ingresa tu nombre de usuario"
        />
        {errors.nombre && <p className="text-red-500 text-sm mt-1">{errors.nombre.message}</p>}
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Correo electrónico</label>
        <input
          {...register("email")}
          className="w-full border border-gray-300 rounded px-3 py-2"
          placeholder="correo@ejemplo.com"
        />
        {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Contraseña</label>
        <input
          {...register("password")}
          type="password"
          className="w-full border border-gray-300 rounded px-3 py-2"
          placeholder="********"
        />
        {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Confirmar contraseña</label>
        <input
          {...register("confirmarPassword")}
          type="password"
          className="w-full border border-gray-300 rounded px-3 py-2"
          placeholder="********"
        />
        {errors.confirmarPassword && (
          <p className="text-red-500 text-sm mt-1">{errors.confirmarPassword.message}</p>
        )}
      </div>

      {error && <p className="text-red-500 mb-4">{error}</p>}
      {success && <p className="text-green-600 mb-4">{success}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
      >
        {isSubmitting ? "Creando cuenta..." : "Registrarse"}
      </button>
    </form>
  );
}
