# Day 03 Lab v2 Report — Sherlock

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: <!-- ABCD -->
- Members: <!-- Dũng, Duy, Đức, Khương -->
- Provider/model: OpenRouter, `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Sherlock** là agent hỗ trợ research và tìm kiếm thông tin: tìm tin trên web, xem tweet theo tài khoản hoặc theo chủ đề, đọc và tóm tắt URL, tìm và đọc paper arXiv, tra policy nội bộ công ty. Sherlock tổng hợp kết quả thành bản tin có nguồn và chỉ gửi lên Telegram khi người dùng đã xác nhận. Ngoài ra Sherlock xem được thời tiết, ngày giờ, và nhớ hồ sơ người dùng (thành phố, chủ đề quan tâm) để cá nhân hóa câu trả lời.

**Link dùng thử (deploy):**

> URL: <!-- TODO: dán link trycloudflare.com khi chạy tunnel -->

## A2. Tool agent có

15 tool: 6 tool lõi, 4 tool bonus có sẵn, 4 tool nhóm tự viết.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng một câu khi thiếu thông tin, hoặc xin xác nhận trước khi gửi Telegram | không |
| timeline | Lấy các tweet gần nhất của một tài khoản X cụ thể | không |
| social_search | Tìm tweet theo chủ đề hoặc từ khóa, từ nhiều tài khoản | không |
| lookup | Tìm kiếm web (tin tức, thông tin công khai), trả về link và tóm tắt | không |
| fetch | Đọc nội dung một URL người dùng đưa | không |
| format | Trình bày kết quả đã thu thập thành bản tin markdown (brief, bullets, thread, ...) | không |
| send | Đăng văn bản lên kênh Telegram, chỉ chạy khi người dùng đã đồng ý | không |
| policy | Tra policy nội bộ công ty, trả về đoạn quy định kèm nguồn và ngày hiệu lực | không |
| papers | Tìm paper trên arXiv theo chủ đề | không |
| paper_text | Tải PDF một paper arXiv và trích text vài trang đầu | không |
| **profile** | Đọc hồ sơ người dùng: tên gọi, thành phố, múi giờ, chủ đề quan tâm, tài khoản hay theo dõi | **có** |
| **profile_save** | Lưu hoặc sửa một trường trong hồ sơ, chỉ khi người dùng muốn lưu | **có** |
| **weather** | Thời tiết hiện tại và dự báo 1–7 ngày cho một thành phố | **có** |
| **now** | Ngày giờ hiện tại theo múi giờ người dùng hoặc múi giờ khác | **có** |

## A3. Câu hỏi mẫu để thử

Các câu dưới đây đã chạy thật với prompt và tools v2 (`v2+p34f5ac3322b4+t5a5f849734c9`), mỗi câu có transcript trong `transcripts/`.

| # | Câu hỏi | Sherlock gọi | Transcript |
|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? Làm thành bản tin ngắn giúp mình. | `lookup` (topic=news, timeframe=day) rồi `format` | `v2_openrouter_20261110T152139783280` |
| 2 | Tìm 3 paper arXiv về đánh giá retrieval augmented generation | `papers` (max_results=3) | `v2_openrouter_20261110T152306703336` |
| 3 | Thời tiết Đà Nẵng cuối tuần này thế nào, có mưa không? | `weather` (days=7) | `v2_openrouter_20261110T152237158923` |
| 4 | Theo policy công ty, tweet viral có được dùng làm nguồn trích dẫn không? | `policy` (policy_area=source_citation) | `v2_openrouter_20261110T152247602955` |
| 5 | Hôm nay thứ mấy, ngày bao nhiêu? Bây giờ ở Tokyo mấy giờ? | `now` hai lần (múi giờ mặc định, rồi Asia/Tokyo) | `v2_openrouter_20261110T152323804459` |

Thử thêm guardrail: gõ "Đăng bản tin này lên Telegram". Sherlock phải hỏi lại để xác nhận (`clarify`, yes_no) trước khi gọi `send`.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

### B3 bổ sung — Eval 4 tool nhóm

Ngoài bộ group 10 case, nhóm yêu cầu thêm **20 prompt: 5 case cho mỗi tool `weather`, `now`, `profile`, `profile_save`**. Suite bổ sung gồm 10 single turn và 10 multi turn, không thay đổi các case trong `data/eval_group.json`.

| Tool | Single turn | Multi turn | Tổng |
|---|---:|---:|---:|
| weather | 3 | 2 | 5 |
| now | 2 | 3 | 5 |
| profile | 3 | 2 | 5 |
| profile_save | 2 | 3 | 5 |

Case và expected behavior: [`data/eval_team_tools.json`](../data/eval_team_tools.json). Ma trận, cách chạy và giới hạn: [hướng dẫn suite](../data/README_team_tools.md). Runner tạo hồ sơ giả riêng từng case và kiểm tra dữ liệu sau lưu; không ghi hồ sơ thật.

Hai lần chạy live đã được giữ log: OpenRouter / gpt-4o-mini bị 403 “model not available in your region”; Groq / gpt-oss-20b bị 403 “Forbidden”. Cả hai có `measured_cases=0`, vì vậy **chưa có điểm chất lượng model cho bộ này**. Xem [log, CSV và trạng thái](../analysis/team_tools_eval/README.md). Cần chạy lại khi provider/model có quyền truy cập.

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
