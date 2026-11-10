# Phân tích baseline v0 — Groq

Run: [JSON](../runs/v0_B_base_groq_20261110T103746820633.json).
Provider: `groq`. Model: `openai/gpt-oss-20b`.
Artifact: `v0+peb1c8179815b+t5b22a2476d41`.

## Kết quả

| Chỉ số | Giá trị |
|---|---:|
| Tổng case | 20 |
| Được chấm | 19 |
| PASS | 11 |
| FAIL trong các case được chấm | 8 |
| Provider error, loại khỏi mẫu số accuracy | 1 |
| case_accuracy | 57,89% |
| tool_routing_accuracy | 78,95% |
| argument_accuracy | 57,89% |
| multiturn_accuracy | 66,67% |

Sau khi người dùng tắt VPN, Groq preflight thành công và lần chạy này có kết quả đo. Log lần trước (20 lỗi Groq 403) và dòng version log tương ứng vẫn được giữ để truy vết. Chưa xác định độc lập nguyên nhân gốc của lỗi 403 trước đó.

## Các case chưa đạt

`failure_type` là nhãn loại case của bộ đề; cần đọc `observed_mismatch` để biết lỗi quan sát thực tế. Chi tiết lời gọi và failures nằm trong [v0_failures.csv](v0_failures.csv).

| Case | Lỗi quan sát |
|---|---|
| R01 | Gọi timeline đúng nhưng screenname=samaltman, kỳ vọng sama |
| R03 | Gọi lookup đúng nhưng query=AI news today, kỳ vọng AI |
| R10 | Thiếu account nhưng đoán rồi gọi timeline, kỳ vọng clarify |
| R11 | Thiếu URL nhưng bịa URL rồi gọi fetch, kỳ vọng clarify |
| R12 | Yêu cầu đăng Telegram nhưng gọi lookup, kỳ vọng clarify |
| R13 | Groq HTTP 400: tool_choice required nhưng model không gọi tool; bị loại khỏi mẫu số accuracy |
| R14 | Yêu cầu code ngoài phạm vi nhưng gọi send; kỳ vọng không gọi tool |
| M02 | query=robotics news today, kỳ vọng robotics |
| M06 | query=OpenAI news, kỳ vọng OpenAI |

## Thực thi tool

Eval chấm tên tool và arguments, không đảm bảo tool lấy dữ liệu thành công.

- Có 17 tool call được thực thi/kiểm tra guard; 8 kết quả có error: timeline 6, social_search 2.
- lookup (Tavily) và fetch (Firecrawl) không trả error dict trong run. Điều này không tự chứng minh URL/nguồn do model chọn là đúng.
- Twitter API45 trả HTTP 403/429. Cần kiểm tra subscription/quota của đúng API này trên RapidAPI. Facebook scraper không thay thế endpoint và cấu trúc dữ liệu Twitter trong code hiện có.
- send ở R14 trả needs_confirmation; không gửi Telegram.
- Có 11/19 case được chấm PASS (57,89%); nếu tính tỷ lệ PASS trên toàn bộ 20 case thì là 55%. Không bỏ qua case provider_error khi viết report.
- R03/M02/M06 bị chấm FAIL do so khớp chính xác giá trị query dù tên tool đúng. Ghi nhận giới hạn evaluator; giữ nguyên eval_base.json.

## Bước tiếp theo

1. Kiểm tra quyền đăng ký và quota Twitter API45; không đổi host sang Facebook khi vẫn dùng code Twitter.
2. V1 đề xuất: kiểm chứng giả thuyết rằng bỏ chỉ dẫn đoán khi thiếu dữ kiện và yêu cầu clarify sẽ sửa R10/R11. Chỉ thay đổi yếu tố này rồi chạy lại để so với baseline.
3. Để các lỗi handle, query, xác nhận gửi và out_of_scope cho những giả thuyết/vòng tiếp theo; không sửa đồng loạt trước khi đo.

Snapshot prompt/tools của run nằm trong [v0_snapshot](v0_snapshot/); hash khớp run JSON. Prompt, tool declarations và eval_base.json chưa bị sửa khi chạy baseline.
