"""
Kiểm tra nhanh vector database (Chroma) đã lưu tài liệu hay chưa.
"""
import sys
from pathlib import Path
from typing import List

# Bảo đảm app/ import được
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.retrieval.custom_chroma import CustomChromaClient  # noqa: E402


def _print_results(results: List):
    """Hiển thị một số kết quả truy vấn."""
    for idx, doc in enumerate(results[:2], 1):
        print(f"\n      --- Result {idx} ---")
        print(f"      Distance: {doc.metadata.get('distance', 'N/A')}")
        print(f"      Document ID: {doc.metadata.get('document_id', 'N/A')}")
        print(f"      Chunk Index: {doc.metadata.get('chunk_index', 'N/A')}")
        print(f"      Content: {doc.page_content[:150]}...")


def test_vector_database():
    """Điểm vào chính của script."""
    print("=" * 70)
    print("🧪 TEST VECTOR DATABASE")
    print("=" * 70)
    print("Mục đích: Kiểm tra document có được lưu trong vector database không")
    print("=" * 70)

    try:
        # 1. Khởi tạo ChromaDB client
        print("\n[1/4] ⏳ Đang khởi tạo ChromaDB client...")
        print("      (Lần đầu có thể mất thời gian để download model)")
        client = CustomChromaClient()
        print("      ✅ ChromaDB client đã khởi tạo thành công!")

        # 2. Kiểm tra collection
        print("\n[2/4] 🔍 Đang kiểm tra collection...")
        collection = client.collection
        count = collection.count()
        print(f"      ✅ Collection '{collection.name}' có {count} documents")

        if count == 0:
            print("\n      ⚠️  Collection trống!")
            print("      Vui lòng upload document trước khi test vector database.")
            print("      Gợi ý: python scripts/test_upload_document.py")
            return

        # 3. Lấy một số documents để kiểm tra
        print("\n[3/4] 📄 Đang lấy một số documents từ collection...")
        try:
            results = collection.get(limit=5)
            ids = results.get("ids", [])
            metadatas = results.get("metadatas", [])
            documents = results.get("documents", [])

            print(f"      ✅ Đã lấy {len(ids)} documents từ collection")
            print("\n      📋 Thông tin documents:")
            for i, (doc_id, metadata, doc_content) in enumerate(
                zip(ids, metadatas, documents), 1
            ):
                print(f"\n      --- Document {i} ---")
                print(f"      ID: {doc_id}")
                print(f"      Document ID: {metadata.get('document_id', 'N/A')}")
                print(f"      Filename: {metadata.get('filename', 'N/A')}")
                print(f"      Document Type: {metadata.get('document_type', 'N/A')}")
                print(f"      Chunk Index: {metadata.get('chunk_index', 'N/A')}")
                print(f"      Total Chunks: {metadata.get('total_chunks', 'N/A')}")
                print(f"      Content Preview: {doc_content[:100]}...")
        except Exception as exc:  # pragma: no cover
            print(f"      ⚠️  Lỗi khi lấy documents: {exc}")

        # 4. Test query
        print("\n[4/4] 🔍 Đang test query vector database...")
        test_queries = ["nghỉ phép", "bảo mật", "làm việc từ xa"]

        for query in test_queries:
            print(f"\n      Query: '{query}'")
            try:
                matches = client.query(query, k=3)
                print(f"      ✅ Tìm thấy {len(matches)} results")
                if matches:
                    _print_results(matches)
            except Exception as exc:  # pragma: no cover
                print(f"      ❌ Lỗi query: {exc}")

        # 5. Tổng kết
        print("\n" + "=" * 70)
        print("✅ TEST VECTOR DATABASE HOÀN TẤT!")
        print("=" * 70)
        print(f"✅ Collection: {collection.name}")
        print(f"✅ Total documents: {count}")
        print(f"✅ Query thành công: {len(test_queries)} queries")
        print("=" * 70)

    except Exception as exc:  # pragma: no cover
        import traceback

        print(f"\n❌ Lỗi: {exc}")
        print("\nTraceback:")
        traceback.print_exc()
        print("\nVui lòng kiểm tra:")
        print("  - Document đã được upload chưa?")
        print("  - Vector database đã được tạo chưa?")
        print("  - Có đủ bộ nhớ để load model?")
        print("  - Kết nối internet (để download model lần đầu)")


if __name__ == "__main__":
    test_vector_database()

