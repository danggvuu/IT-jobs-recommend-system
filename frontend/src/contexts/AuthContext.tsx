import React, { createContext, useState, useEffect } from "react";
import api from "../services/api";

export interface User {
  id: number;
  email: string;
  full_name?: string;
  phone?: string;
  desired_position?: string;
  desired_location?: string;
  desired_level?: string;
  desired_salary?: number;
  years_experience?: number;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (tokenData: any) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        try {
          const res = await api.get("/auth/me");
          setUser(res.data);
        } catch (error) {
          console.error("Failed to fetch user");
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  const login = (tokenData: any) => {
    localStorage.setItem("access_token", tokenData.access_token);
    localStorage.setItem("refresh_token", tokenData.refresh_token);
    setUser(tokenData.user);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
