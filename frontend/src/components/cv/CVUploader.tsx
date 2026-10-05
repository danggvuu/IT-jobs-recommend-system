import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../../services/api';
import toast from 'react-hot-toast';

export default function CVUploader({ onUploadSuccess }: { onUploadSuccess: (cvId: number, text: string) => void }) {
  const [uploading, setUploading] = useState(false);

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    const loadingToast = toast.loading("Đang trích xuất dữ liệu từ CV...");
    
    try {
      const res = await api.post("/cvs/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("Tải lên CV thành công!", { id: loadingToast });
      onUploadSuccess(res.data.cv_id, res.data.extracted_text);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Lỗi tải lên CV", { id: loadingToast });
    }
    setUploading(false);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  return (
    <div 
      {...getRootProps()} 
      className={`p-8 mt-4 text-center border-2 border-dashed rounded-lg cursor-pointer ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <p className="text-gray-600">Đang tải lên và xử lý...</p>
      ) : isDragActive ? (
        <p className="text-blue-500">Thả file vào đây ...</p>
      ) : (
        <div>
          <p className="text-gray-600">Kéo thả CV vào đây, hoặc click để chọn file</p>
          <p className="text-sm text-gray-400 mt-2">Hỗ trợ: PDF, DOCX, JPG, PNG (Tối đa 10MB)</p>
        </div>
      )}
    </div>
  );
}
