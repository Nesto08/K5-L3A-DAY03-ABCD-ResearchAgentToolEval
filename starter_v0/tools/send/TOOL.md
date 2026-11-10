---
name: send
track: bonus
kind: action
provider: Telegram Bot API
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]
inputs: [text, confirmed]
outputs: [status]
side_effect: true
requires_confirmation: true
---
# send

Posts text to a Telegram channel. The message is only sent when `confirmed` is true.

`confirmed` must be the boolean `true`, matching the tool schema. Strings such as
`"false"`, `"true"`, `"yes"`, and numbers such as `1` are not accepted as confirmation.
These inputs return `status="needs_confirmation"` without making a network request.
