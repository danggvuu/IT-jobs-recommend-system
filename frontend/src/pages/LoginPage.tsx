import { useState, useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";
import api from "../services/api";
import { useNavigate, Link } from "react-router-dom";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post("/auth/login", { email, password });
      login(res.data);
      toast.success("Đăng nhập thành công!");
      navigate("/");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Lỗi đăng nhập");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded shadow-md w-96">
        <h2 className="mb-4 text-2xl font-bold text-center">Đăng nhập</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block mb-2 text-sm font-bold text-gray-700">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full px-3 py-2 border rounded" required />
          </div>
          <div className="mb-6">
            <label className="block mb-2 text-sm font-bold text-gray-700">Mật khẩu</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full px-3 py-2 border rounded" required />
          </div>
          <button type="submit" className="w-full px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700">Đăng nhập</button>
        </form>
        <div className="mt-4 text-center">
          <Link to="/register" className="text-sm text-blue-500 hover:underline">Chưa có tài khoản? Đăng ký</Link>
        </div>
      </div>
    </div>
  );
}
