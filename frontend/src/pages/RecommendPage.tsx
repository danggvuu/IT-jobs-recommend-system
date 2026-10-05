import { useState } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import CVUploader from "../components/cv/CVUploader";

export default function RecommendPage() {
  const [cvText, setCvText] = useState("");
  const [cvId, setCvId] = useState<number | null>(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('text');

  const handleRecommend = async () => {
    if (!cvText && !cvId) return toast.error("Vui lòng nhập text hoặc upload CV!");
    setLoading(true);
    try {
      const res = await api.post("/recommend", { 
        cv_text: cvText, 
        cv_id: cvId,
        top_k: 20 
      });
      setResults(res.data.jobs);
      toast.success(`Tìm thấy ${res.data.total} công việc!`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Lỗi khi tìm việc");
    }
    setLoading(false);
  };

  const handleUploadSuccess = (id: number, text: string) => {
    setCvId(id);
    setCvText(text);
    setActiveTab('text'); // Chuyển qua tab text để xem preview
  };

  return (
    <div className="container p-4 mx-auto max-w-6xl">
      <h1 className="mb-6 text-3xl font-bold text-gray-800">🎯 Tìm Việc Làm Thông Minh (AI)</h1>
      
      <div className="flex space-x-4 mb-4 border-b">
        <button 
          className={`pb-2 px-4 ${activeTab === 'upload' ? 'border-b-2 border-blue-500 font-bold text-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('upload')}
        >
          1. Upload CV (PDF/DOCX/Ảnh)
        </button>
        <button 
          className={`pb-2 px-4 ${activeTab === 'text' ? 'border-b-2 border-blue-500 font-bold text-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('text')}
        >
          2. Dán / Sửa Text
        </button>
      </div>

      <div className="mb-6 bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        {activeTab === 'upload' && (
          <CVUploader onUploadSuccess={handleUploadSuccess} />
        )}
        
        {activeTab === 'text' && (
          <div>
            <label className="block mb-2 text-sm font-semibold text-gray-700">
              Nội dung CV (Có thể chỉnh sửa trước khi tìm kiếm):
            </label>
            <textarea
              className="w-full p-4 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm"
              rows={8}
              value={cvText}
              onChange={e => setCvText(e.target.value)}
              placeholder="VD: Tôi có 3 năm kinh nghiệm Python, Django, REST API..."
            ></textarea>
          </div>
        )}
      </div>

      <div className="flex justify-center mb-10">
        <button 
          onClick={handleRecommend} 
          disabled={loading}
          className="px-8 py-3 text-lg font-bold text-white transition-all bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:transform-none"
        >
          {loading ? "Đang phân tích..." : "🔍 Phân Tích & Tìm Việc Ngay"}
        </button>
      </div>

      {results.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Kết quả phù hợp ({results.length})</h2>
          <div className="grid gap-6 md:grid-cols-2">
            {results.map((job: any, idx) => (
              <div key={idx} className="p-5 bg-white border border-gray-100 rounded-xl shadow-md hover:shadow-lg transition-shadow relative overflow-hidden group">
                <div className="absolute top-0 right-0 bg-green-100 text-green-700 font-bold px-3 py-1 rounded-bl-lg text-sm">
                  Top {job.rank} • Match: {job.score.toFixed(1)}%
                </div>
                
                <h3 className="pr-20 mb-2 text-lg font-bold text-gray-800 group-hover:text-blue-600 transition-colors line-clamp-2">
                  {job.title}
                </h3>
                
                <div className="mb-4 text-sm text-gray-600">
                  <p className="font-medium text-gray-700 mb-1">🏢 {job.company_name}</p>
                  <p className="mb-1">📍 {job.location} | 💼 {job.level}</p>
                  <p className="font-semibold text-indigo-600">
                    💰 {job.salary_min ? `${job.salary_min} - ${job.salary_max} triệu` : 'Lương: Thương lượng'}
                  </p>
                </div>
                
                <div className="flex items-center justify-between mt-4">
                  <div className="text-xs text-gray-500">
                    Nguồn: <span className="font-medium uppercase">{job.platforms.join(", ")}</span>
                  </div>
                  {job.url && (
                    <a 
                      href={job.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
                    >
                      Xem chi tiết ↗
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
