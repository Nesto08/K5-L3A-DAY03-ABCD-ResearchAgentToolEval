---
name: weather
track: bonus
kind: live_api
provider: Open-Meteo (geocoding + forecast, không cần API key)
requires_env: []
inputs: [location, days]
outputs: [location, current, daily, items]
side_effect: false
---
# weather

Thời tiết hiện tại và dự báo 1–7 ngày cho một địa điểm.

## Cách chạy

1. `GET https://geocoding-api.open-meteo.com/v1/search?name=<location>&count=1&language=vi`
   lấy tọa độ. Tên có dấu hay không dấu đều được ("Hà Nội", "ha noi", "Hanoi").
2. `GET https://api.open-meteo.com/v1/forecast` với `current` (nhiệt độ, cảm giác, độ ẩm, mưa, gió,
   mã thời tiết) và `daily` (min/max, khả năng mưa), `timezone=auto`, `forecast_days=<days>`.
3. Đổi mã thời tiết WMO sang mô tả tiếng Việt.

## Khi dùng / khi không dùng

- Dùng khi hỏi thời tiết, nhiệt độ, có mưa không, và đã biết địa điểm (người dùng nói, hoặc `city`
  trong `profile`).
- Không dùng khi chưa biết địa điểm (gọi `profile` hoặc `clarify`), hoặc khi hỏi tin bão lũ, thiên tai
  (dùng `lookup` với `topic=news`).

## Tham số

- `location`: tên thành phố hoặc địa danh, tối đa 100 ký tự. Chỉ tên thành phố, không ghi địa chỉ nhà.
- `days`: 1–7, tính cả hôm nay. Nhận cả số dạng chuỗi; ngoài khoảng thì bị kẹp về 1 hoặc 7.

## Output

`location`, `current`, `daily[]`, và `items[0]` theo khuôn chung `{title, url, source, summary}`
để đưa thẳng vào `format`.

## Lỗi

- `invalid_input`: `location` rỗng hoặc quá dài. Không gọi mạng.
- `location_not_found`: geocoding không tìm thấy địa danh. Nên hỏi lại người dùng.
- `HTTPError` / lỗi mạng: trả error dict, không raise.

Open-Meteo miễn phí cho mục đích phi thương mại, giới hạn khoảng 10.000 lượt gọi mỗi ngày.
