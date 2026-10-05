import pandas as pd
import numpy as np
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import json
import random
import time
import importlib.util

# Load JobRecommender class
spec = importlib.util.spec_from_file_location("model", "recommendation/03_model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
JobRecommender = model.JobRecommender

# --- Metrics ---

def precision_at_k(recommended_ids: list, relevant_ids: set, k: int) -> float:
    if k == 0 or not recommended_ids: return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for j in top_k if j in relevant_ids)
    return hits / k

def recall_at_k(recommended_ids: list, relevant_ids: set, k: int) -> float:
    if not relevant_ids or not recommended_ids: return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for j in top_k if j in relevant_ids)
    return hits / len(relevant_ids)

def ndcg_at_k(recommended_ids: list, relevant_ids: set, k: int) -> float:
    if not relevant_ids or not recommended_ids: return 0.0
    top_k = recommended_ids[:k]
    dcg = 0.0
    for i, j in enumerate(top_k):
        if j in relevant_ids:
            dcg += 1.0 / np.log2(i + 2) # i is 0-indexed, so i+2 starts at log2(2)=1
    
    # IDCG (Ideal DCG)
    idcg = 0.0
    ideal_hits = min(len(relevant_ids), k)
    for i in range(ideal_hits):
        idcg += 1.0 / np.log2(i + 2)
        
    return dcg / idcg if idcg > 0 else 0.0

def coverage(all_recommended_ids: set, total_jobs: int) -> float:
    if total_jobs == 0: return 0.0
    return len(all_recommended_ids) / total_jobs

def intra_list_diversity(recommended_job_ids: list, feature_matrix: sp.csr_matrix, jobs_index: dict) -> float:
    if len(recommended_job_ids) < 2: return 0.0
    
    indices = [jobs_index[str(jid)] for jid in recommended_job_ids if str(jid) in jobs_index]
    if len(indices) < 2: return 0.0
    
    sub_matrix = feature_matrix[indices]
    sims = cosine_similarity(sub_matrix)
    
    # Average pairwise similarity (upper triangle excluding diagonal)
    n = sims.shape[0]
    sum_sims = (sims.sum() - n) / 2.0
    pairs = (n * (n - 1)) / 2.0
    
    avg_sim = sum_sims / pairs if pairs > 0 else 0.0
    return 1.0 - avg_sim

# --- Evaluation ---

def evaluate_model(rec: JobRecommender, test_jobs: pd.DataFrame, model_name: str) -> dict:
    metrics = {k: {"p": [], "r": [], "ndcg": [], "div": []} for k in [5, 10, 20]}
    all_recs = {5: set(), 10: set(), 20: set()}
    
    total_jobs = len(rec.jobs_df)
    
    for _, job in test_jobs.iterrows():
        cv_text = job['full_text']
        job_id = job['job_id']
        
        # Lấy full vector để tìm relevant (Pseudo ground truth)
        query_vec = rec._build_query_vector(cv_text)
        sim_scores = cosine_similarity(query_vec, rec.feature_matrix).flatten()
        
        relevant_indices = np.where(sim_scores > 0.3)[0]
        relevant_jobs = set(rec.jobs_df.iloc[relevant_indices]['job_id'].values)
        relevant_jobs.discard(job_id) # Không tính chính nó
        
        if not relevant_jobs:
            continue
            
        # Recommend top 20
        top_indices = sim_scores.argsort()[::-1]
        top_indices = [idx for idx in top_indices if rec.jobs_df.iloc[idx]['job_id'] != job_id][:20]
        top_jobs = rec.jobs_df.iloc[top_indices]['job_id'].tolist()
        
        for k in [5, 10, 20]:
            top_k = top_jobs[:k]
            metrics[k]["p"].append(precision_at_k(top_k, relevant_jobs, k))
            metrics[k]["r"].append(recall_at_k(top_k, relevant_jobs, k))
            metrics[k]["ndcg"].append(ndcg_at_k(top_k, relevant_jobs, k))
            metrics[k]["div"].append(intra_list_diversity(top_k, rec.feature_matrix, rec.jobs_index))
            all_recs[k].update(top_k)
            
    # Tóm tắt
    results = {}
    for k in [5, 10, 20]:
        results[k] = {
            "Precision": np.mean(metrics[k]["p"]) if metrics[k]["p"] else 0,
            "Recall": np.mean(metrics[k]["r"]) if metrics[k]["r"] else 0,
            "NDCG": np.mean(metrics[k]["ndcg"]) if metrics[k]["ndcg"] else 0,
            "Coverage": coverage(all_recs[k], total_jobs),
            "Diversity": np.mean(metrics[k]["div"]) if metrics[k]["div"] else 0
        }
    return results

