import re

with open('recommendation/03_model.py', 'r') as f:
    content = f.read()

# Replace "database/..." with os.path.join(base_dir, "database/...")
new_init = """    def __init__(self):
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
            
        self.id_to_idx = {str(k): int(v) for k, v in self.jobs_index.items()}"""

# We need to replace the __init__ method body
pattern = re.compile(r'    def __init__\(self\):.*?self\.id_to_idx = {str\(k\): int\(v\) for k, v in self\.jobs_index\.items\(\)}', re.DOTALL)
content = pattern.sub(new_init, content)

with open('recommendation/03_model.py', 'w') as f:
    f.write(content)
