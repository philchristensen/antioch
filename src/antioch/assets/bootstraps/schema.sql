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
CREATE INDEX object_owner_key ON object (owner_id);
CREATE INDEX object_location_key ON object (location_id);

CREATE TABLE object_relation (
	parent_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	child_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	weight int NOT NULL DEFAULT 0,
	PRIMARY KEY (parent_id, child_id)
);
CREATE INDEX object_relation_parent ON object_relation (parent_id);
CREATE INDEX object_relation_child ON object_relation (child_id);

CREATE TABLE object_alias (
	object_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	alias varchar(255) NOT NULL,
	PRIMARY KEY (object_id, alias),
	CONSTRAINT verb_name_nomts CHECK(alias <> '')
);
CREATE INDEX object_alias_key ON object_alias (alias);

CREATE TABLE object_observer (
	object_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	observer_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	PRIMARY KEY (object_id, observer_id)
);
CREATE INDEX object_observer_object_key ON object_observer (object_id);
CREATE INDEX object_observer_key ON object_observer (observer_id);

CREATE TABLE verb (
	id bigserial,
	code text NOT NULL,
	filename varchar(255),
	owner_id bigint REFERENCES object ON DELETE SET NULL,
	origin_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	ability boolean NOT NULL,
	method boolean NOT NULL,
	PRIMARY KEY (id)
);
CREATE INDEX verb_origin_key ON verb (origin_id);
CREATE INDEX verb_owner_key ON verb (owner_id);

CREATE TABLE verb_name (
	verb_id bigint NOT NULL REFERENCES verb ON DELETE CASCADE,
	name varchar(255) NOT NULL,
	PRIMARY KEY (verb_id, name),
	CONSTRAINT verb_name_nomts CHECK(name <> '')
);
CREATE INDEX verb_name_key ON verb_name (name);

CREATE TABLE property (
	id bigserial,
	name varchar(255) NOT NULL,
	type eval_type NOT NULL,
	value text,
	owner_id bigint REFERENCES object ON DELETE SET NULL,
	origin_id bigint NOT NULL REFERENCES object ON DELETE CASCADE,
	PRIMARY KEY (id)
);
CREATE INDEX property_name_key ON property (name);
CREATE INDEX property_origin_key ON property (origin_id);
CREATE INDEX property_owner_key ON property (owner_id);

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
CREATE INDEX access_permission_key ON access (permission_id);
CREATE INDEX access_object_key ON access (object_id);
CREATE INDEX access_verb_key ON access (verb_id);
CREATE INDEX access_property_key ON access (property_id);

CREATE TABLE player (
	id bigserial,
	avatar_id bigint REFERENCES object ON DELETE CASCADE,
	session_id varchar(255),
	wizard boolean NOT NULL,
	crypt varchar(255) NOT NULL,
	last_login timestamp,
	last_logout timestamp,
	PRIMARY KEY (id),
	CONSTRAINT user_uniq UNIQUE(id)
);
CREATE INDEX player_avatar_key ON player (avatar_id);
CREATE INDEX player_session_key ON player (session_id);

CREATE TABLE session (
	id varchar(255),
	user_id bigint REFERENCES object ON DELETE CASCADE,
	last_client_ip inet,
	created timestamp default NOW(),
	accessed timestamp default NOW(),
	timeout int default 86400,
	data bytea,
	PRIMARY KEY (id),
	CONSTRAINT session_uniq UNIQUE(id)
);
CREATE INDEX session_user_key ON session (user_id);

CREATE TABLE task (
	id bigserial,
	user_id bigint REFERENCES object ON DELETE CASCADE,
	origin_id bigint REFERENCES object ON DELETE CASCADE,
	verb_name varchar(255) NOT NULL,
	args varchar(255) NOT NULL,
	kwargs varchar(255) NOT NULL,
	created timestamp NOT NULL default NOW(),
	delay int NOT NULL,
	killed boolean NOT NULL default 'f',
	error varchar(255) NOT NULL default '',
	trace text NOT NULL default '',
	PRIMARY KEY (id)
);
CREATE INDEX task_user_key ON task (user_id);
CREATE INDEX task_origin_key ON task (origin_id);
CREATE INDEX task_verb_key ON task (verb_name);