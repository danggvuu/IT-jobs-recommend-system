import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AuthProvider, AuthContext } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { Toaster } from "react-hot-toast";
import { useContext } from "react";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RecommendPage from "./pages/RecommendPage";

function Navbar() {
  const { user, logout } = useContext(AuthContext);
  return (
    <nav className="p-4 text-white bg-gray-800">
      <div className="container flex justify-between mx-auto">
        <Link to="/" className="text-xl font-bold">IT Job Recommender</Link>
        <div>
          {user ? (
            <div className="flex items-center space-x-4">
              <span>Xin chào, {user.full_name || user.email}</span>
              <button onClick={logout} className="px-3 py-1 bg-red-500 rounded">Đăng xuất</button>
            </div>
          ) : (
            <div className="space-x-4">
              <Link to="/login">Đăng nhập</Link>
              <Link to="/register" className="px-3 py-1 bg-blue-500 rounded">Đăng ký</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

function AppContent() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={
          <ProtectedRoute>
            <RecommendPage />
          </ProtectedRoute>
        } />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
