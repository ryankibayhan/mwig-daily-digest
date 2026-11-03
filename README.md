# mwig-daily-digest

Daily "trader-vibe" digest of the Polish mWIG40 session as a Mistral Workflow, 

Pipeline: fetch mWIG40 / WIG20 / EUR-PLN history (stooq CSV) -> pull and rank Polish finance RSS headlines -> a Mistral model ("Gordon", Warsaw trading-desk editor) writes an entertaining English digest (THE TAPE / MOVER SPOTLIGHT / INSIDER WHISPERS / WHY IT MATTERS FOR YOU / TRADER LINGO / FUN FACT) -> push to Telegram.

Workspace secrets required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. Optional: DIGEST_MODEL (default mistral-medium-latest).

Local dev: make test (stdlib-only unit tests), make start-worker (needs DEPLOYMENT_NAME + MISTRAL_API_KEY).
