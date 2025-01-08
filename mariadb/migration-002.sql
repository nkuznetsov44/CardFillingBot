begin;
alter table budget add column quarter_limit float default null;
alter table budget add column year_limit float default null;
alter table budget modify column monthly_limit float null;
commit;


begin;
update budget set monthly_limit=52000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'RESTAURANT';
update budget set monthly_limit=32000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'PUBLIC_SERVICE';
update budget set monthly_limit=15000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'TAXI';
update budget set monthly_limit=6000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'BAR';
update budget set monthly_limit=12000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'Beauty';
update budget set monthly_limit=null, quarter_limit=70000, year_limit=null where fill_scope = 1 and category_code = 'CLOTHES';
update budget set monthly_limit=null, quarter_limit=null, year_limit=400000 where fill_scope = 1 and category_code = 'GIFT';
update budget set monthly_limit=null, quarter_limit=80000, year_limit=null where fill_scope = 1 and category_code = 'HOME';
update budget set monthly_limit=null, quarter_limit=60000, year_limit=null where fill_scope = 1 and category_code = 'MEDICINE';
update budget set monthly_limit=null, quarter_limit=50000, year_limit=null where fill_scope = 1 and category_code = 'OTHER';
update budget set monthly_limit=22000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'ENTERTAINMENT';
update budget set monthly_limit=8000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'REGULAR';
update budget set monthly_limit=28000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'SPORT';
update budget set monthly_limit=null, quarter_limit=null, year_limit=1000000 where fill_scope = 1 and category_code = 'TRAVEL';
update budget set monthly_limit=117500, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'RENT';
update budget set monthly_limit=74000, quarter_limit=null, year_limit=null where fill_scope = 1 and category_code = 'FOOD';
commit;
