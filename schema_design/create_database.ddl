CREATE SCHEMA IF NOT EXISTS content;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS content.genre (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    rating NUMERIC(3,1)
        CHECK (rating >= 0 AND rating <= 10),
    type VARCHAR(50) NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.person (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id uuid NOT NULL,
    film_work_id uuid NOT NULL,
    role VARCHAR(50) NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_person_film_work_person
        FOREIGN KEY (person_id)
        REFERENCES content.person(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_person_film_work_film_work
        FOREIGN KEY (film_work_id)
        REFERENCES content.film_work(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_person_film_work
        UNIQUE (person_id, film_work_id, role)
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    genre_id UUID NOT NULL,
    film_work_id UUID NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_genre_film_work_genre
        FOREIGN KEY (genre_id)
        REFERENCES content.genre(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_genre_film_work_film_work
        FOREIGN KEY (film_work_id)
        REFERENCES content.film_work(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_genre_film_work
        UNIQUE (genre_id, film_work_id)
);

CREATE INDEX idx_film_work_title
    ON content.film_work(title);

CREATE INDEX idx_person_full_name
    ON content.person(full_name);

CREATE INDEX idx_genre_name
    ON content.genre(name);

CREATE INDEX idx_genre_film_work_film_work_id
    ON content.genre_film_work(film_work_id);

CREATE INDEX idx_person_film_work_film_work_id
    ON content.person_film_work(film_work_id);