import google.generativeai as genai

# 🔥 DÁN API KEY CỦA BẠN VÀO ĐÂY 🔥
MY_API_KEY = "AIzaSyC2LbM3ljdtcIAm5OBY0PPVsZylnDE2o6U" 

def list_models_safe():
    if not MY_API_KEY or "DÁN_KEY" in MY_API_KEY:
        print("❌ Lỗi: Bạn chưa điền API Key vào code!")
        return

    try:
        genai.configure(api_key=MY_API_KEY)
        print("\n🔄 Đang lấy danh sách Model từ Google...")
        print("=" * 40)
        
        found = False
        for m in genai.list_models():
            # Chỉ lấy các model hỗ trợ tạo nội dung text/ảnh
            if 'generateContent' in m.supported_generation_methods:
                # In thẳng tên model ra (Đây là cái bạn cần copy)
                print(f"👉 {m.name}")
                found = True
        
        print("=" * 40)
        
        if found:
            print("✅ Xong! Hãy copy một dòng bắt đầu bằng 'models/...'")
            print("và dán vào biến MODEL_NAME trong tool dịch.")
        else:
            print("⚠️ Không tìm thấy model nào khả dụng.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    list_models_safe()