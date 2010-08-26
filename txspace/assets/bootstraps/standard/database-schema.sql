DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS access;
DROP TABLE IF EXISTS permission;
DROP TABLE IF EXISTS property;
DROP TABLE IF EXISTS verb_name;
DROP TABLE IF EXISTS verb;
DROP TABLE IF EXISTS object_relation;
DROP TABLE IF EXISTS object_alias;
DROP TABLE IF EXISTS object;

DROP TYPE IF EXISTS eval_type;
DROP TYPE IF EXISTS rule_type;
DROP TYPE IF EXISTS access_type;
DROP TYPE IF EXISTS group_type;

CREATE TYPE eval_type AS ENUM('string', 'python', 'dynamic');
CREATE TYPE rule_type AS ENUM('allow', 'deny');
CREATE TYPE access_type AS ENUM('accessor', 'group');
CREATE TYPE group_type AS ENUM('everyone', 'owners', 'wizards');

CREATE TABLE object (
	id bigserial,
	name varchar(255) NOT NULL,
	unique_name boolean NOT NULL,
	owner_id bigint REFERENCES object ON DELETE SET NULL,
	location_id bigint REFERENCES object ON DELETE SET NULL,
	PRIMARY KEY (id),
	CONSTRAINT obj_name_nomts CHECK(name <> '')
);

CREATE TABLE object_relation (
	parent_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	child_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	weight int NOT NULL DEFAULT 0,
	PRIMARY KEY (parent_id, child_id)
);

CREATE TABLE object_alias (
	object_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	alias varchar(255) NOT NULL,
	PRIMARY KEY (object_id, alias),
	CONSTRAINT verb_name_nomts CHECK(alias <> '')
);

CREATE TABLE verb (
	id bigserial,
	code text NOT NULL,
	owner_id bigint REFERENCES object ON DELETE SET NULL,
	origin_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	ability boolean NOT NULL,
	method boolean NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE verb_name (
	verb_id bigint NOT NULL REFERENCES verb ON DELETE CASCADE,
	name varchar(255) NOT NULL,
	PRIMARY KEY (verb_id, name),
	CONSTRAINT verb_name_nomts CHECK(name <> '')
);

CREATE TABLE property (
	id bigserial,
	name varchar(255) NOT NULL,
	type eval_type NOT NULL,
	value text NOT NULL,
	owner_id bigint REFERENCES object ON DELETE SET NULL,
	origin_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	PRIMARY KEY (id)
);

CREATE TABLE permission (
	id bigserial,
	name varchar(255) NOT NULL,
	PRIMARY KEY(id),
	CONSTRAINT name_uniq UNIQUE(name),
	CONSTRAINT name_uniq CHECK(name <> '')
);

CREATE TABLE access (
	id bigserial,
	object_id bigint REFERENCES object ON DELETE CASCADE,
	verb_id bigint REFERENCES verb ON DELETE CASCADE,
	property_id bigint REFERENCES property ON DELETE CASCADE,
	rule rule_type NOT NULL,
	permission_id bigint NOT NULL REFERENCES permission ON DELETE CASCADE,
	type access_type NOT NULL,
	accessor_id bigint REFERENCES object ON DELETE CASCADE,
	"group" group_type,
	weight serial,
	PRIMARY KEY (id),
	CONSTRAINT permission_uniq UNIQUE(object_id, verb_id, property_id, rule, permission_id, type, accessor_id, "group"),
	CONSTRAINT object_id_only CHECK(
		CASE WHEN COALESCE(object_id, 0) <> 0 THEN
			COALESCE(verb_id, property_id) IS NULL
		ELSE
			TRUE
		END
	),
	CONSTRAINT verb_id_only CHECK(
		CASE WHEN COALESCE(verb_id, 0) <> 0 THEN
			COALESCE(object_id, property_id) IS NULL
		ELSE
			TRUE
		END
	),
	CONSTRAINT property_id_only CHECK(
		CASE WHEN COALESCE(property_id, 0) <> 0 THEN
			COALESCE(object_id, verb_id) IS NULL
		ELSE
			TRUE
		END
	),
	CONSTRAINT access_type_const CHECK(
		CASE WHEN type = 'accessor' THEN
			accessor_id IS NOT NULL
		ELSE
			"group" IS NOT NULL
		END
	)
);

CREATE TABLE player (
	id bigserial,
	avatar_id bigint REFERENCES object ON DELETE SET NULL,
	session_id bigint,
	wizard boolean NOT NULL,
	crypt varchar(255) NOT NULL,
	last_login timestamp,
	last_logout timestamp,
	PRIMARY KEY (id),
	CONSTRAINT user_uniq UNIQUE(id)
);

CREATE TABLE session (
	id varchar(255),
	user_id bigint REFERENCES object ON DELETE CASCADE,
	created timestamp default NOW(),
	accessed timestamp default NOW(),
	timeout int default 86400,
	data bytea,
	PRIMARY KEY (id),
	CONSTRAINT session_uniq UNIQUE(id)
);
