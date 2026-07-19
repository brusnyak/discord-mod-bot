CREATE TABLE IF NOT EXISTS guilds (
    id INTEGER PRIMARY KEY,
    mod_log_channel_id INTEGER,
    autorole_id INTEGER,
    warn_kick_count INTEGER DEFAULT 5,
    warn_ban_count INTEGER DEFAULT 6,
    mute_role_id INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    channel_id INTEGER,
    status TEXT DEFAULT 'open',
    created_at TEXT DEFAULT (datetime('now')),
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (guild_id, key)
);
