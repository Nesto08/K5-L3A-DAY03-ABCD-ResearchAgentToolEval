---
name: profile
track: bonus
kind: local_knowledge
provider: local JSON file
requires_env: []
inputs: [fields]
outputs: [exists, profile, missing, privacy_note]
side_effect: false
---
# profile

Đọc hồ sơ người dùng đã lưu, để Sherlock cá nhân hóa câu trả lời (thời tiết nơi họ ở,
tin theo chủ đề họ quan tâm, bài của tài khoản họ hay theo dõi).

## Dữ liệu

File `starter_v0/user_profile/profile.json` (gitignored). Đổi file bằng biến môi trường
`SHERLOCK_PROFILE_PATH`, ví dụ trỏ vào bản sao của `user_profile/profile.example.json` khi chạy eval.

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `name` | chuỗi | tên gọi, không cần họ tên đầy đủ |
| `city` | chuỗi | `Hà Nội` |
| `timezone` | chuỗi IANA | `Asia/Ho_Chi_Minh` |
| `language` | chuỗi | `vi` |
| `interests` | danh sách | `["AI", "robotics"]` |
| `followed_accounts` | danh sách handle X, không có `@` | `["karpathy"]` |

Khóa nào khác trong file đều bị bỏ qua, không trả cho model.

## Khi dùng / khi không dùng

- Dùng khi yêu cầu phụ thuộc thông tin cá nhân mà câu chưa nói: "thời tiết hôm nay" (không nói ở
  đâu), "tin liên quan đến mình", "có gì mới không?" (lấy chủ đề quan tâm để gợi ý trong `clarify`).
- Không dùng khi câu đã đủ đối tượng ("tin AI hôm nay", "thời tiết Đà Nẵng").

## Output

```json
{"tool": "profile", "ok": true, "exists": true,
 "profile": {"city": "Hà Nội", "interests": ["AI"]},
 "missing": ["name"], "privacy_note": "..."}
```

`missing` liệt kê trường còn trống trong số trường được hỏi. File chưa có thì `exists=false`,
mọi trường đều nằm trong `missing`.

## Lỗi

- `invalid_input`: `fields` có tên trường không tồn tại.
- `JSONDecodeError` / `ValueError`: file hồ sơ hỏng. Tool trả error dict, không raise.

## Quyền riêng tư

Theo `company_policy/data-privacy-policy.md`: không gửi `name` ra tool web, mạng xã hội hay đọc URL.
Chỉ dùng `city`, `interests`, `followed_accounts` làm tham số cho tool khác.
