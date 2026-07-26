BEGIN TRANSACTION;
CREATE TABLE departments (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "departments" VALUES(1,'Engineering','Software and infrastructure','2026-07-26 17:23:04.851006');
INSERT INTO "departments" VALUES(2,'Sales','Revenue and business development','2026-07-26 17:23:04.851006');
INSERT INTO "departments" VALUES(3,'HR','People & culture','2026-07-26 17:23:04.851006');
INSERT INTO "departments" VALUES(4,'Finance','Financial operations','2026-07-26 17:23:04.851006');
INSERT INTO "departments" VALUES(5,'Operations','Day-to-day operations','2026-07-26 17:23:04.851006');
CREATE TABLE employees (
	id INTEGER NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	phone VARCHAR(30), 
	role VARCHAR(100) NOT NULL, 
	department_id INTEGER, 
	manager_id INTEGER, 
	start_date DATE NOT NULL, 
	salary FLOAT NOT NULL, 
	employment_type VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	deactivated_at DATETIME, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	FOREIGN KEY(department_id) REFERENCES departments (id), 
	FOREIGN KEY(manager_id) REFERENCES employees (id)
);
INSERT INTO "employees" VALUES(1,'James','Vunoh','james.vunoh@vunohglobal.com',NULL,'Chief Executive Officer',3,NULL,'2020-01-15',250000.0,'full_time',1,NULL,'2026-07-26 17:23:04.860512');
INSERT INTO "employees" VALUES(2,'Amina','Ochieng','amina.ochieng@vunohglobal.com',NULL,'HR Manager',3,1,'2021-03-01',120000.0,'full_time',1,NULL,'2026-07-26 17:23:04.862084');
INSERT INTO "employees" VALUES(3,'Brian','Kamau','brian.kamau@vunohglobal.com',NULL,'Engineering Manager',1,1,'2021-06-01',180000.0,'full_time',1,NULL,'2026-07-26 17:23:04.862084');
INSERT INTO "employees" VALUES(4,'Alice','Njeri','alice.njeri@vunohglobal.com',NULL,'Senior Software Engineer',1,3,'2022-02-14',130000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(5,'Bob','Otieno','bob.otieno@vunohglobal.com',NULL,'Software Engineer',1,3,'2023-05-01',95000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(6,'Carol','Wambua','carol.wambua@vunohglobal.com',NULL,'Junior Software Engineer',1,3,'2024-09-01',65000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(7,'David','Mwangi','david.mwangi@vunohglobal.com',NULL,'DevOps Engineer',1,3,'2026-07-15',110000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(8,'Peter','Ndungu','peter.ndungu@vunohglobal.com',NULL,'Sales Manager',2,1,'2021-08-01',135000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(9,'Grace','Achieng','grace.achieng@vunohglobal.com',NULL,'Sales Representative',2,NULL,'2023-01-10',70000.0,'full_time',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(10,'Felix','Mugo','felix.mugo@vunohglobal.com',NULL,'Engineering Intern',1,3,'2026-06-01',25000.0,'intern',1,NULL,'2026-07-26 17:23:04.866442');
INSERT INTO "employees" VALUES(11,'Janet','Maina','janet.maina@vunohglobal.com',NULL,'QA Engineer',1,3,'2022-04-01',88000.0,'full_time',0,'2026-05-31 00:00:00.000000','2026-07-26 17:23:04.866442');
CREATE TABLE leave_balances (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	leave_type_id INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	entitled_days FLOAT NOT NULL, 
	used_days FLOAT NOT NULL, 
	carried_over FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT _emp_lt_year_uc UNIQUE (employee_id, leave_type_id, year), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(leave_type_id) REFERENCES leave_types (id)
);
INSERT INTO "leave_balances" VALUES(1,1,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(2,1,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(3,1,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(4,2,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(5,2,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(6,2,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(7,3,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(8,3,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(9,3,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(10,4,1,2026,21.0,5.0,0.0);
INSERT INTO "leave_balances" VALUES(11,4,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(12,4,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(13,5,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(14,5,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(15,5,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(16,6,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(17,6,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(18,6,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(19,7,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(20,7,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(21,7,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(22,8,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(23,8,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(24,8,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(25,9,1,2026,21.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(26,9,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(27,9,3,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(28,10,1,2026,5.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(29,10,2,2026,10.0,0.0,0.0);
INSERT INTO "leave_balances" VALUES(30,10,3,2026,5.0,0.0,0.0);
CREATE TABLE leave_requests (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	leave_type_id INTEGER NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	days_requested FLOAT NOT NULL, 
	reason TEXT, 
	status VARCHAR(20) NOT NULL, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	rejection_reason TEXT, 
	escalated_at DATETIME, 
	created_at DATETIME, 
	flag_insufficient_notice BOOLEAN, 
	flag_team_coverage_risk BOOLEAN, 
	flag_balance_exceeded BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(leave_type_id) REFERENCES leave_types (id), 
	FOREIGN KEY(reviewed_by) REFERENCES employees (id)
);
INSERT INTO "leave_requests" VALUES(1,4,1,'2026-07-06','2026-07-10',5.0,'Family vacation','approved',3,'2026-07-04 17:23:07.229061',NULL,NULL,'2026-07-26 17:23:07.233067',0,0,0);
INSERT INTO "leave_requests" VALUES(2,5,1,'2026-08-02','2026-08-06',5.0,'Personal travel','pending',NULL,NULL,NULL,NULL,'2026-07-26 17:23:07.239029',0,0,0);
INSERT INTO "leave_requests" VALUES(3,6,2,'2026-07-25','2026-07-26',2.0,'Flu','pending',NULL,NULL,NULL,NULL,'2026-07-26 17:23:07.239029',0,0,0);
INSERT INTO "leave_requests" VALUES(4,9,1,'2026-08-09','2026-08-13',5.0,'Wedding','escalated',NULL,NULL,NULL,'2026-07-26 17:23:07.238430','2026-07-21 17:23:07.238430',0,0,0);
CREATE TABLE leave_types (
	id INTEGER NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	is_paid BOOLEAN, 
	requires_notice BOOLEAN, 
	max_days_per_year INTEGER, 
	description VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO "leave_types" VALUES(1,'Annual Leave',1,1,NULL,'Standard annual leave');
INSERT INTO "leave_types" VALUES(2,'Sick Leave',1,0,10,'Medical illness');
INSERT INTO "leave_types" VALUES(3,'Emergency Leave',1,0,5,'Personal emergency');
INSERT INTO "leave_types" VALUES(4,'Unpaid Leave',0,1,NULL,'Leave without pay');
INSERT INTO "leave_types" VALUES(5,'Maternity Leave',1,1,90,'Maternity leave');
INSERT INTO "leave_types" VALUES(6,'Study Leave',0,1,10,'Approved study or exam');
CREATE TABLE payroll_periods (
	id INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	month INTEGER NOT NULL, 
	status VARCHAR(20), 
	generated_at DATETIME, 
	generated_by INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT _year_month_uc UNIQUE (year, month), 
	FOREIGN KEY(generated_by) REFERENCES users (id)
);
INSERT INTO "payroll_periods" VALUES(1,2026,6,'generated','2026-07-23 17:23:07.238430',NULL);
CREATE TABLE payslips (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	period_id INTEGER NOT NULL, 
	gross_salary FLOAT NOT NULL, 
	days_in_month INTEGER NOT NULL, 
	days_worked FLOAT NOT NULL, 
	prorated_gross FLOAT NOT NULL, 
	unpaid_leave_days FLOAT NOT NULL, 
	unpaid_leave_deduction FLOAT NOT NULL, 
	taxable_income FLOAT NOT NULL, 
	income_tax FLOAT NOT NULL, 
	social_security FLOAT NOT NULL, 
	total_deductions FLOAT NOT NULL, 
	net_pay FLOAT NOT NULL, 
	notes TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT _emp_period_uc UNIQUE (employee_id, period_id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(period_id) REFERENCES payroll_periods (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	employee_id INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);
INSERT INTO "users" VALUES(1,'admin','admin@vunohglobal.com','scrypt:32768:8:1$wys4ROftTlHA0EK2$71cd85adae1a94c0bfe344ab3959bd69dbe0dea6ee626f19dcde5e01a7b293bb135163449ee48a4f8f29bc5818201d832c61a1c40a44dd7e1a7e068ed77dc616','admin',NULL,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(2,'james.vunoh','james.vunoh@vunohglobal.com','scrypt:32768:8:1$OluufFniZ3fnaGiH$cc3d730c79ce1f4743648be50eff32a793174fba9fd8eaf635f3f56ba25caa724d1ee36a566d59a00218993da4a7314f3e113651c60ab7500c02cbd46f946aa2','manager',1,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(3,'amina.ochieng','amina.ochieng@vunohglobal.com','scrypt:32768:8:1$3W3zzHwKH131mOFo$651f1c040f3f1e22ce47419cc060b21cad80b545ee20d11bbc4f903036eaecdd0cf17266d1da0a7f623b828318482045a55491ed5eb4853f65e083fcbf8f57f9','manager',2,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(4,'brian.kamau','brian.kamau@vunohglobal.com','scrypt:32768:8:1$EkkE9JIDMYl0cznF$1007fb62e7d69e52ebc13179c98d61109067f68c90fe13412f9084e59ba3e9bb72dde0f14c110be036b5092bbf931568b542808c5ca152cd323cb7f71e95ea87','manager',3,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(5,'alice.njeri','alice.njeri@vunohglobal.com','scrypt:32768:8:1$gSAqJ2JgNwkfXcEn$82346943b398dbb26454b92ebfc31b0388220185293fc594a5b928366c1bd765cea4f93435ed779cb7b5fb812ba83b5afbc5a0c6bd74008c848a8991d9c44c7d','employee',4,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(6,'bob.otieno','bob.otieno@vunohglobal.com','scrypt:32768:8:1$hq6tmtnP8RGudCuL$b08b9602bdc8d8af5f9dced31c193a87577ac7a40f4ac7a841885da9b22868348faf345d5236962a8a2939656eb2c3a97ea2f37bf9bdc7a03a88a06e5c51e65d','employee',5,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(7,'carol.wambua','carol.wambua@vunohglobal.com','scrypt:32768:8:1$ktbyda7uzkm0Ow8O$eafb202c621a2abec3dba481f034654928c67a546326077b6c7cf715baf0f53fdcc4a5c2101545e212f13e0988f38a4fcd43468d0826be5cbaca6f2a2da38741','employee',6,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(8,'peter.ndungu','peter.ndungu@vunohglobal.com','scrypt:32768:8:1$1TJNu7Q6nnPtqskR$d607d49bd393cdad87e48b78f2047ed5973db59d8397635eec5aff86e4c035f0ab1f562a0dd0e613b2ab349d0ddb28a7f227503c28d7135d88f9e1742ce79deb','manager',8,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(9,'grace.achieng','grace.achieng@vunohglobal.com','scrypt:32768:8:1$2fUvvYejCDqRVP2L$9af16118d981d0b4eb84a7dd8805465453e054f4e2d639c61e24a9d65784f6fe1af4f9ca95aa9c7f4e66edc3491fe2179141769f60de28f3895ca39901cbc240','employee',9,'2026-07-26 17:23:07.221763');
INSERT INTO "users" VALUES(10,'felix.mugo','felix.mugo@vunohglobal.com','scrypt:32768:8:1$GQUlUAGPtUauK4X4$a0a7d14875939087f59d342843ea3bb4de28d6cb65a5a1362d675a8522e4306e1f91f8dee84855387f86336f6a7c045e092afc7bba091f44fd9df2a8dfaeefed','employee',10,'2026-07-26 17:23:07.221763');
COMMIT;
