CREATE TABLE moderation_results (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES advertisements(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_violation BOOLEAN,
    probability FLOAT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP
);
