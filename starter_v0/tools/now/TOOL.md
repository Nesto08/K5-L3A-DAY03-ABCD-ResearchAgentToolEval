---
name: now
track: bonus
kind: local_knowledge
provider: system clock + zoneinfo
requires_env: []
inputs: [timezone]
outputs: [timezone, timezone_source, iso, date, time, weekday, utc_offset, yesterday, tomorrow, weekend]
side_effect: false
---
# now

Ngày giờ hiện tại theo múi giờ của người dùng. Model không tự biết hôm nay là ngày nào, nên tool này
giúp hiểu "hôm nay", "ngày mai", "cuối tuần" và ghi ngày lên tiêu đề bản tin.

## Chọn múi giờ

1. Tham số `timezone` nếu có (người dùng hỏi giờ ở nơi khác).
2. Trường `timezone` trong `profile`.
3. Mặc định `Asia/Ho_Chi_Minh`.

`timezone_source` cho biết đã lấy từ đâu: `argument`, `profile` hoặc `default`.

## Khi dùng / khi không dùng

- Dùng khi hỏi hôm nay ngày mấy, thứ mấy, mấy giờ, hoặc cần ngày cụ thể cho câu trả lời.
- Không cần gọi chỉ để chọn `timeframe` cho `lookup` ("hôm nay" là `timeframe=day`).

## Output

```json
{"tool": "now", "ok": true, "timezone": "Asia/Ho_Chi_Minh", "timezone_source": "default",
 "iso": "2026-11-10T12:30:00+07:00", "date": "2026-11-10", "time": "12:30", "weekday": "Thứ Ba",
 "utc_offset": "+07:00", "yesterday": "2026-11-09", "tomorrow": "2026-11-11",
 "weekend": {"saturday": "2026-11-14", "sunday": "2026-11-15"}}
```

Vào Chủ Nhật, `weekend` là hôm qua và hôm nay (cuối tuần đang diễn ra).

## Lỗi

- `invalid_input`: tên múi giờ không hợp lệ. Trên Windows cần gói `tzdata` (`pip install tzdata`).
- Hồ sơ hỏng không làm tool lỗi: tool bỏ qua hồ sơ và dùng múi giờ mặc định.
