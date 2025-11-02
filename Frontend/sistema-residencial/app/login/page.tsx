"use client";

import Link from "next/link";
import { Command } from "lucide-react";

import LoginForm from "./login-form";
import { GoogleButton } from "../_components/social-auth/google-button";

export default function LoginPage() {
  return (
    <div className="flex h-dvh">
      <div className="bg-primary hidden lg:block lg:w-1/3">
        <div className="flex h-full flex-col items-center justify-center p-12 text-center">
          <div className="space-y-6">
            <Command className="text-primary-foreground mx-auto size-12" />
            <div className="space-y-2">
              <h1 className="text-primary-foreground text-5xl font-light">Conjunto Residencial</h1>
              <p className="text-primary-foreground/80 text-xl">
                La Ensenada
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-background flex w-full items-center justify-center p-8 lg:w-2/3">
        <div className="w-full max-w-md space-y-10 py-24 lg:py-32">
          <div className="space-y-4 text-center">
            <div className="font-medium tracking-tight text-2xl">Ingreso</div>
            <div className="text-muted-foreground mx-auto max-w-xl text-sm">
              Bienvenido de vuelta. Ingrese el usuario y la contraseña para continuar.
            </div>
          </div>

          <div className="space-y-4">
            {/* Formulario con NextAuth */}
            <LoginForm />

            {/* Botón social */}
            <GoogleButton className="w-full" variant="outline" />

            <p className="text-muted-foreground text-center text-xs">
              ¿No tienes una cuenta?{" "}
              <Link href="/register" className="text-primary">
                Registrarse
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
