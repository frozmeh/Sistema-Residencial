import { useContext, useState } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function LoginRegister() {
  const { login, registrarUsuario, recuperarContrasena } = useContext(AuthContext);
  const [tabActiva, setTabActiva] = useState("login");
  const [credenciales, setCredenciales] = useState({ usuario: "", email: "", contrasena: "", confirmar: "" });
  const [errores, setErrores] = useState({});
  const [errorGeneral, setErrorGeneral] = useState("");
  const [cargando, setCargando] = useState(false);
  const navigate = useNavigate();

  const manejarCambio = (e) => {
    const { name, value } = e.target;
    setCredenciales({ ...credenciales, [name]: value });
    setErrores({ ...errores, [name]: "" });
    setErrorGeneral("");
  };

  const validarLogin = () => {
    let valido = true;
    let nuevosErrores = {};
    if (!credenciales.usuario.trim()) {
      nuevosErrores.usuario = "El usuario es obligatorio";
      valido = false;
    }
    if (!credenciales.contrasena.trim()) {
      nuevosErrores.contrasena = "La contraseña es obligatoria";
      valido = false;
    }
    setErrores(nuevosErrores);
    return valido;
  };

  const validarRegister = () => {
    let valido = true;
    let nuevosErrores = {};
    if (!credenciales.usuario.trim()) {
      nuevosErrores.usuario = "El usuario es obligatorio";
      valido = false;
    }
    if (!credenciales.email.trim()) {
      nuevosErrores.email = "El email es obligatorio";
      valido = false;
    }
    if (!credenciales.contrasena.trim()) {
      nuevosErrores.contrasena = "La contraseña es obligatoria";
      valido = false;
    } else if (credenciales.contrasena.length < 6) {
      nuevosErrores.contrasena = "Debe tener al menos 6 caracteres";
      valido = false;
    }
    if (credenciales.contrasena !== credenciales.confirmar) {
      nuevosErrores.confirmar = "Las contraseñas no coinciden";
      valido = false;
    }
    setErrores(nuevosErrores);
    return valido;
  };

  const validarRecuperar = () => {
    let valido = true;
    let nuevosErrores = {};
    if (!credenciales.email.trim()) {
      nuevosErrores.email = "El email es obligatorio";
      valido = false;
    }
    setErrores(nuevosErrores);
    return valido;
  };

  const manejarEnvio = async (e) => {
    e.preventDefault();
    if (tabActiva === "login" && !validarLogin()) return;
    if (tabActiva === "register" && !validarRegister()) return;
    if (tabActiva === "recuperar" && !validarRecuperar()) return;

    setCargando(true);
    setErrorGeneral("");

    try {
      if (tabActiva === "login") {
        await login(credenciales.usuario, credenciales.contrasena);
        navigate("/", { state: { fadeIn: true } }); // redirige al inicio
      } else if (tabActiva === "register") {
        await registrarUsuario(credenciales.usuario, credenciales.email, credenciales.contrasena);
        alert("Usuario registrado exitosamente"); // simple alert
        setTabActiva("login");
        setCredenciales({ usuario: "", email: "", contrasena: "", confirmar: "" });
      } else if (tabActiva === "recuperar") {
        await recuperarContrasena(credenciales.email);
        alert("Se envió un enlace de recuperación a tu email"); // alert para recuperación
        setTabActiva("login");
        setCredenciales({ usuario: "", email: "", contrasena: "", confirmar: "" });
      }
    } catch (error) {
      setErrorGeneral(error?.response?.data?.detail || "Ocurrió un error");
    }

    setCargando(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-600 via-blue-500 to-cyan-400 relative">

      {cargando && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-20">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      <div className="bg-white/95 rounded-2xl shadow-xl w-full max-w-md p-8 relative z-10">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-6">Sistema Residencial</h2>

        {/* Tabs */}
        <div className="flex justify-center mb-6">
          {["login", "register", "recuperar"].map((tab) => (
            <button
              key={tab}
              onClick={() => setTabActiva(tab)}
              className={`px-4 py-2 rounded-t-lg font-semibold ${
                tabActiva === tab ? "bg-white text-blue-600 shadow-md" : "text-gray-500"
              }`}
            >
              {tab === "login" ? "Login" : tab === "register" ? "Register" : "Recuperar"}
            </button>
          ))}
        </div>

        <form onSubmit={manejarEnvio} className="space-y-5">
          {tabActiva === "login" && (
            <>
              <InputField label="Usuario" name="usuario" value={credenciales.usuario} onChange={manejarCambio} error={errores.usuario} placeholder="Ingresa tu usuario" />
              <InputField label="Contraseña" name="contrasena" type="password" value={credenciales.contrasena} onChange={manejarCambio} error={errores.contrasena} placeholder="Ingresa tu contraseña" />
            </>
          )}

          {tabActiva === "register" && (
            <>
              <InputField label="Usuario" name="usuario" value={credenciales.usuario} onChange={manejarCambio} error={errores.usuario} placeholder="Ingresa tu usuario" />
              <InputField label="Email" name="email" value={credenciales.email} onChange={manejarCambio} error={errores.email} placeholder="Ingresa tu email" />
              <InputField label="Contraseña" name="contrasena" type="password" value={credenciales.contrasena} onChange={manejarCambio} error={errores.contrasena} placeholder="Ingresa tu contraseña" />
              <InputField label="Confirmar contraseña" name="confirmar" type="password" value={credenciales.confirmar} onChange={manejarCambio} error={errores.confirmar} placeholder="Confirma tu contraseña" />
            </>
          )}

          {tabActiva === "recuperar" && (
            <>
              <InputField label="Email" name="email" value={credenciales.email} onChange={manejarCambio} error={errores.email} placeholder="Ingresa tu email" />
            </>
          )}

          {errorGeneral && <p className="text-center text-red-600 font-medium">{errorGeneral}</p>}

          <button
            type="submit"
            disabled={cargando}
            className={`w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition duration-200 ${
              cargando ? "opacity-70 cursor-not-allowed" : ""
            }`}
          >
            {cargando
              ? tabActiva === "login"
                ? "Iniciando..."
                : tabActiva === "register"
                ? "Registrando..."
                : "Enviando..."
              : tabActiva === "login"
              ? "Iniciar Sesión"
              : tabActiva === "register"
              ? "Registrarse"
              : "Recuperar Contraseña"}
          </button>
        </form>
      </div>

      <style>
        {`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-4px); }
            40%, 80% { transform: translateX(4px); }
          }
          .animate-shake { animation: shake 0.3s ease-in-out; }

          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .animate-spin { animation: spin 1s linear infinite; }
        `}
      </style>
    </div>
  );
}

// Componente reutilizable para input
function InputField({ label, name, type = "text", value, onChange, error, placeholder }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        className={`w-full px-4 py-2 rounded-lg border ${error ? "border-red-500 animate-shake" : "border-gray-300"} focus:outline-none focus:ring-2 focus:ring-blue-500`}
        placeholder={placeholder}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
}
