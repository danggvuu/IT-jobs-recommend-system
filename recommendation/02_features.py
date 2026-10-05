import pandas as pd
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize, MinMaxScaler
import pickle
import os

def build_features():
    print("Đang load dữ liệu đã clean...")
    df = pd.read_pickle("database/jobs_cleaned.pkl")
    df = df.reset_index(drop=True)

    # 1. TF-IDF trên full_text
    print("1. Build TF-IDF matrix...")
    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1,2), min_df=2)
    tfidf_matrix = tfidf.fit_transform(df['full_text'])
    
    # 2. Skills Binary Matrix
    print("2. Build Skills matrix...")
    all_skills = []
    for s_list in df['skills_list']:
        all_skills.extend(s_list)
    unique_skills = sorted(list(set(all_skills)))
    
    skill_vocab = {skill: idx for idx, skill in enumerate(unique_skills)}
    
    row_ind, col_ind, data_val = [], [], []
    for i, s_list in enumerate(df['skills_list']):
        for skill in s_list:
            if skill in skill_vocab:
                row_ind.append(i)
                col_ind.append(skill_vocab[skill])
                data_val.append(1.0)
                
    skills_matrix = sp.csr_matrix((data_val, (row_ind, col_ind)), shape=(len(df), len(unique_skills)))
    
    # 3. Metadata Matrix
    print("3. Build Metadata matrix...")
    # Location (One-hot)
    loc_dummies = pd.get_dummies(df['location'], prefix='loc')
    
    # Level (Ordinal)
    level_map = {"Khác": 0, "Fresher": 1, "Junior": 2, "Middle": 3, "Senior": 4, "Manager": 5}
    level_encoded = df['level'].map(level_map).fillna(0) / 5.0
    
    # Experience (MinMax)
    scaler = MinMaxScaler()
    exp_scaled = scaler.fit_transform(df[['experience_required']])
    
    meta_df = pd.concat([loc_dummies, level_encoded, pd.DataFrame(exp_scaled, columns=['exp'])], axis=1)
    meta_matrix = sp.csr_matrix(meta_df.values.astype(float))
    
    # 4. Combine
    print("4. Combine features (TFIDF: 0.5, Skills: 0.35, Meta: 0.15)...")
    tfidf_norm = normalize(tfidf_matrix, norm='l2', axis=1) * 0.5
    skills_norm = normalize(skills_matrix, norm='l2', axis=1) * 0.35
    meta_norm = normalize(meta_matrix, norm='l2', axis=1) * 0.15
    
    combined_matrix = sp.hstack([tfidf_norm, skills_norm, meta_norm], format='csr')
    
    # 5. Lưu kết quả
    print("5. Saving artifacts...")
    sp.save_npz("database/feature_matrix.npz", combined_matrix)
    
    with open("database/tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(tfidf, f)
        
    with open("database/skill_vocab.pkl", "wb") as f:
        pickle.dump(skill_vocab, f)
        
    meta_info = {
        "level_map": level_map,
        "location_columns": loc_dummies.columns.tolist(),
        "exp_scaler": scaler
    }
    with open("database/feature_metadata.pkl", "wb") as f:
        pickle.dump(meta_info, f)
        
    jobs_index = {str(job_id): idx for idx, job_id in enumerate(df['job_id'])}
    with open("database/jobs_index.pkl", "wb") as f:
        pickle.dump(jobs_index, f)
        
    # 6. In kết quả
    print("\n" + "="*40)
    print("--- 📊 KẾT QUẢ FEATURE ENGINEERING ---")
    print("="*40)
    print(f"TF-IDF shape    : {tfidf_matrix.shape}")
    print(f"Skills shape    : {skills_matrix.shape}")
    print(f"Meta shape      : {meta_matrix.shape}")
    print(f"Combined shape  : {combined_matrix.shape}")
    
    print("\n⭐ Top 20 skills phổ biến nhất:")
    skill_counts = pd.Series(all_skills).value_counts().head(20)
    print(skill_counts.to_string())

    print("\n🔠 Top 20 TF-IDF terms quan trọng nhất (average score):")
    # Lấy average tf-idf score của mỗi term
    avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
    feature_names = tfidf.get_feature_names_out()
    
    # Sort top 20
    top_indices = avg_scores.argsort()[::-1][:20]
    top_terms = [(feature_names[i], avg_scores[i]) for i in top_indices]
    
    for rank, (term, score) in enumerate(top_terms, 1):
        print(f"{rank:2d}. {term:<20} : {score:.4f}")

if __name__ == "__main__":
    build_features()
