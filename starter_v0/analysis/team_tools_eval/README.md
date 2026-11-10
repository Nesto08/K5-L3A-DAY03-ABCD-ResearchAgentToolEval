# Bàn giao eval 4 tool nhóm

Đã tạo [suite riêng 20 case](../../data/eval_team_tools.json): mỗi tool `weather`, `now`, `profile`, `profile_save` có 5 prompt. Tổng 10 single turn và 10 multi turn. Bộ `eval_group.json` cũ gồm 10 case được giữ nguyên.

Đây là số lượng nhóm yêu cầu bổ sung. README lab yêu cầu 10 case **cho cả bộ nhóm**, không bắt buộc 5 case cho từng tool.

## File sử dụng

- [Ma trận 20 case và hướng dẫn chạy](../../data/README_team_tools.md).
- [Runner có hồ sơ tạm](../../scripts/run_team_tools_eval.py).
- [Test contract suite và cô lập dữ liệu](../../tests/test_team_tools_eval.py).
- [Manifest và hash](manifest.json).
- [Nhật ký chạy](run_log.csv).
- [CSV từng case](results.csv).
- [Đối chiếu issue GitHub](ISSUES_AUDIT.md).

## Kết quả live hiện có

| Lần chạy | Provider / model | Case được đo | Lỗi provider | Kết luận |
|---|---|---:|---:|---|
| r1 | OpenRouter / openai/gpt-4o-mini | 0/20 | 20 | HTTP 403: This model is not available in your region |
| r2 | Groq / openai/gpt-oss-20b | 0/20 | 20 | HTTP 403: Forbidden |

Run JSON:

- [OpenRouter r1](../../runs/v2-team-tools-r1_B_team_tools_openrouter_20261110T161617349492.json).
- [Groq r2](../../runs/v2-team-tools-r2_B_team_tools_groq_20261110T162134960081.json).

**Chưa có điểm chất lượng model.** `case_accuracy=0` trong summary chuẩn không có nghĩa model trả lời sai 20 case: mẫu số `measured_cases` bằng 0. Các kiểm tra thực thi/hồ sơ của case lỗi provider được đánh dấu chưa đo (`null`), không coi là PASS. CSV run log để trống điểm routing cho hai lần này.

Không sửa prompt, tool declaration hay expected answer để né lỗi truy cập. Không tự đổi model ngoài lựa chọn của người dùng. Cần khôi phục quyền truy cập provider/model rồi chạy lại để thu bằng chứng live.

## Đặc điểm kiểm tra

- Mỗi case dùng file hồ sơ giả mới, không ảnh hưởng case sau hay hồ sơ thật.
- Kiểm tra `profile_save` có ghi đúng trường và giữ nguyên các trường khác; các case từ chối lưu phải giữ nguyên toàn bộ hồ sơ.
- Model vẫn thấy toàn bộ 14 khai báo tool để phát hiện nhầm routing. Chỉ 4 tool nhóm và `clarify` được thực thi; lời gọi ngoài suite, đặc biệt `send`, chỉ được ghi nhận.
- Multi turn trong suite là ngữ cảnh cho lời gọi cuối, theo evaluator hiện tại; không tự chấm chuỗi model–tool nhiều vòng.
- Weather dùng dữ liệu Open-Meteo thực nếu model gọi đúng và provider trả lời; không so khớp nhiệt độ/dự báo cố định. Now không so khớp giờ tuyệt đối thay đổi liên tục.
- Không thay đổi `eval_base.json`, `eval_group.json`, `artifacts/system_prompt.md`, `artifacts/tools.yaml` hoặc implementation của các tool.

Unit test bổ sung kiểm tra số lượng/cấu trúc case, sự nhất quán tên tool, cô lập và reset hồ sơ, guard không thực thi hành động ngoài suite, phát hiện ghi file thất bại dù routing đúng, và từ chối runner thông thường khi chưa cô lập profile.

Kiểm tra cuối: **156 passed, 17 skipped, 0 failed**. Riêng file test mới có **8 test PASS**. Các 17 skipped vẫn là TODO cũ trong `tests/test_tools_todo.py`, không phải kết quả eval live. Quét artifact mới không phát hiện giá trị API key/token đang cấu hình.

## Chạy lại

Từ `starter_v0/`, với venv đã kích hoạt:

```powershell
python scripts/preflight_provider.py --provider groq --model openai/gpt-oss-20b
```

Sau khi preflight thành công:

```powershell
python scripts/run_team_tools_eval.py --provider groq --model openai/gpt-oss-20b --version v2-team-tools-r3
```

Runner tạo file có timestamp mới; giữ các run bị chặn để truy vết. Khi sửa prompt/tool để tối ưu, tiếp tục dùng cùng dataset/model và ghi rõ cấu hình mới.
