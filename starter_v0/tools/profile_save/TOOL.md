---
name: profile_save
track: bonus
kind: action
provider: local JSON file
requires_env: []
inputs: [field, value, action, confirmed]
outputs: [status, field, action, value, pending_value]
side_effect: local_file_write
requires_confirmation: true
---
# profile_save

Lưu hoặc sửa MỘT trường trong hồ sơ người dùng (cùng file với tool `profile`).

## Khi dùng / khi không dùng

- Người dùng tự yêu cầu lưu ("nhớ giúp mình là mình ở Huế") → gọi với `confirmed=true`.
- Sherlock tự nhận ra một thông tin cá nhân → hỏi `clarify(response_type="yes_no")` trước,
  chỉ lưu khi người dùng đồng ý.
- Không lưu thông tin nhạy cảm: họ tên đầy đủ, địa chỉ nhà, số điện thoại, email, sức khỏe, tài chính.

## Tham số

| Tham số | Ý nghĩa |
|---|---|
| `field` | `name`, `city`, `timezone`, `language`, `interests`, `followed_accounts` |
| `value` | Giá trị mới. Trường dạng danh sách nhận nhiều giá trị cách nhau bằng dấu phẩy. Rỗng + `set` = xóa trường |
| `action` | `set` thay toàn bộ; `add` / `remove` chỉ cho `interests`, `followed_accounts` |
| `confirmed` | Chỉ `true` (hoặc chuỗi `"true"`) mới ghi. Chuỗi `"false"` không được tính là xác nhận |

## Kiểm tra đầu vào

- Mỗi giá trị một dòng, tối đa 80 ký tự; danh sách tối đa 20 phần tử, tự bỏ trùng (không phân biệt hoa thường).
- `timezone` phải là tên IANA hợp lệ.
- `followed_accounts`: tự bỏ `@`, chỉ nhận chữ, số, `_`, tối đa 15 ký tự.

## Output

- Chưa xác nhận: `{"status": "needs_confirmation", "pending_value": ...}`, không ghi file.
- Đã ghi: `{"status": "saved", "field": "city", "value": "Huế"}`.
- Input sai: `{"ok": false, "error": "invalid_input", "message": ...}`, không ghi file.