def rebuild_feature_matrix(rec: JobRecommender, w_tfidf, w_skills, w_meta):
    """Rebuild the internal feature matrix with new weights inline"""
    print(f"Rebuilding matrix with weights: TFIDF={w_tfidf}, Skills={w_skills}, Meta={w_meta}...")
    
    # We must rebuild from raw jobs_df because the saved matrix is already weighted.
    # Fortunately, we can just use TFIDF transform and skill matching for all jobs.
    # Actually, calculating for 2000 jobs inline takes about 5 seconds.
    
    # 1. TF-IDF
    tfidf_mat = rec.tfidf.transform(rec.jobs_df['full_text'])
    
    # 2. Skills
    row_ind, col_ind, data_val = [], [], []
    for i, s_list in enumerate(rec.jobs_df['skills_list']):
        for skill in s_list:
            if skill in rec.skill_vocab:
                row_ind.append(i)
                col_ind.append(rec.skill_vocab[skill])
                data_val.append(1.0)
    skills_mat = sp.csr_matrix((data_val, (row_ind, col_ind)), shape=(len(rec.jobs_df), len(rec.skill_vocab)))
    
    # 3. Meta
    loc_dummies = pd.get_dummies(rec.jobs_df['location'], prefix='loc')
    # Make sure columns match
    for c in rec.meta_info['location_columns']:
        if c not in loc_dummies: loc_dummies[c] = False
    loc_dummies = loc_dummies[rec.meta_info['location_columns']]
    
    level_encoded = rec.jobs_df['level'].map(rec.meta_info['level_map']).fillna(0) / 5.0
    exp_scaled = rec.meta_info['exp_scaler'].transform(rec.jobs_df[['experience_required']])
    meta_df = pd.concat([loc_dummies, level_encoded, pd.DataFrame(exp_scaled, columns=['exp'])], axis=1)
    meta_mat = sp.csr_matrix(meta_df.values.astype(float))
    
    # Normalize & Combine
    tf_norm = normalize(tfidf_mat, norm='l2', axis=1) * w_tfidf
    sk_norm = normalize(skills_mat, norm='l2', axis=1) * w_skills
    mt_norm = normalize(meta_mat, norm='l2', axis=1) * w_meta
    
    rec.feature_matrix = sp.hstack([tf_norm, sk_norm, mt_norm], format='csr')
    
    # MUST patch _build_query_vector to use new weights!
    original_build = rec._build_query_vector
    def new_build(cv_text):
        # We need to extract the raw norms before weighting. 
        # Since _build_query_vector does weighting inside, we override it.
        cv_tfidf = rec.tfidf.transform([cv_text])
        cv_lower = cv_text.lower()
        r, c, d = [], [], []
        for skill, idx in rec.skill_vocab.items():
            if skill in cv_lower:
                r.append(0); c.append(idx); d.append(1.0)
        cv_skills = sp.csr_matrix((d, (r, c)), shape=(1, len(rec.skill_vocab)))
        
        meta_row = np.zeros(len(rec.meta_info['location_columns']) + 2)
        loc_cols = rec.meta_info['location_columns']
        if "hà nội" in cv_lower: loc_idx = loc_cols.index('loc_Hà Nội') if 'loc_Hà Nội' in loc_cols else 1
        elif "hồ chí minh" in cv_lower or "hcm" in cv_lower: loc_idx = loc_cols.index('loc_TP.HCM') if 'loc_TP.HCM' in loc_cols else 1
        elif "đà nẵng" in cv_lower: loc_idx = loc_cols.index('loc_Đà Nẵng') if 'loc_Đà Nẵng' in loc_cols else 1
        else: loc_idx = loc_cols.index('loc_Khác') if 'loc_Khác' in loc_cols else 1
        meta_row[loc_idx] = 1.0
        meta_row[-2] = 3.0 / 5.0
        meta_row[-1] = rec.meta_info['exp_scaler'].transform([[2.0]])[0][0]
        cv_meta = sp.csr_matrix(meta_row)
        
        t = normalize(cv_tfidf, norm='l2', axis=1) * w_tfidf
        s = normalize(cv_skills, norm='l2', axis=1) * w_skills
        m = normalize(cv_meta, norm='l2', axis=1) * w_meta
        return sp.hstack([t, s, m], format='csr')
        
    rec._build_query_vector = new_build

