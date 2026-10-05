import subprocess
import sys

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"🚀 CHẠY BƯỚC: {script_name}")
    print(f"{'='*50}\n")
    
    result = subprocess.run([sys.executable, f"recommendation/{script_name}"])
    if result.returncode != 0:
        print(f"\n❌ Lỗi khi chạy {script_name}. Dừng pipeline.")
        sys.exit(1)
    
    print(f"\n✅ Hoàn thành {script_name}!\n")

def main():
    scripts = [
        "01_cleaning.py",
        "02_features.py",
        "03_model.py",
        "04_evaluate.py"
    ]
    
    for script in scripts:
        run_script(script)
        
    print("🎉 TẤT CẢ CÁC BƯỚC ĐÃ HOÀN THÀNH THÀNH CÔNG!")

if __name__ == "__main__":
    main()
