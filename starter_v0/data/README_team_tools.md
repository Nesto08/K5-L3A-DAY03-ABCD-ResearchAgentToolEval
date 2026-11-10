# Eval bổ sung cho 4 tool nhóm

File: [eval_team_tools.json](eval_team_tools.json).

Theo yêu cầu nhóm, suite này có **20 prompt: mỗi tool 5 case**, tổng **10 single turn + 10 multi turn**. README lab chỉ yêu cầu 10 case cho toàn bộ eval nhóm; không quy định 5 case/tool. Bộ [eval_group.json](eval_group.json) gồm 10 case hiện có được giữ nguyên.

| Tool được kiểm tra | Single turn | Multi turn | Tổng |
|---|---:|---:|---:|
| weather | 3 | 2 | 5 |
| now | 2 | 3 | 5 |
| profile | 3 | 2 | 5 |
| profile_save | 2 | 3 | 5 |
| **Tổng** | **10** | **10** | **20** |

Các case bao gồm cả khi nên gọi tool và khi không nên gọi. Vì vậy `metadata.tool` là tool đang được kiểm tra, không nhất thiết là tên tool nằm trong `expect` của case phủ định.

## Nội dung từng case

| ID | Tool mục tiêu | Hành vi mong đợi |
|---|---|---|
| TT_W01 | weather | Thành phố rõ ràng, hôm nay → weather days=1, không đọc/lưu profile |
| TT_W02 | weather | Dự báo 7 ngày → giữ nguyên thành phố và days=7 |
| TT_W03 | weather | Thiếu địa điểm → profile trước, không đoán city |
| TT_W04 | weather | Sau clarify, giữ “cuối tuần” và city mới → days=7 theo contract |
| TT_W05 | weather | Sửa thành phố, giữ số ngày; không lưu hồ sơ |
| TT_N01 | now | Đọc giờ theo profile/default, để timezone mặc định |
| TT_N02 | now | Truyền đúng múi giờ IANA được chỉ định |
| TT_N03 | now | Giữ timezone từ lượt trước khi hỏi “ở đó” |
| TT_N04 | now | Timezone mới thay timezone cũ, không lưu ngầm |
| TT_N05 | now | Lời cảm ơn → không gọi lại tool |
| TT_P01 | profile | Chỉ đọc city |
| TT_P02 | profile | Chỉ đọc interests và followed_accounts |
| TT_P03 | profile | Đã có city trong câu → weather trực tiếp, không profile |
| TT_P04 | profile | Đổi từ thời tiết sang đọc interests → profile |
| TT_P05 | profile | City đã đọc trong hội thoại → dùng lại, không đọc profile lần nữa |
| TT_S01 | profile_save | Chủ động yêu cầu lưu city → confirmed=true và ghi đúng dữ liệu |
| TT_S02 | profile_save | Yêu cầu lưu số điện thoại giả → không gọi tool, không đổi hồ sơ |
| TT_S03 | profile_save | Đồng ý lưu timezone → lưu đúng giá trị, không hỏi lặp |
| TT_S04 | profile_save | Đồng ý thêm interests → action=add, giữ danh sách cũ |
| TT_S05 | profile_save | Từ chối lưu → không gọi tool, hồ sơ không đổi |

ID đầy đủ và toàn bộ prompt, turns, expected args có trong JSON. Case TT_W04 bổ sung coverage cho lỗi G07 hiện tại; không thay đổi kỳ vọng của G07 để làm điểm tăng.

## Cách chạy

Từ `starter_v0/`, kích hoạt venv và điền key provider trong `.env`:

```powershell
python -m pytest -q
python scripts/preflight_provider.py --provider groq --model openai/gpt-oss-20b
```

Khi preflight thành công, chạy:

```powershell
python scripts/run_team_tools_eval.py --provider groq --model openai/gpt-oss-20b --version v2-team-tools-r2
```

Script dùng prompt/tools hiện tại. Khi chạy vòng mới, giữ nguyên bộ đề và model để so sánh; thay nhãn `--version` cho đúng cấu hình được đo. Không dùng `auto` hoặc provider fallback cho phép so sánh này.

Có thể thay bằng `--provider openrouter --model openai/gpt-4o-mini` nếu tài khoản có quyền dùng model đó. Hai lần chạy ban đầu bằng OpenRouter và Groq đều bị 403; xem [kết quả và giới hạn](../analysis/team_tools_eval/README.md). Chuyển provider/model là kiểm tra cấu hình khác, không phải bằng chứng một prompt tốt hơn.

**Dùng runner riêng ở trên.** `run_eval.py` thông thường sẽ từ chối suite có `requires_isolated_profile=true` để tránh ghi nhầm hồ sơ thật.

Runner:

- Tạo hồ sơ giả mới cho từng case qua `SHERLOCK_PROFILE_PATH`, khôi phục biến môi trường và dọn hồ sơ tạm khi xong.
- Dùng `profile_fixture` của dataset, hoặc fixture riêng của case nếu có. Không đọc/lưu hồ sơ thật của người dùng.
- Cung cấp toàn bộ khai báo tool cho model để phát hiện gọi nhầm; chỉ thực thi `weather`, `now`, `profile`, `profile_save`, `clarify`. Các tool khác được ghi nhận và chấm routing nhưng không được thực thi, đặc biệt là `send`.
- Dùng cách chấm args/default của `run_eval.py` hiện tại.
- Kiểm tra cả trạng thái hồ sơ sau case. Mặc định hồ sơ phải không đổi; chỉ các case có `expect.profile_updates` mới được thay đổi các trường được chỉ định.
- Ghi run JSON mới trong `runs/`, có `suite=team_tools`, hash prompt/tools, kết quả từng case, tool result và `profile_state` trước/sau.

## Cách đọc kết quả

- `summary.case_accuracy`, `tool_routing_accuracy`, `argument_accuracy`, `multiturn_accuracy`: điểm gọi tool theo evaluator hiện tại. Lỗi provider được báo riêng và không nằm trong mẫu số accuracy này.
- `summary.tool_execution_error_cases`: số case có tool error hoặc lời gọi bị chặn vì ngoài phạm vi thực thi suite.
- `summary.profile_state_accuracy`: tỉ lệ case có hồ sơ sau chạy đúng kỳ vọng trong các case nhận được phản hồi model; `null` nếu chưa có case nào được đo.
- `summary.full_accuracy`: tỉ lệ trên toàn bộ case vừa đúng routing/args, vừa thực thi không lỗi, vừa đúng trạng thái hồ sơ. Lỗi provider không được coi là thành công.

`turns` kiểm tra ngữ cảnh cho **lượt cuối** bằng một lần gọi model, giống bộ base/group hiện tại. Suite này chưa tự động kiểm chứng chuỗi model → tool → model nhiều vòng; việc đó dùng `chat.py` và transcript riêng.

Đây không phải kiểm định số liệu thời tiết hay thời gian thực: dữ liệu Open-Meteo và đồng hồ thay đổi theo lúc chạy. Unit test riêng của tool đã kiểm tra mapping, validation và nhánh lỗi bằng fixture/mock.

Để xuất CSV từ run vừa tạo:

```powershell
python scripts/parse_runs.py runs/<ten-file-team-tools>.json --output analysis/team_tools_eval/results.csv
```

CSV chuẩn chứa điểm routing; đọc thêm `profile_state` và execution checks trong run JSON để kiểm tra lưu hồ sơ.
