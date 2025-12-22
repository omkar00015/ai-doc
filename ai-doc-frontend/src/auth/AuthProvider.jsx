import React, { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const API_BASE = import.meta.env.VITE_API_BASE;

  // Call backend to see if cookie exists and get user
  const fetchMe = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/me`, {
        credentials: "include",
      });
      if (!res.ok) {
        setUser(null);
      } else {
        const json = await res.json();
        setUser(json.user);
      }
    } catch (err) {
      console.error("fetchMe error", err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMe();
  }, []);

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      console.error("logout error", e);
    } finally {
      setUser(null);
    }
  };

  const value = { user, setUser, loading, fetchMe, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
