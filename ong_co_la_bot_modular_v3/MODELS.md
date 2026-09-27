# Current logical data models

The existing SQLite schema remains the source of truth.

Core entities:
- User/Member: Discord user identity and guild-scoped progress
- StudySession: study duration, subject, date, streak/reward settlement
- Reminder: persistent reminder with due time and completion state
- InventoryItem: owned consumable/items
- RoomRecord: temporary room owner, privacy, expiry and original name
- DisciplineRequest: explanation/leave request and review state
- DynamicPunishment: configurable punishment levels
- BotConfig: fixed channel/category IDs per guild

Future web phase can map these to PostgreSQL models without changing the user-facing commands first.
