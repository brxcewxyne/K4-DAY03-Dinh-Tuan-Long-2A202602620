# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đinh Tuấn Long  
> **Mã Sinh Viên / Mã Học viên:** 2A202602620  
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Tra cứu Lịch thi VinUni  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Một số yêu cầu cần thực hiện nhiều bước nối tiếp, ví dụ tra cứu hồ sơ sinh viên, xác định cố vấn phụ trách rồi mới đặt lịch tư vấn. Tuy nhiên, phần lớn tác vụ vẫn có quy trình tương đối ngắn và rõ ràng. |
| **2. Tool Interaction** | 5 / 5 | Agent bắt buộc kết nối MCP Server để gọi công cụ tra cứu dữ liệu học vụ và đặt lịch. Nếu không dùng công cụ, mô hình không có dữ liệu sinh viên cập nhật và không thể thực hiện hành động đặt lịch. |
| **3. Dynamic Decision** | 4 / 5 | Agent phải quyết định trả lời trực tiếp hay gọi công cụ dựa trên yêu cầu của người dùng. Trong tác vụ nhiều bước, hành động tiếp theo còn phụ thuộc vào kết quả tra cứu, chẳng hạn chỉ đặt lịch sau khi tìm được sinh viên và tên cố vấn. |
| **4. Long Horizon Goal** | 3 / 5 | Agent cần duy trì mục tiêu của người dùng qua nhiều bước Thought, Action và Observation, nhưng phiên xử lý thường ngắn, giới hạn trong một yêu cầu học vụ hoặc đặt lịch cụ thể. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | Bài toán đạt trên 12/20, phù hợp triển khai Agentic System vì cần sử dụng công cụ, ra quyết định động và xử lý tác vụ nhiều bước. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026002, sau đó đặt lịch tư vấn với đúng cố vấn đó vào lúc 09:00 ngày 16/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "data": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.6,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
      }
    },
    "provider": "OpenAIProvider",
    "model": "gpt-4o-mini",
    "fallback_path": [
      {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "result": "SUCCESS"
      }
    ],
    "api_provider_status": {
      "gemini": {
        "provider": "GeminiProvider",
        "model": "gemini-3.5-flash-lite",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 5,
        "successes": 5,
        "failures": 0,
        "last_error": null
      },
      "openai": {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 1,
        "successes": 1,
        "failures": 0,
        "last_error": null
      }
    },
    "latency_ms": 3354.18
  },
  {
    "step": 2,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026002, sau đó đặt lịch tư vấn với đúng cố vấn đó vào lúc 09:00 ngày 16/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "SV2026002",
      "datetime_str": "09:00 16/09/2026",
      "advisor_name": "TS. Lê Thị B"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026002-99",
      "student_id": "SV2026002",
      "datetime": "09:00 16/09/2026",
      "advisor": "TS. Lê Thị B",
      "message": "Đặt lịch thành công cho sinh viên SV2026002 với TS. Lê Thị B vào lúc 09:00 16/09/2026."
    },
    "provider": "OpenAIProvider",
    "model": "gpt-4o-mini",
    "fallback_path": [
      {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "result": "SUCCESS"
      }
    ],
    "api_provider_status": {
      "gemini": {
        "provider": "GeminiProvider",
        "model": "gemini-3.5-flash-lite",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 5,
        "successes": 5,
        "failures": 0,
        "last_error": null
      },
      "openai": {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 2,
        "successes": 2,
        "failures": 0,
        "last_error": null
      }
    },
    "latency_ms": 1450.45
  },
  {
    "step": 3,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026002, sau đó đặt lịch tư vấn với đúng cố vấn đó vào lúc 09:00 ngày 16/09/2026.",
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Yêu cầu của bạn đã được hoàn thành. Tôi đã tra cứu và xác định cố vấn học tập của sinh viên SV2026002 là TS. Lê Thị B. Sau đó, tôi cũng đã đặt lịch tư vấn thành công với TS. Lê Thị B vào lúc 09:00 ngày 16/09/2026. \n\nThông tin đặt lịch như sau:\n- Sinh viên: SV2026002\n- Cố vấn: TS. Lê Thị B\n- Thời gian hẹn: 09:00 ngày 16/09/2026\n- Mã đặt lịch: BK-SV2026002-99\n\nNếu bạn cần thêm thông tin hay hỗ trợ gì khác, hãy cho tôi biết!",
    "provider": "OpenAIProvider",
    "model": "gpt-4o-mini",
    "fallback_path": [
      {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "result": "SUCCESS"
      }
    ],
    "api_provider_status": {
      "gemini": {
        "provider": "GeminiProvider",
        "model": "gemini-3.5-flash-lite",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 5,
        "successes": 5,
        "failures": 0,
        "last_error": null
      },
      "openai": {
        "provider": "OpenAIProvider",
        "model": "gpt-4o-mini",
        "configured": true,
        "state": "HEALTHY",
        "attempts": 3,
        "successes": 3,
        "failures": 0,
        "last_error": null
      }
    },
    "latency_ms": 2274.77
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
