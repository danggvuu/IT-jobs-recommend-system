import pandas as pd
import numpy as np
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import pickle
import os

class JobRecommender:
    def __init__(self):
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Load tất cả artifacts từ database/ folder
        print("Loading recommender artifacts...")
        self.feature_matrix = sp.load_npz(os.path.join(base_dir, "database/feature_matrix.npz"))
        self.jobs_df = pd.read_pickle(os.path.join(base_dir, "database/jobs_cleaned.pkl")).reset_index(drop=True)
        
        with open(os.path.join(base_dir, "database/tfidf_vectorizer.pkl"), "rb") as f:
            self.tfidf = pickle.load(f)
            
        with open(os.path.join(base_dir, "database/skill_vocab.pkl"), "rb") as f:
            self.skill_vocab = pickle.load(f)
            
        with open(os.path.join(base_dir, "database/feature_metadata.pkl"), "rb") as f:
            self.meta_info = pickle.load(f)
            
        with open(os.path.join(base_dir, "database/jobs_index.pkl"), "rb") as f:
            self.jobs_index = pickle.load(f)
            
        self.id_to_idx = {str(k): int(v) for k, v in self.jobs_index.items()}

    def _build_query_vector(self, cv_text: str) -> sp.csr_matrix:
        """
        Transform cv_text thành vector giống combined_matrix.
        """
        # 1. TF-IDF transform cv_text
        cv_tfidf = self.tfidf.transform([cv_text])
        
        # 2. Skill matching: scan cv_text tìm skills trong skill_vocab
        cv_lower = cv_text.lower()
        row_ind, col_ind, data_val = [], [], []
        # Pad with spaces to match exact words if needed, or just standard "in"
        # Since skills can be multi-word, "in" is a good fallback
        for skill, idx in self.skill_vocab.items():
            if skill in cv_lower:
                row_ind.append(0)
                col_ind.append(idx)
                data_val.append(1.0)
                
        cv_skills = sp.csr_matrix((data_val, (row_ind, col_ind)), shape=(1, len(self.skill_vocab)))
        
        # 3. Metadata: default level=Middle, location=Khác
        loc_cols = self.meta_info['location_columns']
        # loc_cols thường là ['loc_Hà Nội', 'loc_Khác', 'loc_Remote', 'loc_TP.HCM', 'loc_Đà Nẵng']
        meta_row = np.zeros(len(loc_cols) + 2)
        
        # Nếu cv_text nhắc đến Hà Nội thì location=Hà Nội, v.v.
        if "hà nội" in cv_lower: loc_idx = loc_cols.index('loc_Hà Nội') if 'loc_Hà Nội' in loc_cols else 1
        elif "hồ chí minh" in cv_lower or "hcm" in cv_lower: loc_idx = loc_cols.index('loc_TP.HCM') if 'loc_TP.HCM' in loc_cols else 1
        elif "đà nẵng" in cv_lower: loc_idx = loc_cols.index('loc_Đà Nẵng') if 'loc_Đà Nẵng' in loc_cols else 1
        else: loc_idx = loc_cols.index('loc_Khác') if 'loc_Khác' in loc_cols else 1
            
        meta_row[loc_idx] = 1.0
        
        # Level default = Middle (3.0/5.0)
        meta_row[-2] = 3.0 / 5.0
        # Experience default = 2 years
        meta_row[-1] = self.meta_info['exp_scaler'].transform([[2.0]])[0][0]
        
        cv_meta = sp.csr_matrix(meta_row)
        
        # 4. Combine với cùng trọng số (0.5, 0.35, 0.15)
        tf_norm = normalize(cv_tfidf, norm='l2', axis=1) * 0.5
        sk_norm = normalize(cv_skills, norm='l2', axis=1) * 0.35
        mt_norm = normalize(cv_meta, norm='l2', axis=1) * 0.15
        
        return sp.hstack([tf_norm, sk_norm, mt_norm], format='csr')

    def recommend_from_cv_text(
        self, cv_text: str, top_k: int = 10,
        location_filter: str = None, level_filter: str = None,
        salary_min_filter: float = None
    ) -> pd.DataFrame:
        """
        Return DataFrame ranked by score, after applying hard filters.
        """
        query_vec = self._build_query_vector(cv_text)
        sim_scores = cosine_similarity(query_vec, self.feature_matrix).flatten()
        
        # Apply filters BEFORE ranking
        valid_indices = np.ones(len(self.jobs_df), dtype=bool)
        
        if location_filter and location_filter != "Tất cả":
            valid_indices &= (self.jobs_df['location'] == location_filter)
            
        if level_filter and level_filter != "Tất cả":
            valid_indices &= (self.jobs_df['level'] == level_filter)
            
        if salary_min_filter is not None and salary_min_filter > 0:
            # Chỉ lấy các job có mức lương tối đa >= yêu cầu (hoặc thỏa thuận - None)
            sal_mask = self.jobs_df['salary_max'].isna() | (self.jobs_df['salary_max'] >= salary_min_filter)
            valid_indices &= sal_mask
            
        # Get scores for valid jobs only
        valid_idx_list = np.where(valid_indices)[0]
        if len(valid_idx_list) == 0:
            return pd.DataFrame()
            
        valid_scores = sim_scores[valid_idx_list]
        
        # Rank valid jobs
        top_k = min(top_k, len(valid_idx_list))
        top_local_indices = valid_scores.argsort()[::-1][:top_k]
        top_global_indices = valid_idx_list[top_local_indices]
        
        res_df = self.jobs_df.iloc[top_global_indices].copy()
        res_df['score'] = sim_scores[top_global_indices] * 100
        res_df['rank'] = range(1, len(res_df) + 1)
        
        # Cột url có sẵn trong jobs_df (hoặc lấy từ first record nếu dedup)
        # Vì ta gom nhóm, 'url' không có trong list các cột .agg, nên phải xử lý cẩn thận.
        # Wait, the dedup step didn't save 'url'. Let's check if 'url' exists.
        if 'url' not in res_df.columns:
            res_df['url'] = "N/A"
            
        cols = ['rank', 'score', 'job_id', 'title', 'company_name', 
                'salary_min', 'salary_max', 'location', 'level', 'platforms', 'url']
        
        return res_df[[c for c in cols if c in res_df.columns]]

    def recommend_similar_jobs(self, job_id: str, top_k: int = 10) -> pd.DataFrame:
        """Tìm jobs tương tự với một job cụ thể"""
        if str(job_id) not in self.id_to_idx:
            print(f"Không tìm thấy job_id: {job_id}")
            return pd.DataFrame()
            
        idx = self.id_to_idx[str(job_id)]
        query_vec = self.feature_matrix[idx]
        
        sim_scores = cosine_similarity(query_vec, self.feature_matrix).flatten()
        top_indices = sim_scores.argsort()[::-1]
        
        # Bỏ qua chính nó
        top_indices = [i for i in top_indices if i != idx][:top_k]
        
        res_df = self.jobs_df.iloc[top_indices].copy()
        res_df['score'] = sim_scores[top_indices] * 100
        res_df['rank'] = range(1, len(res_df) + 1)
        
        if 'url' not in res_df.columns: res_df['url'] = "N/A"
        
        cols = ['rank', 'score', 'job_id', 'title', 'company_name', 
                'location', 'level', 'platforms', 'url']
        return res_df[[c for c in cols if c in res_df.columns]]

