"""重新加载 data 目录下的所有知识文件到 Chroma 向量库"""
"""使用 --clean 参数可先清除向量库再全量重建"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.vector_store_service import VectorStoreService

if __name__ == "__main__":
    import shutil
    clean = "--clean" in sys.argv
    if clean:
        from config.settings import settings
        db_dir = Path(settings.chroma_persist_dir)
        if db_dir.exists():
            shutil.rmtree(db_dir)
            print(f"[Clean] 已清除向量库: {db_dir}")
        rec_file = Path(settings.md5_hex_path)
        if rec_file.exists():
            rec_file.unlink()
            print("[Clean] 已清除处理记录")
    service = VectorStoreService()
    service.load_document()
    count = service.vector_store._collection.count()
    print(f"\n完成，向量库中共 {count} 个文档片段")
    if not clean:
        print("提示: 使用 --clean 可先清除向量库再全量重建")
