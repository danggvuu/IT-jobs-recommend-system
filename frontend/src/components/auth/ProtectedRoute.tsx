import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../../contexts/AuthContext";

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) return <div>Đang tải...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return children;
};
