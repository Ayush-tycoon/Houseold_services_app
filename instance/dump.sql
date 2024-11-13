PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS user;
CREATE TABLE user (
	id INTEGER NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	role VARCHAR(80) NOT NULL, 
	date_joined DATETIME NOT NULL, 
	password VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email)
);
INSERT INTO user VALUES(1,'Sugar Daddy','abc@gmail.com','customer','2020-01-01 00:00:00.000000','a');
INSERT INTO user VALUES(2,'admin','admin@gmail.com','admin','2024-10-14 17:56:13.176626','123');
INSERT INTO user VALUES(3,'shon','def@gmail.com','service_professional','2020-01-01 00:00:00.000000','b');
INSERT INTO user VALUES(4,'ayush','ayushsjadhav99@gmail.com','customer','2024-10-14 17:57:07.294991','a');
INSERT INTO user VALUES(6,'Praj','pp@gmail.com','service_professional','2024-10-14 18:14:02.814073','a');
INSERT INTO user VALUES(7,'Tanishq','tan@gmail.com','service_professional','2024-10-15 18:23:24.895240','a');
INSERT INTO user VALUES(8,'Palash','p@gm.com','service_professional','2024-10-16 00:31:41.219218','a');
DROP TABLE IF EXISTS service_category;
CREATE TABLE service_category (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	base_price FLOAT NOT NULL, 
	time_required INTEGER NOT NULL, 
	description VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO service_category VALUES(1,'Electrician',100.0,2,'Electrician');
INSERT INTO service_category VALUES(2,'Painter',2000.0,24,'Home interior and exterior paint');
INSERT INTO service_category VALUES(3,'Plumber',400.0,1,'Houesold plumber');
DROP TABLE IF EXISTS customer;
CREATE TABLE customer (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	phone VARCHAR(80) NOT NULL, 
	city VARCHAR(80) NOT NULL, 
	address VARCHAR(200) NOT NULL, 
	status VARCHAR(80) NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO customer VALUES(1,'John','123','abc','13 street california','active',1);
INSERT INTO customer VALUES(2,'Ayush Jadhav','8668273475','Pune','Pune, amber park','active',4);
DROP TABLE IF EXISTS service_professional;
CREATE TABLE service_professional (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	phone VARCHAR(80) NOT NULL, 
	city VARCHAR(80) NOT NULL, 
	service_category VARCHAR(80) NOT NULL, 
	rating FLOAT, 
	experience INTEGER NOT NULL, 
	company_name VARCHAR(80) NOT NULL, 
	status VARCHAR(80) NOT NULL, 
	price_per_hour FLOAT NOT NULL, 
	expenses_per_hour FLOAT, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO service_professional VALUES(1,'Sugar Daddy','123','abc','Electrician',4.5,2,'abc','approved',100.0,0.0,3);
INSERT INTO service_professional VALUES(2,'Prajwal','222222222','Pune','Painter',NULL,2,'pp inc','approved',2000.0,0.0,6);
INSERT INTO service_professional VALUES(3,'tanishq ojha','222222222','Bhopal','Plumber',NULL,5,'tani inc','approved',500.0,0.0,7);
INSERT INTO service_professional VALUES(4,'palash johri','5555555555','Lucknow','Plumber',NULL,5,'p inc','pending',450.0,0.0,8);
DROP TABLE IF EXISTS service_request;
CREATE TABLE service_request (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	service_professional_id INTEGER NOT NULL, 
	service_category_id INTEGER NOT NULL, 
	service_category VARCHAR(80) NOT NULL,
	date_request DATETIME NOT NULL, 
	date_completion DATETIME NOT NULL, 
	status VARCHAR(80) NOT NULL, 
	rating FLOAT, 
	feedback VARCHAR(400), 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customer (id), 
	FOREIGN KEY(service_professional_id) REFERENCES service_professional (id), 
	FOREIGN KEY(service_category_id) REFERENCES service_category (id)
);
INSERT INTO service_request VALUES(1,1,1,1,'electrician','2020-01-01 00:00:00.000000','2020-01-02 00:00:00.000000','completed',4.5,'good');
DROP TABLE IF EXISTS admin_actions;
CREATE TABLE admin_actions (
	id INTEGER NOT NULL, 
	service_professional_id INTEGER NOT NULL, 
	action VARCHAR(80) NOT NULL, 
	date_action DATETIME NOT NULL, 
	remarks VARCHAR(400), 
	PRIMARY KEY (id), 
	FOREIGN KEY(service_professional_id) REFERENCES service_professional (id)
);
DROP TABLE IF EXISTS review;
CREATE TABLE review (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	service_professional_id INTEGER NOT NULL, 
	"ServiceRequest_id" INTEGER NOT NULL, 
	rating FLOAT NOT NULL, 
	feedback VARCHAR(400), 
	date_review DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customer (id), 
	FOREIGN KEY(service_professional_id) REFERENCES service_professional (id), 
	FOREIGN KEY("ServiceRequest_id") REFERENCES service_request (id)
);
INSERT INTO review VALUES(1,1,1,1,4.5,'good','2020-01-02 00:00:00.000000');
DROP TABLE IF EXISTS alembic_version;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
COMMIT;
