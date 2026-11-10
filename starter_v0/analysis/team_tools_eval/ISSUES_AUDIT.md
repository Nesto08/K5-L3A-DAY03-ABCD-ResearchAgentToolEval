# Đối chiếu Issues với repo

Nguồn: [GitHub Issues](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/), đọc qua GitHub API công khai ngày 2026-11-10. Có **12 issue mở** tại lần kiểm tra. Tất cả chưa gán GitHub assignee, nhưng đã phân vai A/B/C/D bằng label và nội dung; không suy ra rằng chưa ai làm chỉ từ trạng thái open.

| Issue GitHub | Vai trong ticket | Bằng chứng hiện có / việc còn lại |
|---|---|---|
| [#5 — Tool đầu tiên](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/5) | B | Bộ mới có 4 implementation, TOOL.md, registry, YAML và test riêng. Rà lại case routing của từng tool trước khi đóng. |
| [#6 — Tool thứ hai](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/6) | B | Như trên. Ticket chưa nêu tên tool cụ thể nên không tự gán số ticket cho một trong 4 tool. |
| [#7 — Tool thứ ba](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/7) | B | Như trên. |
| [#8 — Tool thứ tư](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/8) | B | Như trên; có 4 tool mới và UI nhưng cần chốt đủ bằng chứng để xác nhận bonus. |
| [#9 — 9 case còn lại](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/9) | D | Bộ group đã đủ 10 case (5/5), run v2 đạt 9/10. G07 mất days=7 sau clarify. Group chưa có case dương gọi profile_save; suite bổ sung 20 case có coverage này. |
| [#11 — V2](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/11) | A | Có prompt/tools v2, version log, run base 20/20, group 9/10 và contract test xanh. Có bằng chứng để rà checklist; vẫn đang open. |
| [#12 — Telegram UI](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/12) | C | Chưa thấy đủ transcript đồng ý gửi/thực sự gửi và từ chối/không gửi như acceptance criteria. Không gửi thử Telegram trong task eval này. |
| [#13 — V3](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/13) | A | Checkout mới chưa có run v3 trên base/group/extension và dòng v3 tương ứng. Giả thuyết mới nên dựa trên lỗi v2 hiện tại, ví dụ G07 hoặc lỗi extension. |
| [#14 — REPORT A](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/14) | C | A1–A3 đã có nội dung và transcript mẫu. Link public còn TODO; Team/Members nằm trong HTML comment; câu mở đầu ghi 15 tool trong khi registry/bảng có 14. |
| [#15 — 17 TODO test](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/15) | D | Trước task này pytest đạt 148 passed, 17 skipped; vẫn còn đúng 17 stub TODO. Các test mới của suite này không thay thế yêu cầu điền TODO. |
| [#16 — REPORT B/CSV/chat](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/16) | D | Phần B còn phần lớn là mẫu; transcript mới chủ yếu là v2. Chưa đủ báo cáo/CSV/transcript v3 theo ticket. Task này bổ sung CSV/log riêng cho suite 20 case. |
| [#17 — Ollama](https://github.com/Nesto08/K5-L3A-DAY03-ABCD-ResearchAgentToolEval/issues/17) | A | Chưa thấy run local trong checkout; bonus, không cần ưu tiên trước phần bắt buộc. |

Đây là đánh giá từ code và artifact hiện có. Không tự đóng/assign issue hay đăng comment; tác giả/nhóm chốt trạng thái sau khi review acceptance criteria và PR.
