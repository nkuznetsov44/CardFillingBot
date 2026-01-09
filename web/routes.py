from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from entities import Budget, FillScope, Category
from services.card_fill_service import CardFillService
from web.auth import verify_telegram_auth, login_required, admin_required
from settings import settings

def init_routes(app, card_fill_service: CardFillService):
    
    @app.route('/')
    @admin_required
    def index():
        return redirect(url_for('list_budgets'))
    
    @app.route('/login')
    def login():
        return render_template('login.html', bot_username=settings.telegram_bot_username, dev_mode=settings.web_dev_mode)
    
    @app.route('/auth/telegram', methods=['POST'])
    def telegram_auth():
        auth_data = request.form.to_dict()
        
        if verify_telegram_auth(auth_data):
            session['telegram_user'] = {
                'id': int(auth_data.get('id')),
                'first_name': auth_data.get('first_name', ''),
                'last_name': auth_data.get('last_name', ''),
                'username': auth_data.get('username', ''),
                'photo_url': auth_data.get('photo_url', ''),
            }
            
            next_url = request.args.get('next', url_for('list_budgets'))
            return redirect(next_url)
        else:
            flash('Ошибка аутентификации. Попробуйте снова.', 'error')
            return redirect(url_for('login'))
    
    @app.route('/auth/dev', methods=['POST'])
    def dev_auth():
        if not settings.web_dev_mode:
            return "Dev auth disabled", 403
        
        user_id = request.form.get('user_id')
        if user_id and user_id.isdigit():
            session['telegram_user'] = {
                'id': int(user_id),
                'first_name': 'Dev',
                'last_name': 'User',
                'username': 'dev_user',
                'photo_url': '',
            }
            flash('Вход выполнен (DEV режим)', 'success')
            return redirect(url_for('list_budgets'))
        else:
            flash('Укажите корректный User ID', 'error')
            return redirect(url_for('login'))
    
    @app.route('/logout')
    def logout():
        session.pop('telegram_user', None)
        flash('Вы успешно вышли из системы.', 'success')
        return redirect(url_for('login'))
    
    @app.route('/budgets')
    @admin_required
    def list_budgets():
        scope_id = request.args.get('scope_id', type=int)
        category_code = request.args.get('category_code')
        
        scopes = card_fill_service.list_all_scopes()
        categories = card_fill_service.list_categories()
        
        if scope_id:
            selected_scope = next((s for s in scopes if s.scope_id == scope_id), None)
            if selected_scope:
                budgets = card_fill_service.list_budgets(selected_scope)
            else:
                budgets = []
        else:
            all_budgets = []
            for scope in scopes:
                all_budgets.extend(card_fill_service.list_budgets(scope))
            budgets = all_budgets
        
        if category_code:
            budgets = [b for b in budgets if b.category.code == category_code]
        
        budgets_with_usage = []
        for budget in budgets:
            usage = card_fill_service.get_current_budget_usage_for_category(
                budget.category, budget.scope
            )
            budgets_with_usage.append({
                'budget': budget,
                'usage': usage
            })
        
        return render_template(
            'budgets_list.html',
            budgets_with_usage=budgets_with_usage,
            scopes=scopes,
            categories=categories,
            selected_scope_id=scope_id,
            selected_category_code=category_code
        )
    
    @app.route('/budgets/new')
    @admin_required
    def new_budget():
        scopes = card_fill_service.list_all_scopes()
        categories = card_fill_service.list_categories()
        return render_template('budget_form.html', scopes=scopes, categories=categories)
    
    @app.route('/budgets/create', methods=['POST'])
    @admin_required
    def create_budget():
        try:
            scope_id = int(request.form.get('scope_id'))
            category_code = request.form.get('category_code')
            limit_type = request.form.get('limit_type')
            limit_amount = float(request.form.get('limit_amount'))
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            scopes = card_fill_service.list_all_scopes()
            selected_scope = next((s for s in scopes if s.scope_id == scope_id), None)
            if not selected_scope:
                flash('Выбранный scope не найден.', 'error')
                return redirect(url_for('new_budget'))
            
            categories = card_fill_service.list_categories()
            selected_category = next((c for c in categories if c.code == category_code), None)
            if not selected_category:
                flash('Выбранная категория не найдена.', 'error')
                return redirect(url_for('new_budget'))
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            
            monthly_limit = limit_amount if limit_type == 'monthly' else None
            quarter_limit = limit_amount if limit_type == 'quarter' else None
            year_limit = limit_amount if limit_type == 'year' else None
            
            budget = Budget(
                id=None,
                scope=selected_scope,
                category=selected_category,
                monthly_limit=monthly_limit,
                quarter_limit=quarter_limit,
                year_limit=year_limit,
                start_date=start_date,
                end_date=end_date
            )
            
            card_fill_service.create_budget(budget)
            flash('Бюджет успешно создан!', 'success')
            return redirect(url_for('list_budgets'))
            
        except Exception as e:
            flash(f'Ошибка при создании бюджета: {str(e)}', 'error')
            return redirect(url_for('new_budget'))
    
    @app.route('/budgets/<int:budget_id>/edit')
    @admin_required
    def edit_budget(budget_id):
        budget = card_fill_service.get_budget_by_id(budget_id)
        if not budget:
            flash('Бюджет не найден.', 'error')
            return redirect(url_for('list_budgets'))
        
        scopes = card_fill_service.list_all_scopes()
        categories = card_fill_service.list_categories()
        
        return render_template(
            'budget_form.html',
            budget=budget,
            scopes=scopes,
            categories=categories,
            is_edit=True
        )
    
    @app.route('/budgets/<int:budget_id>/update', methods=['POST'])
    @admin_required
    def update_budget(budget_id):
        try:
            existing_budget = card_fill_service.get_budget_by_id(budget_id)
            if not existing_budget:
                flash('Бюджет не найден.', 'error')
                return redirect(url_for('list_budgets'))
            
            scope_id = int(request.form.get('scope_id'))
            category_code = request.form.get('category_code')
            limit_type = request.form.get('limit_type')
            limit_amount = float(request.form.get('limit_amount'))
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            scopes = card_fill_service.list_all_scopes()
            selected_scope = next((s for s in scopes if s.scope_id == scope_id), None)
            if not selected_scope:
                flash('Выбранный scope не найден.', 'error')
                return redirect(url_for('edit_budget', budget_id=budget_id))
            
            categories = card_fill_service.list_categories()
            selected_category = next((c for c in categories if c.code == category_code), None)
            if not selected_category:
                flash('Выбранная категория не найдена.', 'error')
                return redirect(url_for('edit_budget', budget_id=budget_id))
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            
            monthly_limit = limit_amount if limit_type == 'monthly' else None
            quarter_limit = limit_amount if limit_type == 'quarter' else None
            year_limit = limit_amount if limit_type == 'year' else None
            
            budget = Budget(
                id=budget_id,
                scope=selected_scope,
                category=selected_category,
                monthly_limit=monthly_limit,
                quarter_limit=quarter_limit,
                year_limit=year_limit,
                start_date=start_date,
                end_date=end_date
            )
            
            card_fill_service.update_budget(budget)
            flash('Бюджет успешно обновлен!', 'success')
            return redirect(url_for('list_budgets'))
            
        except Exception as e:
            flash(f'Ошибка при обновлении бюджета: {str(e)}', 'error')
            return redirect(url_for('edit_budget', budget_id=budget_id))
    
    @app.route('/budgets/<int:budget_id>/delete', methods=['POST'])
    @admin_required
    def delete_budget(budget_id):
        try:
            card_fill_service.delete_budget(budget_id)
            flash('Бюджет успешно удален!', 'success')
        except Exception as e:
            flash(f'Ошибка при удалении бюджета: {str(e)}', 'error')
        
        return redirect(url_for('list_budgets'))