if __name__ == "__main__":
    recommender = JobRecommender()
    
    cv_mau = """
    Tôi là lập trình viên với 3 năm kinh nghiệm Python và Django.
    Thành thạo REST API, PostgreSQL, Docker, AWS.
    Đã làm việc với React, có kiến thức về Machine Learning.
    Mong muốn làm việc tại Hà Nội, mức lương 25-35 triệu.
    """
    
    print("\n" + "="*50)
    print("📋 [CV MẪU]:", cv_mau.strip())
    print("="*50)
    
    print("\n🔍 KỊCH BẢN 1: TÌM KIẾM KHÔNG FILTER")
    results1 = recommender.recommend_from_cv_text(cv_mau, top_k=3)
    for i, row in results1.iterrows():
        print(f" #{row['rank']} ({row['score']:.1f}%) | {row['title']}")
        print(f"   🏢 {row['company_name']} | 📍 {row['location']} | 💰 {row['salary_min']}-{row['salary_max']}tr\n")

    print("🔍 KỊCH BẢN 2: TÌM KIẾM CÓ FILTER (Hà Nội, Lương >= 30tr, Senior)")
    results2 = recommender.recommend_from_cv_text(
        cv_mau, top_k=3, 
        location_filter="Hà Nội", 
        level_filter="Senior",
        salary_min_filter=30
    )
    if results2.empty:
        print("   ❌ Không có job nào thỏa mãn filter.")
    else:
        for i, row in results2.iterrows():
            print(f" #{row['rank']} ({row['score']:.1f}%) | {row['title']}")
            print(f"   🏢 {row['company_name']} | 📍 {row['location']} | 💰 {row['salary_min']}-{row['salary_max']}tr\n")
