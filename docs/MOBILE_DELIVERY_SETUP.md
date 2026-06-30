# Mobile Delivery Setup

Status: Telegram DM delivery tested successfully after owner approval.

Latest successful receipt: `receipts/mobile_delivery/SYSTEM-90PLUS-DELIVERY-TEST_20260630124345_final_retry.json`.

Telegram home-channel delivery for scheduled briefs/cron was configured and verified.

Latest home-channel receipt: `receipts/mobile_delivery/SYSTEM-TELEGRAM-HOME-CRON-SETUP_20260630130044.json`.

Supported targets: Telegram, WhatsApp, Slack, Discord, or email.

Safe sequence:
1. Owner chooses one channel.
2. Configure credentials without printing secrets.
3. Send one harmless test message.
4. Save receipt under `receipts/mobile_delivery/`.
5. Update cron delivery target only after test success.

Current tested channel: Telegram DM via `hermes send --to telegram:<dm>`.

Current scheduled delivery target: `telegram`.

No tender submission, supplier/buyer message, payment, DSC, quote, final classification, or origin claim is authorized by delivery setup.
