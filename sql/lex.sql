CREATE TABLE "dim_date_day" (
  "id" int4 NOT NULL,
  "value" int2 NOT NULL,
  "label" varchar(6) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "dim_date_month" (
  "id" int4 NOT NULL,
  "value" int2 NOT NULL,
  "label" varchar(16) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "dim_date_year" (
  "id" int4 NOT NULL,
  "value" int2 NOT NULL,
  "label" varchar(4) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "dim_status" (
  "id" int4 NOT NULL,
  "value" varchar(3) NOT NULL,
  "label" varchar(32) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "dim_permit_type" (
  "id" int4 NOT NULL,
  "value" varchar(2) NOT NULL,
  "label" varchar(64) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "fact_permit" (
  "id" uuid NOT NULL,
  "app_id" varchar(32) NOT NULL,
  "is_renewal" bool NOT NULL,
  "application_date" date NOT NULL,
  "date_day_id" int4 NOT NULL,
  "date_month_id" int4 NOT NULL,
  "date_year_id" int4 NOT NULL,
  "type_id" int4 NOT NULL,
  "status" varchar(32) NOT NULL,
  PRIMARY KEY ("id")
);

ALTER TABLE "fact_permit" ADD CONSTRAINT "fk_fact_permit_dim_type_1" FOREIGN KEY ("type_id") REFERENCES "dim_permit_type" ("id");
ALTER TABLE "fact_permit" ADD CONSTRAINT "fk_fact_permit_dim_date_month_1" FOREIGN KEY ("date_month_id") REFERENCES "dim_date_month" ("id");
ALTER TABLE "fact_permit" ADD CONSTRAINT "fk_fact_permit_dim_date_year_1" FOREIGN KEY ("date_year_id") REFERENCES "dim_date_year" ("id");
ALTER TABLE "fact_permit" ADD CONSTRAINT "fk_fact_permit_dim_date_day_1" FOREIGN KEY ("date_day_id") REFERENCES "dim_date_day" ("id");


