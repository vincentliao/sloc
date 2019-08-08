schema = """
CREATE TABLE IF NOT EXISTS repository (
	sno INTEGER NOT NULL,
	name VARCHAR(256),
	path VARCHAR(256),
	owner VARCHAR(100),
	PRIMARY KEY (sno)
);
CREATE TABLE IF NOT EXISTS revision (
	sno INTEGER NOT NULL,
	hash VARCHAR(32),
	commit_time DATETIME,
	repo_sno INTEGER,
	PRIMARY KEY (sno),
	FOREIGN KEY(repo_sno) REFERENCES repository (sno)
);
CREATE TABLE  IF NOT EXISTS sloc (
	sno INTEGER NOT NULL,
	language VARCHAR(256),
	filename VARCHAR(256),
	source_line INTEGER,
	empty_line INTEGER,
	revision_sno INTEGER,
	PRIMARY KEY (sno),
	FOREIGN KEY(revision_sno) REFERENCES revision (sno)
);
"""
