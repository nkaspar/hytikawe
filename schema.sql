CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    ingredients TEXT,
    instructions TEXT,
    user_id INTEGER REFERENCES users
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    content TEXT,
    rating INTEGER,
    recipe_id INTEGER REFERENCES recipes,
    user_id INTEGER REFERENCES users
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    value TEXT
);

CREATE TABLE recipe_classes (
    recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes,
    PRIMARY KEY (recipe_id, class_id)
);