def print_markdown_table(results, model_name):
    print(f"\n### {model_name}\n")
    print("| Metric        | K=5   | K=10  | K=20  |")
    print("|---------------|-------|-------|-------|")
    
    m_p = [results[k]['Precision'] for k in [5,10,20]]
    print(f"| Precision@K   | {m_p[0]:.3f} | {m_p[1]:.3f} | {m_p[2]:.3f} |")
    
    m_r = [results[k]['Recall'] for k in [5,10,20]]
    print(f"| Recall@K      | {m_r[0]:.3f} | {m_r[1]:.3f} | {m_r[2]:.3f} |")
    
    m_n = [results[k]['NDCG'] for k in [5,10,20]]
    print(f"| NDCG@K        | {m_n[0]:.3f} | {m_n[1]:.3f} | {m_n[2]:.3f} |")
    
    m_c = [results[k]['Coverage']*100 for k in [5,10,20]]
    print(f"| Coverage      | {m_c[0]:.1f}% | {m_c[1]:.1f}% | {m_c[2]:.1f}% |")
    
    m_d = [results[k]['Diversity'] for k in [5,10,20]]
    print(f"| Diversity     | {m_d[0]:.3f} | {m_d[1]:.3f} | {m_d[2]:.3f} |")

def main():
    print("Khởi tạo Recommender System...")
    rec = JobRecommender()
    
    random.seed(42)
    test_jobs = rec.jobs_df.sample(100, random_state=42)
    
    print("\n[ĐÁNH GIÁ MODEL A] - Trọng số: TF-IDF=0.5, Skills=0.35, Meta=0.15")
    rebuild_feature_matrix(rec, 0.5, 0.35, 0.15)
    start = time.time()
    res_A = evaluate_model(rec, test_jobs, "Model A")
    print(f"Thời gian đánh giá Model A: {time.time() - start:.1f}s")
    
    print("\n[ĐÁNH GIÁ MODEL B] - Trọng số: TF-IDF=0.3, Skills=0.55, Meta=0.15")
    rebuild_feature_matrix(rec, 0.3, 0.55, 0.15)
    start = time.time()
    res_B = evaluate_model(rec, test_jobs, "Model B")
    print(f"Thời gian đánh giá Model B: {time.time() - start:.1f}s")
    
    print("\n" + "="*50)
    print("BẢNG KẾT QUẢ SO SÁNH")
    print("="*50)
    print_markdown_table(res_A, "Model A: (TF-IDF=0.5, Skills=0.35)")
    print_markdown_table(res_B, "Model B: (TF-IDF=0.3, Skills=0.55)")
    
    ndcg10_A = res_A[10]['NDCG']
    ndcg10_B = res_B[10]['NDCG']
    
    print("\n🏆 KẾT LUẬN:")
    if ndcg10_A > ndcg10_B:
        print(f"Model A TỐT HƠN theo NDCG@10 ({ndcg10_A:.3f} > {ndcg10_B:.3f})")
    elif ndcg10_B > ndcg10_A:
        print(f"Model B TỐT HƠN theo NDCG@10 ({ndcg10_B:.3f} > {ndcg10_A:.3f})")
    else:
        print("Hai model tương đương nhau theo NDCG@10.")
        
    # Lưu file
    output = {"Model_A": res_A, "Model_B": res_B}
    with open("database/evaluation_results.json", "w") as f:
        json.dump(output, f, indent=4)
    print("\nĐã lưu kết quả vào database/evaluation_results.json")

if __name__ == "__main__":
    main()
