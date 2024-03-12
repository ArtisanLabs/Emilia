CREATE TABLE telegram_users (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    is_bot BOOLEAN DEFAULT false,
    language_code TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE user_stored_messages (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT REFERENCES telegram_users(chat_id),
    messages TEXT,
    emoji TEXT,
    stage TEXT,
    stored_at TIMESTAMP DEFAULT now()
);
