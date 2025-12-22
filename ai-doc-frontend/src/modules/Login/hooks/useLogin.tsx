import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../../auth/AuthProvider";

export function useLogin() {
  const auth = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showRegisterPrompt, setShowRegisterPrompt] = useState(false);

  const handleLogin = async () => {
    if (!auth) {
      console.error("Auth not initialized");
      setError("Authentication system not ready");
      return;
    }

    const { setUser } = auth;
    const API_BASE = import.meta.env.VITE_API_BASE;

    setLoading(true);
    setError("");
    setShowRegisterPrompt(false);

    try {
      const res = await fetch(
        `${API_BASE}/auth/login`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );

      const json = await res.json();

      if (!res.ok) {
        const message = json?.message || "Login failed";
        setError(message);

        const lower = message.toLowerCase();
        if (
          res.status === 400 &&
          (lower.includes("invalid") ||
            lower.includes("not found") ||
            lower.includes("no user"))
        ) {
          setShowRegisterPrompt(true);
        }

        setUser(null);
        return;
      }
      setUser(json.user);
      navigate("/main");
    } catch (err) {
      console.error("Login error:", err);
      setError("Network error. Please try again.");
      setShowRegisterPrompt(false);
    } finally {
      setLoading(false);
    }
  };

  const goToRegister = () => {
    navigate("/register", { state: { email } });
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    loading,
    error,
    showRegisterPrompt,
    handleLogin,
    goToRegister,
  };
}
