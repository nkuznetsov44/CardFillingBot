alter table budget add column start_date date not null default '2025-01-01';
alter table budget add column end_date date null;

alter table budget add constraint chk_budget_exactly_one_limit
check (
    (monthly_limit IS NOT NULL AND quarter_limit IS NULL AND year_limit IS NULL) OR
    (monthly_limit IS NULL AND quarter_limit IS NOT NULL AND year_limit IS NULL) OR
    (monthly_limit IS NULL AND quarter_limit IS NULL AND year_limit IS NOT NULL)
);

alter table budget add constraint chk_budget_monthly_dates
check (
    monthly_limit IS NULL OR (
        DAY(start_date) = 1 AND
        (end_date IS NULL OR (DAY(LAST_DAY(end_date)) = DAY(end_date)))
    )
);

alter table budget add constraint chk_budget_quarter_dates
check (
    quarter_limit IS NULL OR (
        DAY(start_date) = 1 AND
        MONTH(start_date) IN (1, 4, 7, 10) AND
        (end_date IS NULL OR (
            DAY(LAST_DAY(end_date)) = DAY(end_date) AND
            MONTH(end_date) IN (3, 6, 9, 12)
        ))
    )
);

alter table budget add constraint chk_budget_year_dates
check (
    year_limit IS NULL OR (
        DAYOFYEAR(start_date) = 1 AND
        (end_date IS NULL OR (MONTH(end_date) = 12 AND DAY(end_date) = 31))
    )
);

DROP TRIGGER IF EXISTS trg_budget_check_overlap_insert;

CREATE TRIGGER trg_budget_check_overlap_insert
BEFORE INSERT ON budget
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT;
    
    SELECT COUNT(*) INTO overlap_count
    FROM budget
    WHERE fill_scope = NEW.fill_scope
      AND category_code = NEW.category_code
      AND NEW.start_date <= COALESCE(end_date, '9999-12-31')
      AND COALESCE(NEW.end_date, '9999-12-31') >= start_date;
    
    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Budget periods cannot overlap for the same scope and category';
    END IF;
END;

DROP TRIGGER IF EXISTS trg_budget_check_overlap_update;

CREATE TRIGGER trg_budget_check_overlap_update
BEFORE UPDATE ON budget
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT;
    
    SELECT COUNT(*) INTO overlap_count
    FROM budget
    WHERE id != NEW.id
      AND fill_scope = NEW.fill_scope
      AND category_code = NEW.category_code
      AND NEW.start_date <= COALESCE(end_date, '9999-12-31')
      AND COALESCE(NEW.end_date, '9999-12-31') >= start_date;
    
    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Budget periods cannot overlap for the same scope and category';
    END IF;
END;
