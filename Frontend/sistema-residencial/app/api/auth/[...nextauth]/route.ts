import NextAuth, { AuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import axios from "axios";

// Definimos el tipo User según tu backend
interface Usuario {
  id: string;
  name: string;
  email: string;
  role: string;
  access_token: string;
}

export const authOptions: AuthOptions = {
  secret: process.env.NEXTAUTH_SECRET, // Obligatorio para JWT
  providers: [
    CredentialsProvider({
      name: "Credenciales",
      credentials: {
        nombre_usuario: { label: "Usuario", type: "text" },
        contrasena: { label: "Contraseña", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials) return null;

        try {
            const res = await axios.post("http://localhost:8000/auth/login", {
            nombre_usuario: credentials.nombre_usuario,
            contrasena: credentials.contrasena,
            });

            const { usuario, access_token } = res.data;

            if (!usuario) {
            // Usuario no encontrado
            throw new Error("usuario_no_encontrado");
            }

            return {
            id: String(usuario.id),
            name: usuario.nombre,
            email: usuario.correo,
            role: String(usuario.rol),
            access_token: access_token,
            };
        } catch (err: any) {
            // Mapear errores del backend a códigos propios
            const backendError = err.response?.data?.detail;

            if (backendError === "Usuario no encontrado") {
            throw new Error("usuario_no_encontrado");
            } else if (backendError === "Contraseña incorrecta") {
            throw new Error("contrasena_incorrecta");
            } else if (backendError === "Usuario bloqueado") {
            throw new Error("usuario_bloqueado");
            } else {
            throw new Error("error_desconocido");
            }
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
        token.access_token = user.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      session.user.role = token.role as string;
      session.user.access_token = token.access_token as string;
      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
