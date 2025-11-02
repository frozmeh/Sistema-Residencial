import NextAuth, { DefaultSession, DefaultUser } from "next-auth";

// Extender el tipo de Session y User
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      role: string;
      access_token: string;
    } & DefaultSession["user"];
  }

  interface User extends DefaultUser {
    id: string;
    role: string;
    access_token: string;
  }
}
