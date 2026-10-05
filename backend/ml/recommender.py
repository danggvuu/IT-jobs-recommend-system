import os
import pickle
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity
import re

class JobRecommender:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
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

    def _build_query_vector(self, cv_text: str):
        tfidf_vec = self.tfidf.transform([cv_text])
        
        skills_vec = np.zeros((1, len(self.skill_vocab)))
        cv_text_lower = cv_text.lower()
        for skill, idx in self.skill_vocab.items():
            if f" {skill} " in f" {cv_text_lower} ":
                skills_vec[0, idx] = 1
        skills_vec = sp.csr_matrix(skills_vec)
        
        n_locations = len(self.meta_info['location_columns'])
        loc_vec = np.zeros((1, n_locations))
        loc_vec[0, 0] = 1.0  # Khác
        
        level_val = self.meta_info['level_map'].get('Middle', 0) / 5.0
        exp_val = 2.0  # Guess 2 years
        if self.meta_info.get('scaler'):
            exp_val = self.meta_info['scaler'].transform([[exp_val]])[0][0]
        else:
            exp_val = exp_val / 10.0
            
        meta_vec = np.zeros((1, n_locations + 2))
        meta_vec[0, :n_locations] = loc_vec
        meta_vec[0, -2] = level_val
        meta_vec[0, -1] = exp_val
        meta_vec = sp.csr_matrix(meta_vec)
        
        from sklearn.preprocessing import normalize
        tfidf_vec = normalize(tfidf_vec, norm='l2') if tfidf_vec.nnz > 0 else tfidf_vec
        skills_vec = normalize(skills_vec, norm='l2') if skills_vec.nnz > 0 else skills_vec
        meta_vec = normalize(meta_vec, norm='l2') if meta_vec.nnz > 0 else meta_vec
        
        combined = sp.hstack([tfidf_vec * 0.5, skills_vec * 0.35, meta_vec * 0.15])
        return combined

    def recommend_from_cv_text(self, cv_text: str, top_k=10, location_filter=None, level_filter=None, salary_min_filter=None):
        query_vec = self._build_query_vector(cv_text)
        sim_scores = cosine_similarity(query_vec, self.feature_matrix).flatten()
        
        df = self.jobs_df.copy()
        df['score'] = sim_scores * 100
        
        if location_filter and location_filter != "Tất cả":
            df = df[df['location'].str.contains(location_filter, case=False, na=False)]
        if level_filter and level_filter != "Tất cả":
            df = df[df['level'].str.contains(level_filter, case=False, na=False)]
        if salary_min_filter and salary_min_filter > 0:
            df = df[(df['salary_max'] >= salary_min_filter) | (df['salary_min'] >= salary_min_filter)]
            
        df = df.sort_values('score', ascending=False).head(top_k)
        df['rank'] = range(1, len(df) + 1)
        return df
