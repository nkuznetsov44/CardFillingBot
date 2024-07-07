alter table fill_scope add column report_scopes json null;

create table currency_rate (
	currency varchar(255) not null primary key,
	rate float not null
);

insert into currency_rate(currency, rate)
values ('RUB', 1.25), ('EUR', 117.5);

insert into category (code, name, aliases, proportion, emoji_name)
values ('RENT', 'Аренда квартиры', 'аренда,квартира',1,':money_with_wings:');

alter table card_fill add column currency varchar(255) null;
