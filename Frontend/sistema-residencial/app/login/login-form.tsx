"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { signIn } from "next-auth/react";
import { useState } from "react";
import { useRouter } from "next/navigation";

const loginSchema = z.object({
  nombre_usuario: z.string().min(1, "El nombre de usuario es requerido"),
  contrasena: z.string().min(1, "La contraseña es requerida"),
});

type LoginFormInputs = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormInputs) => {
    setError(null);

    const res = await signIn("credentials", {
      redirect: false,
      nombre_usuario: data.nombre_usuario,
      contrasena: data.contrasena,
    });

    if (res?.error) {
      // Mapear los códigos de error a mensajes amigables
      switch (res.error) {
        case "usuario_no_encontrado":
          setError("El usuario no existe");
          break;
        case "contrasena_incorrecta":
          setError("Contraseña incorrecta");
          break;
        case "usuario_bloqueado":
          setError("Cuenta bloqueada, contacta al administrador");
          break;
        case "error_desconocido":
          setError("Ocurrió un error, intenta nuevamente");
          break;
        default:
          setError("Error en el inicio de sesión");
      }
    } else {
      router.push("/dashboard"); // Redirige si login exitoso
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="bg-white p-8 rounded-lg shadow-md w-full"
    >
      <div className="mb-4">
        <label className="block mb-1 font-medium">Nombre de usuario</label>
        <input
          {...register("nombre_usuario")}
          className="w-full border border-gray-400 rounded px-3 py-2 focus:border-gray-500 focus:ring-1 focus:ring-gray-500 focus:outline-none"
          placeholder="Ingresa tu usuario"
        />
        {errors.nombre_usuario && (
          <p className="text-red-500 text-sm mt-1">{errors.nombre_usuario.message}</p>
        )}
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Contraseña</label>
        <input
          {...register("contrasena")}
          type="password"
          className="w-full border border-gray-400 rounded px-3 py-2 focus:border-gray-500 focus:ring-1 focus:ring-gray-500 focus:outline-none"
          placeholder="Ingresa tu contraseña"
        />
        {errors.contrasena && (
          <p className="text-red-500 text-sm mt-1">{errors.contrasena.message}</p>
        )}
      </div>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
      >
        {isSubmitting ? "Ingresando..." : "Iniciar sesión"}
      </button>
    </form>
  );
}
