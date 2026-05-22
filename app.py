from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from datetime import datetime, timedelta
import sqlite3
import json
import os
import hashlib
from functools import wraps
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-in-production-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Создание папок
for folder in ['photos', 'files', 'chat', 'posts']:
    os.makedirs(os.path.join('uploads', folder), exist_ok=True)

def init_db():
    conn = sqlite3.connect('real_estate_crm.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            age INTEGER,
            personal_phones TEXT,
            work_phones TEXT,
            login TEXT UNIQUE,
            password TEXT,
            photo TEXT,
            category TEXT,
            role TEXT DEFAULT 'employee',
            created_at TEXT
        )
    ''')
    
    # Таблица задач
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            author_id INTEGER,
            executor_id INTEGER,
            photo TEXT,
            status TEXT DEFAULT 'new',
            created_date TEXT
        )
    ''')
    
    # Таблица заявок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_type TEXT,
            address TEXT,
            area REAL,
            rooms INTEGER,
            windows INTEGER,
            floor INTEGER,
            total_floors INTEGER,
            documents TEXT,
            total_price REAL,
            price_per_m2 REAL,
            phone TEXT,
            client_name TEXT,
            manager TEXT,
            smm TEXT,
            comment TEXT,
            author_id INTEGER,
            executor_id INTEGER,
            files TEXT,
            status TEXT DEFAULT 'new',
            created_date TEXT
        )
    ''')

    # Таблица постов (барои Social Media Marketing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        title TEXT,
        description TEXT,
        category TEXT,
        content_type TEXT,
        project TEXT,
        media_path TEXT,
        media_type TEXT,
        link TEXT,
        post_date TEXT,
        created_date TEXT,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        reach INTEGER DEFAULT 0,
        is_published INTEGER DEFAULT 1,
        published_at TEXT,
        updated_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица чатов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        message TEXT,
        file_path TEXT,
        file_name TEXT,
        file_type TEXT,
        created_date TEXT
        )
    ''')
    
    
        # Таблицаи доскаҳо
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests_boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            color TEXT DEFAULT '#0f172a',
            is_public INTEGER DEFAULT 1,
            author_id INTEGER,
            created_date TEXT,
            updated_date TEXT,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # Таблицаи колонкаҳо
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER,
            title TEXT NOT NULL,
            color TEXT DEFAULT '#3b82f6',
            order_index INTEGER DEFAULT 0,
            created_date TEXT,
            FOREIGN KEY (board_id) REFERENCES requests_boards (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблицаи заявкаҳо (бо column_id ва order_index)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER,
            board_id INTEGER,
            property_type TEXT,
            address TEXT,
            area REAL,
            rooms INTEGER,
            windows INTEGER,
            floor INTEGER,
            total_floors INTEGER,
            total_price REAL,
            price_per_m2 REAL,
            phone TEXT,
            client_name TEXT,
            comment TEXT,
            author_id INTEGER,
            author_name TEXT,
            executor_id INTEGER,
            executor_name TEXT,
            files TEXT,
            order_index INTEGER DEFAULT 0,
            created_date TEXT,
            updated_date TEXT,
            FOREIGN KEY (column_id) REFERENCES requests_columns (id) ON DELETE CASCADE,
            FOREIGN KEY (board_id) REFERENCES requests_boards (id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users (id),
            FOREIGN KEY (executor_id) REFERENCES users (id)
        )
    ''')
    
     
    
    # ================ SIM CARDS AND PHONES TABLES ================
    
    # Company phones table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            phone_id TEXT UNIQUE,
            assigned_to INTEGER,
            description TEXT,
            status TEXT DEFAULT 'free',
            created_date TEXT,
            FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # SIM cards table (with all required columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sim_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            operator TEXT NOT NULL,
            assigned_to INTEGER,
            phone_id INTEGER,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_date TEXT,
            FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (phone_id) REFERENCES company_phones (id) ON DELETE SET NULL
        )
    ''')
    
    # Tariffs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sim_tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sim_id INTEGER NOT NULL,
            minutes INTEGER DEFAULT 0,
            gb REAL DEFAULT 0,
            sms INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            created_date TEXT,
            FOREIGN KEY (sim_id) REFERENCES sim_cards (id) ON DELETE CASCADE
        )
    ''')
    
    # Payments history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tariff_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sim_id INTEGER NOT NULL,
            tariff_id INTEGER,
            amount REAL DEFAULT 0,
            payment_date TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'paid',
            created_date TEXT,
            FOREIGN KEY (sim_id) REFERENCES sim_cards (id) ON DELETE CASCADE,
            FOREIGN KEY (tariff_id) REFERENCES sim_tariffs (id) ON DELETE SET NULL
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sim_cards_phone_number ON sim_cards(phone_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sim_cards_assigned_to ON sim_cards(assigned_to)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sim_cards_phone_id ON sim_cards(phone_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sim_tariffs_sim_id ON sim_tariffs(sim_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sim_tariffs_status ON sim_tariffs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tariff_payments_sim_id ON tariff_payments(sim_id)')

    # Таблица объектов недвижимости
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS houses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        construction_type TEXT,
        district TEXT,
        address TEXT,
        area REAL,
        rooms INTEGER,
        windows INTEGER,
        floor INTEGER,
        total_floors INTEGER,
        price_per_m2 REAL,
        total_price REAL,
        developer TEXT,
        contact_phone TEXT,
        has_tech_passport TEXT,
        has_renovation_permit TEXT,
        files TEXT,
        author_id INTEGER,
        created_date TEXT,
        FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # ================ REALTY OBJECTS TABLES (БО КАРТА) ================

    # Таблица объектов с координатами
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realty_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        address TEXT,
        lat REAL DEFAULT 38.5598,
        lng REAL DEFAULT 68.7870,
        construction_type TEXT DEFAULT 'новостройка',
        district TEXT DEFAULT 'н.Сино',
        area REAL DEFAULT 0,
        rooms INTEGER DEFAULT 0,
        windows INTEGER DEFAULT 0,
        floor INTEGER DEFAULT 0,
        total_floors INTEGER DEFAULT 0,
        price_per_m2 REAL DEFAULT 0,
        total_price REAL DEFAULT 0,
        developer TEXT,
        contact_phone TEXT,
        has_tech_passport TEXT DEFAULT 'нет',
        has_renovation_permit TEXT DEFAULT 'нет',
        created_date TEXT,
        updated_date TEXT,
        author_id INTEGER,
        FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')

    # Таблица блоков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realty_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_id INTEGER,
        name TEXT NOT NULL,
        code TEXT,
        order_index INTEGER DEFAULT 0,
        created_date TEXT,
        FOREIGN KEY (object_id) REFERENCES realty_objects (id) ON DELETE CASCADE
        )
    ''')

    # Таблица прайс-листов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realty_pricing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_id INTEGER,
        block_id INTEGER,
        floor_number INTEGER,
        floor_range_start INTEGER,
        floor_range_end INTEGER,
        percent_value INTEGER,
        price_usd REAL DEFAULT 0,
        price_tjs REAL DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        created_date TEXT,
        updated_date TEXT,
        FOREIGN KEY (object_id) REFERENCES realty_objects (id) ON DELETE CASCADE,
        FOREIGN KEY (block_id) REFERENCES realty_blocks (id) ON DELETE CASCADE
        )
    ''')

    # Таблица планировок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realty_layouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_id INTEGER,
        room_type TEXT,
        windows_count INTEGER,
        area REAL,
        price_usd REAL DEFAULT 0,
        price_tjs REAL DEFAULT 0,
        description TEXT,
        created_date TEXT,
        FOREIGN KEY (object_id) REFERENCES realty_objects (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        phone TEXT,
        topic TEXT,
        comment TEXT,
        source TEXT,
        mortgage INTEGER DEFAULT 0,
        box INTEGER DEFAULT 0,
        author_id INTEGER,
        created_date TEXT,
        FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        parent_id INTEGER DEFAULT 0,
        author_id INTEGER,
        author_name TEXT,
        created_date TEXT,
        FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # ================ KANBAN BOARD TABLES ================

    # Таблица досок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanban_boards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        color TEXT DEFAULT '#0079bf',
        is_public INTEGER DEFAULT 1,
        author_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        created_date TEXT,
        updated_date TEXT,
        FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')

    # Таблица участников приватной доски
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanban_board_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_id INTEGER,
        user_id INTEGER,
        added_date TEXT,
        FOREIGN KEY (board_id) REFERENCES kanban_boards (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Таблица колонок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanban_columns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_id INTEGER,
        title TEXT NOT NULL,
        color TEXT DEFAULT '#0079bf',
        order_index INTEGER DEFAULT 0,
        is_archived INTEGER DEFAULT 0,
        created_date TEXT,
        FOREIGN KEY (board_id) REFERENCES kanban_boards (id) ON DELETE CASCADE
        )
    ''')

    # Таблица лидов (карточек) в колонках
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanban_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        column_id INTEGER,
        board_id INTEGER,
        client_name TEXT,
        phone TEXT,
        topic TEXT,
        comment TEXT,
        source TEXT,
        mortgage INTEGER DEFAULT 0,
        box INTEGER DEFAULT 0,
        author_id INTEGER,
        author_name TEXT,
        order_index INTEGER DEFAULT 0,
        created_date TEXT,
        updated_date TEXT,
        FOREIGN KEY (column_id) REFERENCES kanban_columns (id) ON DELETE CASCADE,
        FOREIGN KEY (board_id) REFERENCES kanban_boards (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица взаимодействий с лидами
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanban_lead_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        phone TEXT,
        topic TEXT,
        source TEXT,
        contact_type TEXT,
        comment TEXT,
        mortgage INTEGER DEFAULT 0,
        box INTEGER DEFAULT 0,
        created_date TEXT,
        FOREIGN KEY (lead_id) REFERENCES kanban_leads (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS folder_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER,
        filename TEXT,
        original_name TEXT,
        filepath TEXT,
        filetype TEXT,
        filesize INTEGER,
        author_id INTEGER,
        author_name TEXT,
        created_date TEXT,
        FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
        )
    ''')
    
    
    # Создание админа
    admin_password = hashlib.sha256('nav-xona@2026'.encode()).hexdigest()
    cursor.execute('SELECT * FROM users WHERE login = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (full_name, age, personal_phones, work_phones, login, password, photo, category, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Главный Администратор', 30, '[]', '[]', 'admin', admin_password, '', 'Руководство', 'admin', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('real_estate_crm.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ================ PAGE ROUTES ================
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin')
@login_required
@admin_required
def admin_page():
    return render_template('admin_korgaron.html')

@app.route('/zadacha')
@login_required
def zadacha_page():
    return render_template('zadacha.html')

@app.route('/zayavka')
@login_required
def zayavka_page():
    return render_template('zayavka.html')

@app.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html')

@app.route('/posts')
@login_required
def posts_page():
    return render_template('posts.html')

# ================ API ROUTES ================

# ================ OBJEKT (ШАХМАТКА) API - ҚИСМИ ПУРРА ================




def auto_create_apartments_for_block(block_id):
    """Автоматӣ эҷоди квартираҳо барои блок"""
    conn = get_db()
    block = conn.execute('SELECT * FROM objekt_blocks WHERE id = ?', (block_id,)).fetchone()
    if not block:
        conn.close()
        return 0
    
    created_count = 0
    for floor in range(block['floor_from'], block['floor_to'] + 1):
        existing = conn.execute(
            'SELECT id FROM objekt_apartments WHERE block_id = ? AND floor = ?',
            (block_id, floor)
        ).fetchone()
        if not existing:
            total_price = block['default_area'] * block['default_price_per_m2']
            conn.execute('''
                INSERT INTO objekt_apartments (
                    block_id, floor, area, rooms, windows, price_per_m2, total_price,
                    status, balcony, bathroom, plan_image, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (block_id, floor, block['default_area'], block['default_rooms'],
                  block['default_windows'], block['default_price_per_m2'], total_price,
                  'free', block['default_balcony'], block['default_bathroom'],
                  block['default_plan_image'], datetime.now().isoformat(), datetime.now().isoformat()))
            created_count += 1
    conn.commit()
    conn.close()
    return created_count


# ==================== API ENDPOINTS ====================

# ---------- ПРОЕКТҲО ----------
@app.route('/api/objekt/projects', methods=['GET'])
@login_required
def get_objekt_projects():
    """Гирифтани ҳамаи проектҳо"""
    conn = get_db()
    try:
        projects = conn.execute('SELECT * FROM objekt_projects ORDER BY id DESC').fetchall()
        return jsonify([dict(p) for p in projects])
    except Exception as e:
        print(f"Error get_objekt_projects: {e}")
        return jsonify([])
    finally:
        conn.close()


@app.route('/api/objekt/projects', methods=['POST'])
@login_required
def create_objekt_project():
    """Эҷоди проекти нав"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO objekt_projects (name, address, developer, description, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data.get('address', ''), data.get('developer', ''),
              data.get('description', ''), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


@app.route('/api/objekt/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_objekt_project(project_id):
    """Таҳрири проект"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE objekt_projects SET 
                name = ?, address = ?, developer = ?, description = ?, updated_date = ?
            WHERE id = ?
        ''', (data['name'], data.get('address', ''), data.get('developer', ''),
              data.get('description', ''), datetime.now().isoformat(), project_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


@app.route('/api/objekt/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_objekt_project(project_id):
    """Нест кардани проект ва ҳамаи блокҳо/квартираҳо"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM objekt_projects WHERE id = ?', (project_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


# ---------- БЛОКҲО ----------
@app.route('/api/objekt/projects/<int:project_id>/blocks', methods=['GET'])
@login_required
def get_objekt_blocks(project_id):
    """Гирифтани блокҳои проект"""
    conn = get_db()
    try:
        blocks = conn.execute('''
            SELECT * FROM objekt_blocks WHERE project_id = ? ORDER BY order_index ASC, id ASC
        ''', (project_id,)).fetchall()
        return jsonify([dict(b) for b in blocks])
    except Exception as e:
        return jsonify([])
    finally:
        conn.close()





@app.route('/api/objekt/blocks/order', methods=['POST'])
@login_required
def update_objekt_blocks_order():
    """Иваз кардани тартиби блокҳо (Drag & Drop)"""
    data = request.json
    block_id = data['block_id']
    target_id = data['target_id']
    
    conn = get_db()
    try:
        # Гирифтани ҳарду блок
        source = conn.execute('SELECT * FROM objekt_blocks WHERE id = ?', (block_id,)).fetchone()
        target = conn.execute('SELECT * FROM objekt_blocks WHERE id = ?', (target_id,)).fetchone()
        
        if not source or not target:
            return jsonify({'success': False, 'error': 'Блок не найден'}), 404
        
        # Иваз кардани order_index
        source_order = source['order_index']
        target_order = target['order_index']
        
        conn.execute('UPDATE objekt_blocks SET order_index = ? WHERE id = ?', (target_order, block_id))
        conn.execute('UPDATE objekt_blocks SET order_index = ? WHERE id = ?', (source_order, target_id))
        conn.commit()
        
        # Баргардонидани ҳамаи блокҳо барои рендеринг
        blocks = conn.execute('''
            SELECT * FROM objekt_blocks WHERE project_id = ? ORDER BY order_index ASC, id ASC
        ''', (source['project_id'],)).fetchall()
        
        return jsonify({'success': True, 'blocks': [dict(b) for b in blocks]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


@app.route('/api/objekt/blocks/<int:block_id>', methods=['DELETE'])
@login_required
def delete_objekt_block(block_id):
    """Нест кардани блок ва ҳамаи квартираҳо"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM objekt_blocks WHERE id = ?', (block_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


# ---------- КВАРТИРАҲО ----------
@app.route('/api/objekt/projects/<int:project_id>/apartments', methods=['GET'])
@login_required
def get_objekt_apartments(project_id):
    """Гирифтани ҳамаи квартираҳои проект"""
    conn = get_db()
    try:
        apartments = conn.execute('''
            SELECT a.*, b.name as block_name 
            FROM objekt_apartments a
            JOIN objekt_blocks b ON a.block_id = b.id
            WHERE b.project_id = ?
            ORDER BY b.order_index ASC, b.id ASC, a.floor ASC
        ''', (project_id,)).fetchall()
        return jsonify([dict(a) for a in apartments])
    except Exception as e:
        return jsonify([])
    finally:
        conn.close()


@app.route('/api/objekt/apartments/<int:apartment_id>', methods=['PUT'])
@login_required
def update_objekt_apartment(apartment_id):
    """Таҳрири пурраи квартира"""
    data = request.json
    conn = get_db()
    try:
        total_price = data.get('area', 0) * data.get('price_per_m2', 0)
        conn.execute('''
            UPDATE objekt_apartments SET
                area = ?, rooms = ?, windows = ?, price_per_m2 = ?,
                total_price = ?, status = ?, balcony = ?, bathroom = ?,
                plan_image = ?, description = ?, updated_date = ?
            WHERE id = ?
        ''', (
            data['area'], data['rooms'], data['windows'], data['price_per_m2'],
            total_price, data['status'], 1 if data.get('balcony') else 0,
            1 if data.get('bathroom') else 0, data.get('plan_image', ''),
            data.get('description', ''), datetime.now().isoformat(), apartment_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


@app.route('/api/objekt/apartments/<int:apartment_id>/status', methods=['PATCH'])
@login_required
def update_objekt_apartment_status(apartment_id):
    """Танҳо статуси квартираро иваз кунед"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE objekt_apartments SET status = ?, updated_date = ? WHERE id = ?
        ''', (data['status'], datetime.now().isoformat(), apartment_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


# ---------- БОРГУЗОРИИ АКС ----------
@app.route('/api/objekt/upload-image', methods=['POST'])
@login_required
def upload_objekt_image():
    """Боргузории акс барои квартира"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Файл не найден'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
    
    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
    upload_dir = os.path.join('uploads', 'objekt_images')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return jsonify({'success': True, 'url': f'/uploads/objekt_images/{filename}'})


# ---------- ЭКСПОРТ ----------
@app.route('/api/objekt/export/excel', methods=['GET'])
@login_required
def export_objekt_apartments_excel():
    """Экспорти квартираҳо ба Excel бо фильтрҳо"""
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status', 'all')
    floor = request.args.get('floor', type=int)
    area_min = request.args.get('area_min', type=float)
    area_max = request.args.get('area_max', type=float)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    rooms = request.args.get('rooms', type=int)
    
    conn = get_db()
    try:
        query = '''
            SELECT a.*, b.name as block_name 
            FROM objekt_apartments a
            JOIN objekt_blocks b ON a.block_id = b.id
            WHERE b.project_id = ?
        '''
        params = [project_id]
        
        if status != 'all':
            query += ' AND a.status = ?'
            params.append(status)
        if floor:
            query += ' AND a.floor = ?'
            params.append(floor)
        if area_min:
            query += ' AND a.area >= ?'
            params.append(area_min)
        if area_max:
            query += ' AND a.area <= ?'
            params.append(area_max)
        if price_min:
            query += ' AND a.total_price >= ?'
            params.append(price_min)
        if price_max:
            query += ' AND a.total_price <= ?'
            params.append(price_max)
        if rooms:
            query += ' AND a.rooms = ?'
            params.append(rooms)
        
        query += ' ORDER BY b.order_index ASC, b.id ASC, a.floor ASC'
        apartments = conn.execute(query, params).fetchall()
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
    
    status_map = {'free': 'Свободна', 'reserved': 'Бронь', 'sold': 'Фурӯхта'}
    data = []
    for ap in apartments:
        data.append({
            'Блок': ap['block_name'],
            'Этаж': ap['floor'],
            'Масоҳат (м²)': ap['area'],
            'Ҳуҷраҳо': ap['rooms'],
            'Тирезаҳо': ap['windows'],
            'Нархи як м² ($)': ap['price_per_m2'],
            'Нархи умумӣ ($)': ap['total_price'],
            'Статус': status_map.get(ap['status'], ap['status']),
            'Балкон': 'Да' if ap['balcony'] else 'Не',
            'Санузел': 'Да' if ap['bathroom'] else 'Не',
            'Тавсиф': ap['description'] or ''
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Квартираҳо', index=False)
        worksheet = writer.sheets['Квартираҳо']
        for column in worksheet.columns:
            max_length = 0
            col_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 40)
    
    output.seek(0)
    return send_file(
        output,
        download_name=f'apartments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# ==================== MIGRATION FOR OBJEKT TABLES ====================
def migrate_objekt_tables():
    """Иловаи сутунҳои нав ба таблитсаҳои objekt"""
    conn = get_db()
    try:
        # Ба objekt_blocks илова кардан
        cursor = conn.execute("PRAGMA table_info(objekt_blocks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'default_bathroom_type' not in columns:
            conn.execute('ALTER TABLE objekt_blocks ADD COLUMN default_bathroom_type TEXT DEFAULT "combined"')
            print("✅ Added default_bathroom_type to objekt_blocks")
        
        if 'default_bathroom_count' not in columns:
            conn.execute('ALTER TABLE objekt_blocks ADD COLUMN default_bathroom_count INTEGER DEFAULT 1')
            print("✅ Added default_bathroom_count to objekt_blocks")
        
        # Ба objekt_apartments илова кардан
        cursor = conn.execute("PRAGMA table_info(objekt_apartments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'bathroom_type' not in columns:
            conn.execute('ALTER TABLE objekt_apartments ADD COLUMN bathroom_type TEXT DEFAULT "combined"')
            print("✅ Added bathroom_type to objekt_apartments")
        
        if 'bathroom_count' not in columns:
            conn.execute('ALTER TABLE objekt_apartments ADD COLUMN bathroom_count INTEGER DEFAULT 1')
            print("✅ Added bathroom_count to objekt_apartments")
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

# Функсияи навсозии эҷоди автоматии квартираҳо
def auto_create_apartments_for_block_updated(block_id):
    """Автоматӣ эҷоди квартираҳо барои блок бо сутунҳои нав"""
    conn = get_db()
    block = conn.execute('SELECT * FROM objekt_blocks WHERE id = ?', (block_id,)).fetchone()
    if not block:
        conn.close()
        return 0
    
    created_count = 0
    for floor in range(block['floor_from'], block['floor_to'] + 1):
        existing = conn.execute(
            'SELECT id FROM objekt_apartments WHERE block_id = ? AND floor = ?',
            (block_id, floor)
        ).fetchone()
        if not existing:
            total_price = block['default_area'] * block['default_price_per_m2']
            bathroom_type = block['default_bathroom_type'] if block['default_bathroom_type'] else 'combined'
            bathroom_count = block['default_bathroom_count'] if block['default_bathroom_count'] else 1
            
            conn.execute('''
                INSERT INTO objekt_apartments (
                    block_id, floor, area, rooms, windows, price_per_m2, total_price,
                    status, balcony, bathroom_type, bathroom_count, plan_image, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (block_id, floor, block['default_area'], block['default_rooms'],
                  block['default_windows'], block['default_price_per_m2'], total_price,
                  'free', block['default_balcony'], bathroom_type, bathroom_count,
                  block['default_plan_image'], datetime.now().isoformat(), datetime.now().isoformat()))
            created_count += 1
    conn.commit()
    conn.close()
    return created_count

# Навсозии функсияи create_objekt_block
@app.route('/api/objekt/blocks', methods=['POST'])
@login_required
def create_objekt_block_updated():
    """Эҷоди блок бо боргузории акс ва сутунҳои нав"""
    project_id = request.form.get('project_id')
    name = request.form.get('name')
    floor_from = int(request.form.get('floor_from'))
    floor_to = int(request.form.get('floor_to'))
    default_area = float(request.form.get('default_area'))
    default_rooms = int(request.form.get('default_rooms'))
    default_windows = int(request.form.get('default_windows'))
    default_price_per_m2 = float(request.form.get('default_price_per_m2'))
    default_balcony = 1 if request.form.get('default_balcony') == 'true' else 0
    default_bathroom_type = request.form.get('default_bathroom_type', 'combined')
    default_bathroom_count = int(request.form.get('default_bathroom_count', 1))
    description = request.form.get('description', '')
    
    plan_image = ''
    if 'plan_image' in request.files:
        file = request.files['plan_image']
        if file and file.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            upload_dir = os.path.join('uploads', 'objekt_plans')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            plan_image = f'/uploads/objekt_plans/{filename}'
    
    conn = get_db()
    try:
        max_order = conn.execute('SELECT COALESCE(MAX(order_index), -1) as max_order FROM objekt_blocks WHERE project_id = ?', (project_id,)).fetchone()
        order_index = (max_order['max_order'] or -1) + 1
        
        cursor = conn.execute('''
            INSERT INTO objekt_blocks (
                project_id, name, floor_from, floor_to, default_area, default_rooms,
                default_windows, default_price_per_m2, default_balcony, 
                default_bathroom_type, default_bathroom_count,
                default_plan_image, description, order_index, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, name, floor_from, floor_to, default_area, default_rooms,
              default_windows, default_price_per_m2, default_balcony,
              default_bathroom_type, default_bathroom_count,
              plan_image, description, order_index, datetime.now().isoformat()))
        block_id = cursor.lastrowid
        conn.commit()
        
        created_count = auto_create_apartments_for_block_updated(block_id)
        
        return jsonify({'success': True, 'id': block_id, 'count': created_count})
    except Exception as e:
        print(f"Error create_objekt_block: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# Навсозии функсияи update_objekt_apartment
@app.route('/api/objekt/apartments/<int:apartment_id>', methods=['PUT'])
@login_required
def update_objekt_apartment_updated(apartment_id):
    """Таҳрири пурраи квартира бо сутунҳои нав"""
    data = request.json
    conn = get_db()
    try:
        total_price = data.get('area', 0) * data.get('price_per_m2', 0)
        conn.execute('''
            UPDATE objekt_apartments SET
                area = ?, rooms = ?, windows = ?, price_per_m2 = ?,
                total_price = ?, status = ?, balcony = ?, 
                bathroom_type = ?, bathroom_count = ?,
                plan_image = ?, description = ?, updated_date = ?
            WHERE id = ?
        ''', (
            data['area'], data['rooms'], data['windows'], data['price_per_m2'],
            total_price, data['status'], 1 if data.get('balcony') else 0,
            data.get('bathroom_type', 'combined'), data.get('bathroom_count', 1),
            data.get('plan_image', ''), data.get('description', ''), 
            datetime.now().isoformat(), apartment_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_objekt_apartment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# Функсияи навсозии init_objekt_tables
def init_objekt_tables_updated():
    """Эҷоди таблицаҳои лозима барои шахматка бо сутунҳои нав"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objekt_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            developer TEXT,
            description TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objekt_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            floor_from INTEGER NOT NULL,
            floor_to INTEGER NOT NULL,
            default_area REAL NOT NULL,
            default_rooms INTEGER NOT NULL,
            default_windows INTEGER NOT NULL,
            default_price_per_m2 REAL NOT NULL,
            default_balcony INTEGER DEFAULT 0,
            default_bathroom_type TEXT DEFAULT 'combined',
            default_bathroom_count INTEGER DEFAULT 1,
            default_plan_image TEXT,
            description TEXT,
            order_index INTEGER DEFAULT 0,
            created_date TEXT,
            FOREIGN KEY (project_id) REFERENCES objekt_projects (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objekt_apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            floor INTEGER NOT NULL,
            area REAL NOT NULL,
            rooms INTEGER NOT NULL,
            windows INTEGER NOT NULL,
            price_per_m2 REAL NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'free',
            balcony INTEGER DEFAULT 0,
            bathroom_type TEXT DEFAULT 'combined',
            bathroom_count INTEGER DEFAULT 1,
            plan_image TEXT,
            description TEXT,
            client_name TEXT,
            client_phone TEXT,
            created_date TEXT,
            updated_date TEXT,
            FOREIGN KEY (block_id) REFERENCES objekt_blocks (id) ON DELETE CASCADE,
            UNIQUE(block_id, floor)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Табличаҳои objekt бо сутунҳои нав эҷод шуданд")

# Навсозии функсияи export_objekt_apartments_pdf (ислоҳи хатои PDF)
@app.route('/api/objekt/export/pdf/<int:project_id>', methods=['GET'])
@login_required
def export_objekt_apartments_pdf_fixed(project_id):
    """Экспорти шахматка ба PDF бо ислоҳи хатоҳо"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return jsonify({'error': 'ReportLab не установлен. Установите: pip install reportlab'}), 500
    
    conn = get_db()
    try:
        project = conn.execute('SELECT * FROM objekt_projects WHERE id = ?', (project_id,)).fetchone()
        if not project:
            return jsonify({'error': 'Проект не найден'}), 404
        
        blocks = conn.execute('SELECT * FROM objekt_blocks WHERE project_id = ? ORDER BY order_index ASC, id ASC', (project_id,)).fetchall()
        apartments = conn.execute('''
            SELECT a.*, b.name as block_name 
            FROM objekt_apartments a
            JOIN objekt_blocks b ON a.block_id = b.id
            WHERE b.project_id = ?
            ORDER BY b.order_index ASC, b.id ASC, a.floor ASC
        ''', (project_id,)).fetchall()
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
    
    if not blocks or not apartments:
        return jsonify({'error': 'Нет данных для экспорта'}), 400
    
    floors = sorted(set([ap['floor'] for ap in apartments]))
    status_map = {'free': '🟢', 'reserved': '🟡', 'sold': '🔴'}
    
    # Тайёр кардани таблитса
    table_data = [['Блок / Этаж'] + [str(f) for f in floors]]
    for block in blocks:
        row = [block['name']]
        for floor in floors:
            apt = next((a for a in apartments if a['block_id'] == block['id'] and a['floor'] == floor), None)
            if apt:
                row.append(status_map.get(apt['status'], '⚪'))
            else:
                row.append('—')
        table_data.append(row)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                           leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    
    # Сарлавҳа
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=10)
    story.append(Paragraph(f"Шахматка - {project['name']}", title_style))
    
    # Маълумот
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    story.append(Paragraph(f"Суроға: {project['address'] or '—'}", info_style))
    story.append(Paragraph(f"Сана: {datetime.now().strftime('%d.%m.%Y')}", info_style))
    story.append(Spacer(1, 15))
    
    # Легенда
    legend_data = [['🟢', 'Свободна'], ['🟡', 'Бронь'], ['🔴', 'Фурӯхта']]
    legend_table = Table(legend_data, colWidths=[40, 80])
    legend_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(legend_table)
    story.append(Spacer(1, 15))
    
    # Таблицаи асосӣ
    col_widths = [80] + [45] * len(floors)
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
    ]))
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        download_name=f'chessboard_{project["name"]}_{datetime.now().strftime("%Y%m%d")}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

# Даъвати функсияҳои мигратсия
migrate_objekt_tables()

# ==================== UPDATE OBJEKT BLOCK (PUT) ====================
@app.route('/api/objekt/blocks/<int:block_id>', methods=['PUT'])
@login_required
def update_objekt_block(block_id):
    """Таҳрири блок ва навсозии ҳамаи квартираҳои марбут"""
    conn = get_db()
    
    # Санҷиши вуҷуди блок
    block = conn.execute('SELECT * FROM objekt_blocks WHERE id = ?', (block_id,)).fetchone()
    if not block:
        conn.close()
        return jsonify({'success': False, 'error': 'Блок не найден'}), 404
    
    # Гирифтани маълумотҳо аз form-data
    name = request.form.get('name')
    floor_from = int(request.form.get('floor_from'))
    floor_to = int(request.form.get('floor_to'))
    default_area = float(request.form.get('default_area'))
    default_rooms = int(request.form.get('default_rooms'))
    default_windows = int(request.form.get('default_windows'))
    default_price_per_m2 = float(request.form.get('default_price_per_m2'))
    default_balcony = 1 if request.form.get('default_balcony') == 'true' else 0
    default_bathroom_type = request.form.get('default_bathroom_type', 'combined')
    default_bathroom_count = int(request.form.get('default_bathroom_count', 1))
    description = request.form.get('description', '')
    
    # Боргузории акси нав (агар бошад)
    plan_image = block['default_plan_image']
    if 'plan_image' in request.files:
        file = request.files['plan_image']
        if file and file.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            upload_dir = os.path.join('uploads', 'objekt_plans')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            plan_image = f'/uploads/objekt_plans/{filename}'
    
    try:
        # Навсозии блок
        conn.execute('''
            UPDATE objekt_blocks SET 
                name = ?, floor_from = ?, floor_to = ?, default_area = ?,
                default_rooms = ?, default_windows = ?, default_price_per_m2 = ?,
                default_balcony = ?, default_bathroom_type = ?, default_bathroom_count = ?,
                default_plan_image = ?, description = ?
            WHERE id = ?
        ''', (name, floor_from, floor_to, default_area, default_rooms, default_windows,
              default_price_per_m2, default_balcony, default_bathroom_type, default_bathroom_count,
              plan_image, description, block_id))
        
        # Навсозии ҳамаи квартираҳои марбут ба блок
        for floor in range(floor_from, floor_to + 1):
            total_price = default_area * default_price_per_m2
            conn.execute('''
                UPDATE objekt_apartments SET
                    area = ?, rooms = ?, windows = ?, price_per_m2 = ?,
                    total_price = ?, balcony = ?, bathroom_type = ?, bathroom_count = ?,
                    plan_image = ?, description = ?, updated_date = ?
                WHERE block_id = ? AND floor = ?
            ''', (default_area, default_rooms, default_windows, default_price_per_m2,
                  total_price, default_balcony, default_bathroom_type, default_bathroom_count,
                  plan_image, description, datetime.now().isoformat(), block_id, floor))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_objekt_block: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()
    
@app.route('/obiekt')
@login_required
def obiekt_page():
    """Саҳифаи шахматкаи недвижимости"""
    return render_template('obiekt.html')


# ==================== ИНИЦИАЛИЗАЦИЯ ====================
# Эҷоди таблицаҳо ҳангоми старт
try:
    init_objekt_tables()
    print("✅ Объект таблицаҳо тайёр шуданд")
except Exception as e:
    print(f"⚠️ Хатогӣ дар эҷоди таблицаҳои объект: {e}")

# ================ BOARDS API ================

@app.route('/api/requests-boards', methods=['GET'])
@login_required
def get_requests_boards():
    """Гирифтани ҳамаи доскаҳои дастрас"""
    conn = get_db()
    if session['role'] == 'admin':
        boards = conn.execute('''
            SELECT * FROM requests_boards 
            WHERE is_public = 1 OR author_id = ?
            ORDER BY id DESC
        ''', (session['user_id'],)).fetchall()
    else:
        boards = conn.execute('''
            SELECT * FROM requests_boards 
            WHERE is_public = 1
            ORDER BY id DESC
        ''').fetchall()
    conn.close()
    return jsonify([dict(board) for board in boards])

@app.route('/api/requests-boards', methods=['POST'])
@login_required
def create_requests_board():
    """Эҷоди доскаи нав"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO requests_boards (title, color, is_public, author_id, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['title'], data.get('color', '#0f172a'), data['is_public'], 
              session['user_id'], datetime.now().isoformat(), datetime.now().isoformat()))
        board_id = cursor.lastrowid
        
        # Илова кардани колонкаҳои стандартӣ
        default_columns = ['Нав', 'Дар кор', 'Анҷом', 'Бекор']
        default_colors = ['#3b82f6', '#f59e0b', '#22c55e', '#ef4444']
        for i, col in enumerate(default_columns):
            conn.execute('''
                INSERT INTO requests_columns (board_id, title, color, order_index, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (board_id, col, default_colors[i], i, datetime.now().isoformat()))
        
        conn.commit()
        return jsonify({'success': True, 'id': board_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-boards/<int:board_id>', methods=['PUT'])
@login_required
def update_requests_board(board_id):
    """Таҳрири доска"""
    data = request.json
    conn = get_db()
    
    board = conn.execute('SELECT * FROM requests_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('''
            UPDATE requests_boards SET title = ?, color = ?, is_public = ?, updated_date = ?
            WHERE id = ?
        ''', (data['title'], data.get('color', '#0f172a'), data['is_public'], 
              datetime.now().isoformat(), board_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-boards/<int:board_id>', methods=['DELETE'])
@login_required
def delete_requests_board(board_id):
    """Нест кардани доска"""
    conn = get_db()
    
    board = conn.execute('SELECT * FROM requests_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('DELETE FROM requests_boards WHERE id = ?', (board_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# ================ COLUMNS API ================

@app.route('/api/requests-boards/<int:board_id>/columns', methods=['GET'])
@login_required
def get_requests_columns_by_board(board_id):
    """Гирифтани колонкаҳои доска"""
    conn = get_db()
    columns = conn.execute('''
        SELECT * FROM requests_columns WHERE board_id = ? ORDER BY order_index ASC
    ''', (board_id,)).fetchall()
    conn.close()
    return jsonify([dict(col) for col in columns])

@app.route('/api/requests-columns', methods=['POST'])
@login_required
def create_requests_column():
    """Эҷоди колонкаи нав"""
    data = request.json
    conn = get_db()
    
    # Санҷиши дастрасӣ ба доска
    board = conn.execute('SELECT * FROM requests_boards WHERE id = ?', (data['board_id'],)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin' and board['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        max_order = conn.execute('SELECT MAX(order_index) as max_order FROM requests_columns WHERE board_id = ?',
                                  (data['board_id'],)).fetchone()
        order_index = (max_order['max_order'] or -1) + 1
        
        cursor = conn.execute('''
            INSERT INTO requests_columns (board_id, title, color, order_index, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['board_id'], data['title'], data.get('color', '#3b82f6'), order_index, datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-columns/<int:column_id>', methods=['PUT'])
@login_required
def update_requests_column(column_id):
    """Таҳрири колонка"""
    data = request.json
    conn = get_db()
    
    column = conn.execute('''
        SELECT c.*, b.author_id as board_author_id, b.is_public
        FROM requests_columns c
        JOIN requests_boards b ON c.board_id = b.id
        WHERE c.id = ?
    ''', (column_id,)).fetchone()
    
    if not column:
        return jsonify({'success': False, 'error': 'Колонка не найдена'}), 404
    
    if column['board_author_id'] != session['user_id'] and session['role'] != 'admin' and column['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('''
            UPDATE requests_columns SET title = ?, color = ?, order_index = ?
            WHERE id = ?
        ''', (data['title'], data.get('color', '#3b82f6'), data.get('order_index', 0), column_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-columns/<int:column_id>', methods=['DELETE'])
@login_required
def delete_requests_column(column_id):
    """Нест кардани колонка ва ҳама заявкаҳои он"""
    conn = get_db()
    
    column = conn.execute('''
        SELECT c.*, b.author_id as board_author_id, b.is_public
        FROM requests_columns c
        JOIN requests_boards b ON c.board_id = b.id
        WHERE c.id = ?
    ''', (column_id,)).fetchone()
    
    if not column:
        return jsonify({'success': False, 'error': 'Колонка не найдена'}), 404
    
    if column['board_author_id'] != session['user_id'] and session['role'] != 'admin' and column['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('DELETE FROM requests_columns WHERE id = ?', (column_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-columns/<int:column_id>/order', methods=['PUT'])
@login_required
def update_requests_column_order(column_id):
    """Иваз кардани тартиби колонкаҳо (swap)"""
    data = request.json
    conn = get_db()
    try:
        target_id = data['target_id']
        # Гирифтани ҳарду колонка
        col1 = conn.execute('SELECT order_index FROM requests_columns WHERE id = ?', (column_id,)).fetchone()
        col2 = conn.execute('SELECT order_index FROM requests_columns WHERE id = ?', (target_id,)).fetchone()
        
        if col1 and col2:
            conn.execute('UPDATE requests_columns SET order_index = ? WHERE id = ?', (col2['order_index'], column_id))
            conn.execute('UPDATE requests_columns SET order_index = ? WHERE id = ?', (col1['order_index'], target_id))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# ================ REQUESTS API ================

@app.route('/api/requests-board/<int:board_id>/requests', methods=['GET'])
@login_required
def get_requests_by_board(board_id):
    """Гирифтани ҳамаи заявкаҳои доска"""
    conn = get_db()
    requests = conn.execute('''
        SELECT r.*, u.full_name as author_name, u2.full_name as executor_name
        FROM requests_items r
        LEFT JOIN users u ON r.author_id = u.id
        LEFT JOIN users u2 ON r.executor_id = u2.id
        WHERE r.board_id = ?
        ORDER BY r.column_id ASC, r.order_index ASC
    ''', (board_id,)).fetchall()
    conn.close()
    return jsonify([dict(req) for req in requests])

@app.route('/api/requests-new', methods=['POST'])
@login_required
def create_requests_item():
    """Эҷоди заявкаи нав"""
    data = request.json
    conn = get_db()
    
    # Гирифтани маълумоти иҷрокунанда
    executor_name = ''
    if data.get('executor_id'):
        user = conn.execute('SELECT full_name FROM users WHERE id = ?', (data['executor_id'],)).fetchone()
        if user:
            executor_name = user['full_name']
    
    # Гирифтани максималӣ order_index дар колонка
    max_order = conn.execute('SELECT MAX(order_index) as max_order FROM requests_items WHERE column_id = ?',
                             (data['column_id'],)).fetchone()
    order_index = (max_order['max_order'] or -1) + 1
    
    try:
        cursor = conn.execute('''
            INSERT INTO requests_items (
                column_id, board_id, property_type, address, area, rooms, windows,
                floor, total_floors, total_price, price_per_m2, phone, client_name,
                comment, author_id, author_name, executor_id, executor_name, files,
                order_index, created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['column_id'], data['board_id'], data['property_type'], data['address'],
            data['area'], data['rooms'], data['windows'], data['floor'], data['total_floors'],
            data['total_price'], data['price_per_m2'], data['phone'], data['client_name'],
            data.get('comment', ''), session['user_id'], session['user_name'],
            data.get('executor_id'), executor_name, json.dumps(data.get('files', [])),
            order_index, datetime.now().isoformat(), datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error create_requests_item: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-update/<int:request_id>', methods=['PUT'])
@login_required
def update_requests_item(request_id):
    """Таҳрири заявка"""
    data = request.json
    conn = get_db()
    
    # Санҷиши вуҷуд
    req = conn.execute('SELECT * FROM requests_items WHERE id = ?', (request_id,)).fetchone()
    if not req:
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    
    # Санҷиши ҳуқуқ
    if req['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    # Гирифтани номи иҷрокунанда
    executor_name = ''
    if data.get('executor_id'):
        user = conn.execute('SELECT full_name FROM users WHERE id = ?', (data['executor_id'],)).fetchone()
        if user:
            executor_name = user['full_name']
    
    try:
        conn.execute('''
            UPDATE requests_items SET
                property_type = ?, address = ?, area = ?, rooms = ?, windows = ?,
                floor = ?, total_floors = ?, total_price = ?, price_per_m2 = ?,
                phone = ?, client_name = ?, comment = ?, executor_id = ?,
                executor_name = ?, files = ?, updated_date = ?
            WHERE id = ?
        ''', (
            data['property_type'], data['address'], data['area'], data['rooms'], data['windows'],
            data['floor'], data['total_floors'], data['total_price'], data['price_per_m2'],
            data['phone'], data['client_name'], data.get('comment', ''),
            data.get('executor_id'), executor_name, json.dumps(data.get('files', [])),
            datetime.now().isoformat(), request_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests-delete/<int:request_id>', methods=['DELETE'])
@login_required
def delete_requests_item(request_id):
    """Нест кардани заявка"""
    conn = get_db()
    
    req = conn.execute('SELECT * FROM requests_items WHERE id = ?', (request_id,)).fetchone()
    if not req:
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    
    if req['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    conn.execute('DELETE FROM requests_items WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/requests-move', methods=['POST'])
@login_required
def move_requests_item():
    """Ҷой иваз кардани заявка (байни колонкаҳо ва дар дохили колонка)"""
    data = request.json
    conn = get_db()
    
    request_id = data['request_id']
    new_column_id = data['column_id']
    new_order = data.get('order_index')
    
    # Гирифтани заявка
    req = conn.execute('SELECT * FROM requests_items WHERE id = ?', (request_id,)).fetchone()
    if not req:
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    
    old_column_id = req['column_id']
    old_order = req['order_index']
    
    try:
        if old_column_id == new_column_id:
            # Ҷой иваз кардан дар дохили як колонка
            if new_order is not None:
                if new_order < old_order:
                    # Болои ҳозира - ҳамаи заявкаҳои байниро як адад боло мебарем
                    conn.execute('''
                        UPDATE requests_items SET order_index = order_index + 1 
                        WHERE column_id = ? AND order_index >= ? AND order_index < ?
                    ''', (new_column_id, new_order, old_order))
                else:
                    # Поёни ҳозира - ҳамаи заявкаҳои байниро як адад поён мебарем
                    conn.execute('''
                        UPDATE requests_items SET order_index = order_index - 1 
                        WHERE column_id = ? AND order_index > ? AND order_index <= ?
                    ''', (new_column_id, old_order, new_order - 1))
                
                # Навсозии order_index заявкаи ҳозира
                conn.execute('''
                    UPDATE requests_items SET order_index = ?, updated_date = ?
                    WHERE id = ?
                ''', (new_order, datetime.now().isoformat(), request_id))
        else:
            # Ба колонкаи дигар мебарем
            # Дар колонкаи кӯҳна - ҳамаи пас аз онро як адад кам мекунем
            conn.execute('''
                UPDATE requests_items SET order_index = order_index - 1 
                WHERE column_id = ? AND order_index > ?
            ''', (old_column_id, old_order))
            
            # Дар колонкаи нав - ҳамаи аз new_order ба болоро як адад зиёд мекунем
            if new_order is not None:
                conn.execute('''
                    UPDATE requests_items SET order_index = order_index + 1 
                    WHERE column_id = ? AND order_index >= ?
                ''', (new_column_id, new_order))
            
            # Навсозии заявка
            conn.execute('''
                UPDATE requests_items SET column_id = ?, order_index = ?, updated_date = ?
                WHERE id = ?
            ''', (new_column_id, new_order if new_order is not None else 0, datetime.now().isoformat(), request_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/upload-request-file', methods=['POST'])
@login_required
def upload_request_file():
    """Боргузории файл барои заявка"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    original_name = file.filename
    ext = original_name.split('.')[-1].lower()
    safe_filename = secure_filename(f"{datetime.now().timestamp()}_{original_name}")
    
    # Муайян кардани намуди файл
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']:
        file_type = 'image'
        subfolder = 'request_images'
    elif ext in ['mp4', 'webm', 'mov', 'avi', 'mkv', 'flv']:
        file_type = 'video'
        subfolder = 'request_videos'
    elif ext == 'pdf':
        file_type = 'pdf'
        subfolder = 'request_docs'
    else:
        file_type = 'document'
        subfolder = 'request_docs'
    
    upload_dir = os.path.join('uploads', 'requests', subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, safe_filename)
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'name': original_name,
        'path': f'/uploads/requests/{subfolder}/{safe_filename}',
        'type': file_type
    })

@app.route('/api/requests-export/excel', methods=['GET'])
@login_required
def export_requests_kanban_excel():
    """Экспорти заявкаҳо ба Excel бо фильтрҳо"""
    board_id = request.args.get('board_id')
    date_filter = request.args.get('date_filter', 'all')
    type_filter = request.args.get('type_filter', 'all')
    author_filter = request.args.get('author_filter', 'all')
    
    conn = get_db()
    query = '''
        SELECT r.*, u.full_name as author_name, u2.full_name as executor_name, c.title as column_title
        FROM requests_items r
        LEFT JOIN users u ON r.author_id = u.id
        LEFT JOIN users u2 ON r.executor_id = u2.id
        LEFT JOIN requests_columns c ON r.column_id = c.id
        WHERE r.board_id = ?
    '''
    params = [board_id]
    
    if type_filter != 'all':
        query += ' AND r.property_type = ?'
        params.append(type_filter)
    
    if author_filter != 'all':
        query += ' AND r.author_id = ?'
        params.append(int(author_filter))
    
    if date_filter == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        query += ' AND DATE(r.created_date) = ?'
        params.append(today)
    elif date_filter == 'week':
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query += ' AND DATE(r.created_date) >= ?'
        params.append(week_ago)
    elif date_filter == 'month':
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query += ' AND DATE(r.created_date) >= ?'
        params.append(month_ago)
    
    query += ' ORDER BY r.created_date DESC'
    
    requests = conn.execute(query, params).fetchall()
    conn.close()
    
    data = []
    for req in requests:
        data.append({
            'ID': req['id'],
            'Колонка': req['column_title'],
            'Клиент': req['client_name'],
            'Телефон': req['phone'],
            'Намуди амвол': req['property_type'],
            'Суроға': req['address'],
            'Масоҳат (м²)': req['area'],
            'Ҳуҷраҳо': req['rooms'],
            'Тирезаҳо': req['windows'],
            'Ошёна': req['floor'],
            'Ошёнаҳои бино': req['total_floors'],
            'Нархи умумӣ (₽)': req['total_price'],
            'Нархи як м² (₽)': req['price_per_m2'],
            'Автор': req['author_name'],
            'Иҷрокунанда': req['executor_name'],
            'Шарҳ': req['comment'] or '',
            'Санаи эҷод': req['created_date']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Заявкаҳо', index=False)
        
        worksheet = writer.sheets['Заявкаҳо']
        for column in worksheet.columns:
            max_length = 0
            col_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
    
    output.seek(0)
    return send_file(output, 
                    download_name=f'requests_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    as_attachment=True,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ================ LID (LEADS) API ================

@app.route('/api/lids', methods=['GET'])
@login_required
def get_lids():
    # Гирифтани параметрҳои филтр
    search_name = request.args.get('search_name', '')
    search_phone = request.args.get('search_phone', '')
    mortgage = request.args.get('mortgage', 'all')
    box = request.args.get('box', 'all')
    source = request.args.get('source', 'all')
    user_filter = request.args.get('user_filter', 'all')
    date_range = request.args.get('date_range', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db()
    query = '''
        SELECT l.*, u.full_name as author_name
        FROM lids l
        LEFT JOIN users u ON l.author_id = u.id
        WHERE 1=1
    '''
    params = []
    
    # Фильтр по правам (сотрудник видит только свои лиды)
    if session['role'] != 'admin' and session['category'] == 'Отдел продаж':
        query += ' AND l.author_id = ?'
        params.append(session['user_id'])
    
    # Поиск по имени
    if search_name:
        query += ' AND l.client_name LIKE ?'
        params.append(f'%{search_name}%')
    
    # Поиск по телефону
    if search_phone:
        query += ' AND l.phone LIKE ?'
        params.append(f'%{search_phone}%')
    
    # Фильтр по ипотеке
    if mortgage == 'yes':
        query += ' AND l.mortgage = 1'
    elif mortgage == 'no':
        query += ' AND l.mortgage = 0'
    
    # Фильтр по коробке
    if box == 'yes':
        query += ' AND l.box = 1'
    elif box == 'no':
        query += ' AND l.box = 0'
    
    # Фильтр по источнику
    if source != 'all':
        query += ' AND l.source = ?'
        params.append(source)
    
    # Фильтр по сотруднику (только для админа)
    if user_filter != 'all' and session['role'] == 'admin':
        query += ' AND l.author_id = ?'
        params.append(int(user_filter))
    
    # Фильтр по дате
    if date_range == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        query += ' AND DATE(l.created_date) = ?'
        params.append(today)
    elif date_range == 'week':
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        query += ' AND DATE(l.created_date) >= ?'
        params.append(start_of_week.strftime('%Y-%m-%d'))
    elif date_range == 'month':
        now = datetime.now()
        start_of_month = now.replace(day=1)
        query += ' AND DATE(l.created_date) >= ?'
        params.append(start_of_month.strftime('%Y-%m-%d'))
    elif date_range == 'range' and date_from and date_to:
        query += ' AND DATE(l.created_date) BETWEEN ? AND ?'
        params.extend([date_from, date_to])
    
    query += ' ORDER BY l.id DESC'
    lids = conn.execute(query, params).fetchall()
    
    # Статистика для отдела продаж
    stats = {}
    if session['category'] == 'Отдел продаж' or session['role'] == 'admin':
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = conn.execute('SELECT COUNT(*) as count FROM lids WHERE DATE(created_date) = ? AND author_id = ?', 
                                   (today, session['user_id'])).fetchone()
        
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
        week_count = conn.execute('SELECT COUNT(*) as count FROM lids WHERE DATE(created_date) >= ? AND author_id = ?',
                                  (week_start, session['user_id'])).fetchone()
        
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        month_count = conn.execute('SELECT COUNT(*) as count FROM lids WHERE DATE(created_date) >= ? AND author_id = ?',
                                   (month_start, session['user_id'])).fetchone()
        
        # Статистика по источникам
        sources_stats = {}
        for s in ['Входящий', 'Исходящий', 'WhatsApp', 'Telegram', 'Somon.tj', 'Instagram', 'TikTok', 'Офис застройщика', 'Наш офис', 'Холодный контакт']:
            count = conn.execute('SELECT COUNT(*) as count FROM lids WHERE source = ? AND author_id = ?',
                                (s, session['user_id'])).fetchone()
            sources_stats[s] = count['count']
        
        stats = {
            'today': today_count['count'],
            'week': week_count['count'],
            'month': month_count['count'],
            'by_source': sources_stats
        }
    
    conn.close()
    return jsonify({'lids': [dict(lid) for lid in lids], 'stats': stats})

@app.route('/api/lids', methods=['POST'])
@login_required
def add_lid():
    data = request.json
    
    # Танҳо сотсиёти отдели продаж метавонанд лид илова кунанд
    if session['category'] != 'Отдел продаж' and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO lids (client_name, phone, topic, comment, source, mortgage, box, author_id, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['client_name'], data['phone'], data.get('topic', ''), data.get('comment', ''),
            data['source'], 1 if data.get('mortgage') else 0, 1 if data.get('box') else 0,
            session['user_id'], datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/lids/<int:lid_id>', methods=['PUT'])
@login_required
def update_lid(lid_id):
    data = request.json
    conn = get_db()
    lid = conn.execute('SELECT * FROM lids WHERE id = ?', (lid_id,)).fetchone()
    
    if not lid:
        return jsonify({'success': False, 'error': 'Лид не найден'}), 404
    
    # Проверка прав
    if lid['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('''
            UPDATE lids SET client_name = ?, phone = ?, topic = ?, comment = ?,
            source = ?, mortgage = ?, box = ? WHERE id = ?
        ''', (
            data['client_name'], data['phone'], data.get('topic', ''), data.get('comment', ''),
            data['source'], 1 if data.get('mortgage') else 0, 1 if data.get('box') else 0, lid_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/lids/<int:lid_id>', methods=['DELETE'])
@login_required
def delete_lid(lid_id):
    conn = get_db()
    lid = conn.execute('SELECT * FROM lids WHERE id = ?', (lid_id,)).fetchone()
    
    if not lid:
        return jsonify({'success': False, 'error': 'Лид не найден'}), 404
    
    if lid['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    conn.execute('DELETE FROM lids WHERE id = ?', (lid_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/lids/export', methods=['GET'])
@login_required
def export_lids():
    # Гирифтани параметрҳои филтр
    search_name = request.args.get('search_name', '')
    search_phone = request.args.get('search_phone', '')
    mortgage = request.args.get('mortgage', 'all')
    box = request.args.get('box', 'all')
    source = request.args.get('source', 'all')
    user_filter = request.args.get('user_filter', 'all')
    date_range = request.args.get('date_range', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db()
    query = '''
        SELECT l.*, u.full_name as author_name
        FROM lids l
        LEFT JOIN users u ON l.author_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if session['role'] != 'admin' and session['category'] == 'Отдел продаж':
        query += ' AND l.author_id = ?'
        params.append(session['user_id'])
    
    if search_name:
        query += ' AND l.client_name LIKE ?'
        params.append(f'%{search_name}%')
    if search_phone:
        query += ' AND l.phone LIKE ?'
        params.append(f'%{search_phone}%')
    if mortgage == 'yes':
        query += ' AND l.mortgage = 1'
    elif mortgage == 'no':
        query += ' AND l.mortgage = 0'
    if box == 'yes':
        query += ' AND l.box = 1'
    elif box == 'no':
        query += ' AND l.box = 0'
    if source != 'all':
        query += ' AND l.source = ?'
        params.append(source)
    if user_filter != 'all' and session['role'] == 'admin':
        query += ' AND l.author_id = ?'
        params.append(int(user_filter))
    
    if date_range == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        query += ' AND DATE(l.created_date) = ?'
        params.append(today)
    elif date_range == 'week':
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        query += ' AND DATE(l.created_date) >= ?'
        params.append(start_of_week.strftime('%Y-%m-%d'))
    elif date_range == 'month':
        now = datetime.now()
        start_of_month = now.replace(day=1)
        query += ' AND DATE(l.created_date) >= ?'
        params.append(start_of_month.strftime('%Y-%m-%d'))
    elif date_range == 'range' and date_from and date_to:
        query += ' AND DATE(l.created_date) BETWEEN ? AND ?'
        params.extend([date_from, date_to])
    
    query += ' ORDER BY l.id DESC'
    lids = conn.execute(query, params).fetchall()
    conn.close()
    
    # Создание Excel
    data = []
    source_map = {
        'Входящий': '📞 Входящий', 'Исходящий': '📞 Исходящий',
        'WhatsApp': '💬 WhatsApp', 'Telegram': '✈️ Telegram',
        'Somon.tj': '🏠 Somon.tj', 'Instagram': '📷 Instagram',
        'TikTok': '🎵 TikTok', 'Офис застройщика': '🏢 Офис застройщика',
        'Наш офис': '🏢 Наш офис', 'Холодный контакт': '❄️ Холодный контакт'
    }
    
    for lid in lids:
        data.append({
            'ID': lid['id'],
            'Клиент': lid['client_name'],
            'Телефон': lid['phone'],
            'Тема разговора': lid['topic'] or '',
            'Комментарий': lid['comment'] or '',
            'Источник': source_map.get(lid['source'], lid['source']),
            'Ипотека': '✅ Да' if lid['mortgage'] else '❌ Нет',
            'Коробка': '✅ Да' if lid['box'] else '❌ Нет',
            'Автор': lid['author_name'],
            'Дата создания': lid['created_date']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Лиды', index=False)
        
        worksheet = writer.sheets['Лиды']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(output, download_name=f'lids_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', as_attachment=True)

@app.route('/lids')
@login_required
def lids_page():
    if session['category'] != 'Отдел продаж' and session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('lid.html')

# ================ HOUSES API ================

@app.route('/api/houses', methods=['GET'])
@login_required
def get_houses():
    conn = get_db()
    try:
        houses = conn.execute('''
            SELECT h.*, u.full_name as author_name 
            FROM houses h
            LEFT JOIN users u ON h.author_id = u.id
            ORDER BY h.id DESC
        ''').fetchall()
        return jsonify([dict(house) for house in houses])
    except Exception as e:
        print(f"Error get_houses: {e}")
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/houses', methods=['POST'])
@login_required
def add_house():
    try:
        title = request.form.get('title')
        construction_type = request.form.get('construction_type')
        district = request.form.get('district')
        address = request.form.get('address')
        area = float(request.form.get('area')) if request.form.get('area') else 0
        rooms = int(request.form.get('rooms')) if request.form.get('rooms') else 0
        windows = int(request.form.get('windows')) if request.form.get('windows') else 0
        floor = int(request.form.get('floor')) if request.form.get('floor') else 0
        total_floors = int(request.form.get('total_floors')) if request.form.get('total_floors') else 0
        price_per_m2 = float(request.form.get('price_per_m2')) if request.form.get('price_per_m2') else 0
        total_price = float(request.form.get('total_price')) if request.form.get('total_price') else 0
        developer = request.form.get('developer', '')
        contact_phone = request.form.get('contact_phone', '')
        has_tech_passport = request.form.get('has_tech_passport', 'нет')
        has_renovation_permit = request.form.get('has_renovation_permit', 'нет')
        
        # Обработка файлов
        files_data = []
        if 'files' in request.files:
            uploaded_files = request.files.getlist('files')
            for file in uploaded_files:
                if file and file.filename:
                    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                    ext = filename.split('.')[-1].lower()
                    
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        subfolder = 'houses/images'
                        file_type = 'image'
                    else:
                        subfolder = 'houses/docs'
                        file_type = 'document'
                    
                    os.makedirs(os.path.join('uploads', subfolder), exist_ok=True)
                    filepath = os.path.join('uploads', subfolder, filename)
                    file.save(filepath)
                    
                    files_data.append({
                        'name': file.filename,
                        'path': f'/{filepath}',
                        'type': file_type
                    })
        
        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO houses (
                title, construction_type, district, address, area, rooms, windows,
                floor, total_floors, price_per_m2, total_price, developer, contact_phone,
                has_tech_passport, has_renovation_permit, files, author_id, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, construction_type, district, address, area, rooms, windows,
            floor, total_floors, price_per_m2, total_price, developer, contact_phone,
            has_tech_passport, has_renovation_permit, json.dumps(files_data),
            session['user_id'], datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error add_house: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/houses/<int:house_id>', methods=['PUT'])
@login_required
def update_house(house_id):
    try:
        conn = get_db()
        house = conn.execute('SELECT * FROM houses WHERE id = ?', (house_id,)).fetchone()
        
        if not house:
            conn.close()
            return jsonify({'success': False, 'error': 'Объект не найден'}), 404
        
        if house['author_id'] != session['user_id'] and session['role'] != 'admin':
            conn.close()
            return jsonify({'success': False, 'error': 'Нет прав'}), 403
        
        title = request.form.get('title')
        construction_type = request.form.get('construction_type')
        district = request.form.get('district')
        address = request.form.get('address')
        area = float(request.form.get('area')) if request.form.get('area') else 0
        rooms = int(request.form.get('rooms')) if request.form.get('rooms') else 0
        windows = int(request.form.get('windows')) if request.form.get('windows') else 0
        floor = int(request.form.get('floor')) if request.form.get('floor') else 0
        total_floors = int(request.form.get('total_floors')) if request.form.get('total_floors') else 0
        price_per_m2 = float(request.form.get('price_per_m2')) if request.form.get('price_per_m2') else 0
        total_price = float(request.form.get('total_price')) if request.form.get('total_price') else 0
        developer = request.form.get('developer', '')
        contact_phone = request.form.get('contact_phone', '')
        has_tech_passport = request.form.get('has_tech_passport', 'нет')
        has_renovation_permit = request.form.get('has_renovation_permit', 'нет')
        
        # Получение существующих файлов
        existing_files = json.loads(house['files']) if house['files'] else []
        
        # Обработка новых файлов
        if 'files' in request.files:
            uploaded_files = request.files.getlist('files')
            for file in uploaded_files:
                if file and file.filename:
                    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                    ext = filename.split('.')[-1].lower()
                    
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        subfolder = 'houses/images'
                        file_type = 'image'
                    else:
                        subfolder = 'houses/docs'
                        file_type = 'document'
                    
                    os.makedirs(os.path.join('uploads', subfolder), exist_ok=True)
                    filepath = os.path.join('uploads', subfolder, filename)
                    file.save(filepath)
                    
                    existing_files.append({
                        'name': file.filename,
                        'path': f'/{filepath}',
                        'type': file_type
                    })
        
        conn.execute('''
            UPDATE houses SET
                title = ?, construction_type = ?, district = ?, address = ?,
                area = ?, rooms = ?, windows = ?, floor = ?, total_floors = ?,
                price_per_m2 = ?, total_price = ?, developer = ?, contact_phone = ?,
                has_tech_passport = ?, has_renovation_permit = ?, files = ?
            WHERE id = ?
        ''', (
            title, construction_type, district, address, area, rooms, windows,
            floor, total_floors, price_per_m2, total_price, developer, contact_phone,
            has_tech_passport, has_renovation_permit, json.dumps(existing_files), house_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_house: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/houses/<int:house_id>', methods=['DELETE'])
@login_required
def delete_house(house_id):
    try:
        conn = get_db()
        house = conn.execute('SELECT * FROM houses WHERE id = ?', (house_id,)).fetchone()
        
        if not house:
            conn.close()
            return jsonify({'success': False, 'error': 'Объект не найден'}), 404
        
        if house['author_id'] != session['user_id'] and session['role'] != 'admin':
            conn.close()
            return jsonify({'success': False, 'error': 'Нет прав'}), 403
        
        conn.execute('DELETE FROM houses WHERE id = ?', (house_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error delete_house: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/houses/<int:house_id>/files', methods=['DELETE'])
@login_required
def delete_house_file(house_id):
    try:
        data = request.json
        file_path = data.get('file_path')
        
        conn = get_db()
        house = conn.execute('SELECT * FROM houses WHERE id = ?', (house_id,)).fetchone()
        
        if not house:
            conn.close()
            return jsonify({'success': False, 'error': 'Объект не найден'}), 404
        
        files = json.loads(house['files']) if house['files'] else []
        files = [f for f in files if f['path'] != file_path]
        
        conn.execute('UPDATE houses SET files = ? WHERE id = ?', (json.dumps(files), house_id))
        conn.commit()
        conn.close()
        
        # Удаление физического файла
        if os.path.exists(file_path[1:]):
            os.remove(file_path[1:])
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error delete_house_file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/houses/export', methods=['GET'])
@login_required
def export_houses():
    try:
        search = request.args.get('search', '')
        construction_type = request.args.get('construction_type', 'all')
        district = request.args.get('district', 'all')
        area_min = request.args.get('area_min', '')
        area_max = request.args.get('area_max', '')
        rooms_min = request.args.get('rooms_min', '')
        rooms_max = request.args.get('rooms_max', '')
        floor_min = request.args.get('floor_min', '')
        floor_max = request.args.get('floor_max', '')
        price_per_m2_min = request.args.get('price_per_m2_min', '')
        price_per_m2_max = request.args.get('price_per_m2_max', '')
        price_min = request.args.get('price_min', '')
        price_max = request.args.get('price_max', '')
        
        conn = get_db()
        query = '''
            SELECT h.*, u.full_name as author_name 
            FROM houses h
            LEFT JOIN users u ON h.author_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if search:
            query += ' AND (h.title LIKE ? OR h.address LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        if construction_type != 'all':
            query += ' AND h.construction_type = ?'
            params.append(construction_type)
        if district != 'all':
            query += ' AND h.district = ?'
            params.append(district)
        if area_min:
            query += ' AND h.area >= ?'
            params.append(float(area_min))
        if area_max:
            query += ' AND h.area <= ?'
            params.append(float(area_max))
        if rooms_min:
            query += ' AND h.rooms >= ?'
            params.append(int(rooms_min))
        if rooms_max:
            query += ' AND h.rooms <= ?'
            params.append(int(rooms_max))
        if floor_min:
            query += ' AND h.floor >= ?'
            params.append(int(floor_min))
        if floor_max:
            query += ' AND h.floor <= ?'
            params.append(int(floor_max))
        if price_per_m2_min:
            query += ' AND h.price_per_m2 >= ?'
            params.append(float(price_per_m2_min))
        if price_per_m2_max:
            query += ' AND h.price_per_m2 <= ?'
            params.append(float(price_per_m2_max))
        if price_min:
            query += ' AND h.total_price >= ?'
            params.append(float(price_min))
        if price_max:
            query += ' AND h.total_price <= ?'
            params.append(float(price_max))
        
        query += ' ORDER BY h.id DESC'
        houses = conn.execute(query, params).fetchall()
        conn.close()
        
        data = []
        district_map = {
            'н.Сино': 'Сино', 'н.Шоҳмансур': 'Шоҳмансур', 'н.Фирдавси': 'Фирдавси', 'н.Сомони': 'Сомони'
        }
        
        for house in houses:
            data.append({
                'ID': house['id'],
                'Название объекта': house['title'],
                'Тип строительства': house['construction_type'],
                'Район': district_map.get(house['district'], house['district']),
                'Адрес': house['address'],
                'Площадь (м²)': house['area'],
                'Количество комнат': house['rooms'],
                'Количество окон': house['windows'],
                'Этаж': house['floor'],
                'Этажность здания': house['total_floors'],
                'Цена за м² (₽)': house['price_per_m2'],
                'Общая цена (₽)': house['total_price'],
                'Застройщик': house['developer'] or '',
                'Контакт': house['contact_phone'] or '',
                'Техпаспорт': house['has_tech_passport'],
                'Разрешение на ремонт': house['has_renovation_permit'],
                'Автор': house['author_name'],
                'Дата создания': house['created_date']
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Объекты недвижимости', index=False)
            
            worksheet = writer.sheets['Объекты недвижимости']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return send_file(
            output, 
            download_name=f'houses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"Error export_houses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/houses')
@login_required
def houses_page():
    return render_template('houses.html')

# -------------------- COMPANY PHONES API --------------------
def migrate_sim_phone_tables():
    """Add missing columns to existing tables"""
    conn = get_db()
    try:
        # Check sim_cards table columns
        cursor = conn.execute("PRAGMA table_info(sim_cards)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'phone_id' not in columns:
            conn.execute('ALTER TABLE sim_cards ADD COLUMN phone_id INTEGER')
            print("✅ Added 'phone_id' to sim_cards")
        
        if 'description' not in columns:
            conn.execute('ALTER TABLE sim_cards ADD COLUMN description TEXT')
            print("✅ Added 'description' to sim_cards")
        
        if 'operator' not in columns and 'operator' not in columns:
            conn.execute('ALTER TABLE sim_cards ADD COLUMN operator TEXT DEFAULT "Tcell"')
            print("✅ Added 'operator' to sim_cards")
        
        # Check company_phones table
        cursor = conn.execute("PRAGMA table_info(company_phones)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'description' not in columns:
            conn.execute('ALTER TABLE company_phones ADD COLUMN description TEXT')
            print("✅ Added 'description' to company_phones")
        
        if 'created_date' not in columns:
            conn.execute('ALTER TABLE company_phones ADD COLUMN created_date TEXT')
            print("✅ Added 'created_date' to company_phones")
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()


# ================ COMPANY PHONES API ================

@app.route('/api/company-phones', methods=['GET'])
@login_required
def get_company_phones():
    """Get all company phones"""
    conn = get_db()
    try:
        phones = conn.execute('''
            SELECT p.*, u.full_name as employee_name
            FROM company_phones p
            LEFT JOIN users u ON p.assigned_to = u.id
            ORDER BY p.id DESC
        ''').fetchall()
        return jsonify([dict(phone) for phone in phones])
    except Exception as e:
        print(f"Error get_company_phones: {e}")
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/company-phones', methods=['POST'])
@login_required
@admin_required
def add_company_phone():
    """Add new company phone"""
    data = request.json
    conn = get_db()
    try:
        # Generate auto phone ID
        count = conn.execute('SELECT COUNT(*) as cnt FROM company_phones').fetchone()
        phone_id = f"PH-{count['cnt'] + 1:04d}"
        
        cursor = conn.execute('''
            INSERT INTO company_phones (model, phone_id, assigned_to, description, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('model'),
            phone_id,
            data.get('assigned_to') if data.get('assigned_to') else None,
            data.get('description', ''),
            'used' if data.get('assigned_to') else 'free',
            datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid, 'phone_id': phone_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/company-phones/<int:phone_id>', methods=['PUT'])
@login_required
@admin_required
def update_company_phone(phone_id):
    """Update company phone"""
    data = request.json
    conn = get_db()
    try:
        status = 'used' if data.get('assigned_to') else 'free'
        conn.execute('''
            UPDATE company_phones SET 
                model = ?, assigned_to = ?, description = ?, status = ?
            WHERE id = ?
        ''', (data.get('model'), data.get('assigned_to'), data.get('description', ''), status, phone_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/company-phones/<int:phone_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_company_phone(phone_id):
    """Delete company phone"""
    conn = get_db()
    try:
        # Unlink SIM cards
        conn.execute('UPDATE sim_cards SET phone_id = NULL WHERE phone_id = ?', (phone_id,))
        conn.execute('DELETE FROM company_phones WHERE id = ?', (phone_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# ================ SIM CARDS API ================

@app.route('/api/sim-cards', methods=['GET'])
@login_required
def get_sim_cards():
    """Get all SIM cards with details"""
    conn = get_db()
    try:
        sim_cards = conn.execute('''
            SELECT s.*, 
                   u.full_name as employee_name,
                   p.model as phone_model,
                   p.phone_id as phone_code
            FROM sim_cards s
            LEFT JOIN users u ON s.assigned_to = u.id
            LEFT JOIN company_phones p ON s.phone_id = p.id
            ORDER BY s.id DESC
        ''').fetchall()
        return jsonify([dict(sim) for sim in sim_cards])
    except Exception as e:
        print(f"Error get_sim_cards: {e}")
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/sim-cards', methods=['POST'])
@login_required
@admin_required
def add_sim_card():
    """Add new SIM card"""
    data = request.json
    conn = get_db()
    try:
        # Check if phone number already exists
        existing = conn.execute('SELECT id FROM sim_cards WHERE phone_number = ?', (data['phone_number'],)).fetchone()
        if existing:
            return jsonify({'success': False, 'error': 'Ин рақами телефон аллакай мавҷуд аст!'}), 400
        
        cursor = conn.execute('''
            INSERT INTO sim_cards (phone_number, operator, assigned_to, phone_id, description, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['phone_number'],
            data['operator'],
            data.get('assigned_to') if data.get('assigned_to') else None,
            data.get('phone_id') if data.get('phone_id') else None,
            data.get('description', ''),
            'active',
            datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error add_sim_card: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/sim-cards/<int:sim_id>', methods=['PUT'])
@login_required
@admin_required
def update_sim_card(sim_id):
    """Update SIM card"""
    data = request.json
    conn = get_db()
    try:
        # Check if phone number already exists (excluding current card)
        if data.get('phone_number'):
            existing = conn.execute('SELECT id FROM sim_cards WHERE phone_number = ? AND id != ?', 
                                    (data['phone_number'], sim_id)).fetchone()
            if existing:
                return jsonify({'success': False, 'error': 'Ин рақами телефон аллакай мавҷуд аст!'}), 400
        
        conn.execute('''
            UPDATE sim_cards SET 
                phone_number = COALESCE(?, phone_number),
                operator = COALESCE(?, operator),
                assigned_to = ?,
                phone_id = ?,
                description = COALESCE(?, description)
            WHERE id = ?
        ''', (
            data.get('phone_number'),
            data.get('operator'),
            data.get('assigned_to') if data.get('assigned_to') in [None, ''] else data.get('assigned_to'),
            data.get('phone_id') if data.get('phone_id') else None,
            data.get('description'),
            sim_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_sim_card: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/sim-cards/<int:sim_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_sim_card(sim_id):
    """Delete SIM card"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM sim_cards WHERE id = ?', (sim_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# ================ TARIFFS API ================

@app.route('/api/sim-tariffs', methods=['GET'])
@login_required
def get_sim_tariffs():
    """Get all tariffs"""
    conn = get_db()
    try:
        tariffs = conn.execute('''
            SELECT t.*, s.phone_number, s.operator
            FROM sim_tariffs t
            JOIN sim_cards s ON t.sim_id = s.id
            ORDER BY t.id DESC
        ''').fetchall()
        
        # Auto-deactivate expired tariffs
        now = datetime.now().isoformat()
        for tariff in tariffs:
            if tariff['status'] == 'active' and tariff['end_date'] and tariff['end_date'] < now:
                conn.execute('UPDATE sim_tariffs SET status = ? WHERE id = ?', ('inactive', tariff['id']))
        conn.commit()
        
        # Refresh data
        tariffs = conn.execute('''
            SELECT t.*, s.phone_number, s.operator
            FROM sim_tariffs t
            JOIN sim_cards s ON t.sim_id = s.id
            ORDER BY t.id DESC
        ''').fetchall()
        
        return jsonify([dict(t) for t in tariffs])
    except Exception as e:
        print(f"Error get_sim_tariffs: {e}")
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/sim-tariffs', methods=['POST'])
@login_required
@admin_required
def add_sim_tariff_enhanced():
    """Add new tariff, auto-activate it, and create payment record"""
    data = request.json
    conn = get_db()
    try:
        # Validate required fields
        if not data.get('start_date') or not data.get('end_date'):
            return jsonify({'success': False, 'error': 'Санаи оғоз ва анҷом ҳатмист!'}), 400
        
        # Deactivate all active tariffs for this SIM
        conn.execute('UPDATE sim_tariffs SET status = ? WHERE sim_id = ? AND status = ?',
                    ('inactive', data['sim_id'], 'active'))
        
        # Create new tariff
        cursor = conn.execute('''
            INSERT INTO sim_tariffs (sim_id, minutes, gb, sms, cost, start_date, end_date, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['sim_id'],
            data.get('minutes', 0),
            data.get('gb', 0),
            data.get('sms', 0),
            data.get('cost', 0),
            data.get('start_date'),
            data.get('end_date'),
            'active',
            datetime.now().isoformat()
        ))
        tariff_id = cursor.lastrowid
        
        # Create payment record for this tariff
        payment_amount = data.get('cost', 0)
        conn.execute('''
            INSERT INTO tariff_payments (sim_id, tariff_id, amount, payment_date, start_date, end_date, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['sim_id'],
            tariff_id,
            payment_amount,
            datetime.now().strftime('%Y-%m-%d'),
            data.get('start_date'),
            data.get('end_date'),
            'paid',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        return jsonify({'success': True, 'id': tariff_id})
    except Exception as e:
        print(f"Error add_sim_tariff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


@app.route('/api/sim-tariffs/<int:tariff_id>', methods=['PUT'])
@login_required
@admin_required
def update_tariff_enhanced(tariff_id):
    """Update tariff and recreate payment record"""
    data = request.json
    
    # If only status update
    if 'status' in data and len(data) == 1:
        status = data.get('status')
        if status not in ['active', 'inactive']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        conn = get_db()
        try:
            tariff = conn.execute('SELECT * FROM sim_tariffs WHERE id = ?', (tariff_id,)).fetchone()
            if not tariff:
                return jsonify({'success': False, 'error': 'Tariff not found'}), 404
            
            if status == 'active':
                conn.execute('UPDATE sim_tariffs SET status = ? WHERE sim_id = ? AND status = ?',
                            ('inactive', tariff['sim_id'], 'active'))
            
            conn.execute('UPDATE sim_tariffs SET status = ? WHERE id = ?', (status, tariff_id))
            conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        finally:
            conn.close()
    
    # Full update of tariff
    conn = get_db()
    try:
        # Get current tariff
        tariff = conn.execute('SELECT * FROM sim_tariffs WHERE id = ?', (tariff_id,)).fetchone()
        if not tariff:
            return jsonify({'success': False, 'error': 'Tariff not found'}), 404
        
        # Validate dates
        if not data.get('start_date') or not data.get('end_date'):
            return jsonify({'success': False, 'error': 'Санаи оғоз ва анҷом ҳатмист!'}), 400
        
        # Deactivate all active tariffs for this SIM (except this one if activating)
        if data.get('status') == 'active' or not data.get('status'):
            conn.execute('UPDATE sim_tariffs SET status = ? WHERE sim_id = ? AND status = ? AND id != ?',
                        ('inactive', tariff['sim_id'], 'active', tariff_id))
        
        # Update tariff
        conn.execute('''
            UPDATE sim_tariffs SET 
                minutes = ?, gb = ?, sms = ?, cost = ?, 
                start_date = ?, end_date = ?, status = ?
            WHERE id = ?
        ''', (
            data.get('minutes', 0),
            data.get('gb', 0),
            data.get('sms', 0),
            data.get('cost', 0),
            data.get('start_date'),
            data.get('end_date'),
            data.get('status', 'active'),
            tariff_id
        ))
        
        # Update or create payment record
        existing_payment = conn.execute('SELECT id FROM tariff_payments WHERE tariff_id = ?', (tariff_id,)).fetchone()
        if existing_payment:
            conn.execute('''
                UPDATE tariff_payments SET 
                    amount = ?, start_date = ?, end_date = ?, payment_date = ?
                WHERE tariff_id = ?
            ''', (
                data.get('cost', 0),
                data.get('start_date'),
                data.get('end_date'),
                datetime.now().strftime('%Y-%m-%d'),
                tariff_id
            ))
        else:
            conn.execute('''
                INSERT INTO tariff_payments (sim_id, tariff_id, amount, payment_date, start_date, end_date, status, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tariff['sim_id'],
                tariff_id,
                data.get('cost', 0),
                datetime.now().strftime('%Y-%m-%d'),
                data.get('start_date'),
                data.get('end_date'),
                'paid',
                datetime.now().isoformat()
            ))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_tariff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


# ================ REQUESTS KANBAN API (НАВ) ================

# Таблицаи колонкаҳо барои заявкаҳо (агар набошад)
def init_requests_columns_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            color TEXT DEFAULT '#3b82f6',
            order_index INTEGER DEFAULT 0,
            created_date TEXT
        )
    ''')
    # Илова кардани колонкаҳои стандартӣ агар холӣ бошад
    count = cursor.execute('SELECT COUNT(*) as cnt FROM requests_columns').fetchone()
    if count['cnt'] == 0:
        default_columns = ['Нав', 'Дар кор', 'Анҷом', 'Бекор']
        for i, col in enumerate(default_columns):
            cursor.execute('''
                INSERT INTO requests_columns (title, color, order_index, created_date)
                VALUES (?, ?, ?, ?)
            ''', (col, '#3b82f6' if i==0 else '#f59e0b' if i==1 else '#22c55e' if i==2 else '#ef4444', i, datetime.now().isoformat()))
        conn.commit()
    conn.close()

# Функсия барои табдил додани status ба колонка
def get_column_by_status(status):
    status_map = {'new': 'Нав', 'progress': 'Дар кор', 'done': 'Анҷом', 'cancel': 'Бекор'}
    return status_map.get(status, 'Нав')

@app.route('/api/requests-columns', methods=['GET'])
@login_required
def get_requests_columns():
    """Гирифтани ҳамаи колонкаҳо барои заявкаҳо"""
    conn = get_db()
    columns = conn.execute('SELECT * FROM requests_columns ORDER BY order_index ASC').fetchall()
    conn.close()
    return jsonify([dict(col) for col in columns])



@app.route('/api/requests/all', methods=['GET'])
@login_required
def get_all_requests_kanban():
    """Гирифтани ҳамаи заявкаҳо барои Kanban (бидуни маҳдудият)"""
    conn = get_db()
    query = '''
        SELECT r.*, u.full_name as author_name, u2.full_name as executor_name
        FROM requests r
        LEFT JOIN users u ON r.author_id = u.id
        LEFT JOIN users u2 ON r.executor_id = u2.id
        ORDER BY r.id DESC
    '''
    requests = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(req) for req in requests])

@app.route('/api/requests/new', methods=['POST'])
@login_required
def create_request_kanban():
    """Эҷоди заявкаи нав (бидуни менеджер ва smm)"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO requests (
                property_type, address, area, rooms, windows, floor, total_floors,
                total_price, price_per_m2, phone, client_name, comment,
                author_id, executor_id, files, status, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['property_type'], data['address'], data['area'], data['rooms'],
            data['windows'], data['floor'], data['total_floors'],
            data['total_price'], data['price_per_m2'], data['phone'], data['client_name'],
            data.get('comment', ''), session['user_id'], data['executor_id'],
            json.dumps(data.get('files', [])), 'new', datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error create_request_kanban: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests/<int:request_id>', methods=['PUT'])
@login_required
def update_request_kanban(request_id):
    """Таҳрири заявка (бо ҳама майдонҳо)"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE requests SET
                property_type = ?, address = ?, area = ?, rooms = ?, windows = ?,
                floor = ?, total_floors = ?, total_price = ?, price_per_m2 = ?,
                phone = ?, client_name = ?, comment = ?, executor_id = ?, files = ?
            WHERE id = ?
        ''', (
            data['property_type'], data['address'], data['area'], data['rooms'],
            data['windows'], data['floor'], data['total_floors'],
            data['total_price'], data['price_per_m2'], data['phone'], data['client_name'],
            data.get('comment', ''), data['executor_id'], json.dumps(data.get('files', [])), request_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_request_kanban: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_request_kanban(request_id):
    """Нест кардани заявка"""
    conn = get_db()
    conn.execute('DELETE FROM requests WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})



@app.route('/api/sim-tariffs/<int:tariff_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_tariff_complete_enhanced(tariff_id):
    """Delete tariff and all related payment history"""
    conn = get_db()
    try:
        # Check if tariff exists
        tariff = conn.execute('SELECT * FROM sim_tariffs WHERE id = ?', (tariff_id,)).fetchone()
        if not tariff:
            return jsonify({'success': False, 'error': 'Tariff not found'}), 404
        
        # Delete related payments
        conn.execute('DELETE FROM tariff_payments WHERE tariff_id = ?', (tariff_id,))
        # Delete tariff
        conn.execute('DELETE FROM sim_tariffs WHERE id = ?', (tariff_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error delete_tariff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()


# ================ PAYMENTS HISTORY API ================

@app.route('/api/tariff-payments', methods=['GET'])
@login_required
def get_tariff_payments():
    """Get payment history"""
    conn = get_db()
    try:
        payments = conn.execute('''
            SELECT tp.*, s.phone_number, s.operator
            FROM tariff_payments tp
            JOIN sim_cards s ON tp.sim_id = s.id
            ORDER BY tp.id DESC
        ''').fetchall()
        return jsonify([dict(p) for p in payments])
    except Exception as e:
        print(f"Error get_tariff_payments: {e}")
        return jsonify([])
    finally:
        conn.close()

@app.route('/api/tariff-payments/<int:payment_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_payment(payment_id):
    """Delete a single payment record"""
    conn = get_db()
    try:
        payment = conn.execute('SELECT * FROM tariff_payments WHERE id = ?', (payment_id,)).fetchone()
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        conn.execute('DELETE FROM tariff_payments WHERE id = ?', (payment_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# ================ ENHANCED EXPORT FOR SIM/PHONES ================

@app.route('/api/sim-phones/export/excel', methods=['GET'])
@login_required
@admin_required
def export_sim_phones_excel_enhanced():
    """Export data to Excel with separate sheets based on type parameter"""
    export_type = request.args.get('type', 'all')
    conn = get_db()
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Export SIM Cards
        if export_type in ['all', 'sims']:
            sim_cards = conn.execute('''
                SELECT s.*, u.full_name as employee_name, p.model as phone_model, p.phone_id as phone_code
                FROM sim_cards s
                LEFT JOIN users u ON s.assigned_to = u.id
                LEFT JOIN company_phones p ON s.phone_id = p.id
                ORDER BY s.id DESC
            ''').fetchall()
            
            sim_data = [{
                'ID': s['id'],
                'Номер телефона': s['phone_number'],
                'Оператор': s['operator'],
                'Сотрудник': s['employee_name'] or 'Свободный',
                'Телефон': s['phone_model'] or 'Свободный',
                'Код телефона': s['phone_code'] or '',
                'Описание': s['description'] or '',
                'Дата добавления': s['created_date']
            } for s in sim_cards]
            df_sim = pd.DataFrame(sim_data) if sim_data else pd.DataFrame()
            if not df_sim.empty:
                df_sim.to_excel(writer, sheet_name='SIM-карты', index=False)
        
        # Export Company Phones
        if export_type in ['all', 'phones']:
            phones = conn.execute('''
                SELECT p.*, u.full_name as employee_name
                FROM company_phones p
                LEFT JOIN users u ON p.assigned_to = u.id
                ORDER BY p.id DESC
            ''').fetchall()
            
            phones_data = [{
                'ID': p['id'],
                'Модель': p['model'],
                'Код телефона': p['phone_id'],
                'Сотрудник': p['employee_name'] or 'Свободный',
                'Описание': p['description'] or '',
                'Статус': 'Используется' if p['status'] == 'used' else 'Свободен',
                'Дата добавления': p['created_date']
            } for p in phones]
            df_phones = pd.DataFrame(phones_data) if phones_data else pd.DataFrame()
            if not df_phones.empty:
                df_phones.to_excel(writer, sheet_name='Телефоны', index=False)
        
        # Export Tariffs
        if export_type in ['all', 'tariffs']:
            tariffs = conn.execute('''
                SELECT t.*, s.phone_number, s.operator
                FROM sim_tariffs t
                JOIN sim_cards s ON t.sim_id = s.id
                ORDER BY t.id DESC
            ''').fetchall()
            
            tariff_data = [{
                'ID': t['id'],
                'Номер SIM': t['phone_number'],
                'Оператор': t['operator'],
                'Минуты': t['minutes'],
                'ГБ': t['gb'],
                'SMS': t['sms'],
                'Нарх (сомони)': t['cost'],
                'Дата начала': t['start_date'],
                'Дата окончания': t['end_date'],
                'Статус': 'Активен' if t['status'] == 'active' else 'Неактивен'
            } for t in tariffs]
            df_tariffs = pd.DataFrame(tariff_data) if tariff_data else pd.DataFrame()
            if not df_tariffs.empty:
                df_tariffs.to_excel(writer, sheet_name='Тарифы', index=False)
        
        # Export Payments
        if export_type in ['all', 'payments']:
            payments = conn.execute('''
                SELECT tp.*, s.phone_number, s.operator
                FROM tariff_payments tp
                JOIN sim_cards s ON tp.sim_id = s.id
                ORDER BY tp.id DESC
            ''').fetchall()
            
            payment_data = [{
                'ID': p['id'],
                'Номер SIM': p['phone_number'],
                'Оператор': p['operator'],
                'Сумма (сомони)': p['amount'],
                'Дата оплаты': p['payment_date'],
                'Период с': p['start_date'],
                'Период до': p['end_date'],
                'Дата создания': p['created_date']
            } for p in payments]
            df_payments = pd.DataFrame(payment_data) if payment_data else pd.DataFrame()
            if not df_payments.empty:
                df_payments.to_excel(writer, sheet_name='История оплат', index=False)
        
        # Auto-width columns for all sheets
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for column in worksheet.columns:
                max_length = 0
                col_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
    
    conn.close()
    output.seek(0)
    return send_file(output, 
                    download_name=f'sim_phones_export_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    as_attachment=True,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# -------------------- STATISTICS API --------------------
@app.route('/api/sim-phones/stats', methods=['GET'])
@login_required
def get_sim_phones_stats():
    """Get statistics"""
    conn = get_db()
    try:
        total_phones = conn.execute('SELECT COUNT(*) as count FROM company_phones').fetchone()['count']
        total_sims = conn.execute('SELECT COUNT(*) as count FROM sim_cards').fetchone()['count']
        active_tariffs = conn.execute("SELECT COUNT(*) as count FROM sim_tariffs WHERE status = 'active'").fetchone()['count']
        
        # Total monthly cost
        current_month = datetime.now().strftime('%Y-%m')
        monthly_cost = conn.execute('''
            SELECT COALESCE(SUM(cost), 0) as total 
            FROM sim_tariffs 
            WHERE status = 'active' 
            AND strftime('%Y-%m', start_date) = ?
        ''', (current_month,)).fetchone()['total']
        
        return jsonify({
            'total_phones': total_phones,
            'total_sims': total_sims,
            'active_tariffs': active_tariffs,
            'monthly_cost': monthly_cost
        })
    except Exception as e:
        print(f"Error get_sim_phones_stats: {e}")
        return jsonify({'total_phones': 0, 'total_sims': 0, 'active_tariffs': 0, 'monthly_cost': 0})
    finally:
        conn.close()

# -------------------- NOTIFICATIONS --------------------
def send_tariff_notification(sim_id, end_date):
    """Send notification to admin about tariff expiration"""
    try:
        conn = sqlite3.connect('real_estate_crm.db')
        sim = conn.execute('SELECT * FROM sim_cards WHERE id = ?', (sim_id,)).fetchone()
        
        if sim:
            # Create notification for admin (if you have notifications table)
            message = f"Тариф SIM-карты {sim['phone_number']} истекает {end_date}. Необходимо продлить."
            print(f"NOTIFICATION: {message}")
            
        conn.close()
    except Exception as e:
        print(f"Error send_tariff_notification: {e}")

@app.route('/sim-cards')
@login_required
@admin_required
def sim_cards_page():
    return render_template('sim_card.html')


@app.route('/api/check-auth')
@login_required
def check_auth():
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    login = data.get('login')
    password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE login = ? AND password = ?', (login, password)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['role'] = user['role']
        session['category'] = user['category']
        session['photo'] = user['photo']
        return jsonify({'success': True, 'role': user['role']})
    return jsonify({'success': False, 'error': 'Неверный логин или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# ================ USERS API ================
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    conn = get_db()
    if session['role'] == 'admin':
        users = conn.execute('SELECT * FROM users').fetchall()
    else:
        users = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/users/list', methods=['GET'])
@login_required
def get_users_list():
    conn = get_db()
    users = conn.execute('SELECT id, full_name, category, photo FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def add_user():
    if request.is_json:
        data = request.json
        password = hashlib.sha256(data['password'].encode()).hexdigest()
        photo_path = data.get('photo', '')
    else:
        data = request.form
        password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
        photo_path = ''
        if 'photo_file' in request.files:
            file = request.files['photo_file']
            if file and file.filename:
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join('uploads/photos', filename)
                file.save(filepath)
                photo_path = f'/uploads/photos/{filename}'
    
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO users (full_name, age, personal_phones, work_phones, login, password, photo, category, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['full_name'], int(data['age']), 
            json.dumps(data.get('personal_phones', '').split(',') if isinstance(data.get('personal_phones'), str) else data.get('personal_phones', [])),
            json.dumps(data.get('work_phones', '').split(',') if isinstance(data.get('work_phones'), str) else data.get('work_phones', [])),
            data['login'], password, photo_path, data['category'], 'employee', datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Сотрудник добавлен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    conn = get_db()
    try:
        if request.is_json:
            data = request.json
            if 'full_name' in data:
                conn.execute('UPDATE users SET full_name = ? WHERE id = ?', (data['full_name'], user_id))
            if 'age' in data:
                conn.execute('UPDATE users SET age = ? WHERE id = ?', (int(data['age']), user_id))
            if 'personal_phones' in data:
                conn.execute('UPDATE users SET personal_phones = ? WHERE id = ?', (json.dumps(data['personal_phones']), user_id))
            if 'work_phones' in data:
                conn.execute('UPDATE users SET work_phones = ? WHERE id = ?', (json.dumps(data['work_phones']), user_id))
            if 'category' in data:
                conn.execute('UPDATE users SET category = ? WHERE id = ?', (data['category'], user_id))
            if 'password' in data and data['password']:
                password = hashlib.sha256(data['password'].encode()).hexdigest()
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (password, user_id))
        else:
            data = request.form
            if 'full_name' in data:
                conn.execute('UPDATE users SET full_name = ? WHERE id = ?', (data['full_name'], user_id))
            if 'age' in data:
                conn.execute('UPDATE users SET age = ? WHERE id = ?', (int(data['age']), user_id))
            if 'personal_phones' in data:
                conn.execute('UPDATE users SET personal_phones = ? WHERE id = ?', (json.dumps(data['personal_phones'].split(',')), user_id))
            if 'work_phones' in data:
                conn.execute('UPDATE users SET work_phones = ? WHERE id = ?', (json.dumps(data['work_phones'].split(',')), user_id))
            if 'category' in data:
                conn.execute('UPDATE users SET category = ? WHERE id = ?', (data['category'], user_id))
            if 'password' in data and data['password']:
                password = hashlib.sha256(data['password'].encode()).hexdigest()
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (password, user_id))
            
            if 'photo_file' in request.files:
                file = request.files['photo_file']
                if file and file.filename:
                    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                    filepath = os.path.join('uploads/photos', filename)
                    file.save(filepath)
                    conn.execute('UPDATE users SET photo = ? WHERE id = ?', (f'/uploads/photos/{filename}', user_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Нельзя удалить себя'}), 400
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ================ TASKS API ================
@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    status = request.args.get('status', 'all')
    conn = get_db()
    
    query = '''
        SELECT t.*, u.full_name as author_name, u2.full_name as executor_name
        FROM tasks t
        LEFT JOIN users u ON t.author_id = u.id
        LEFT JOIN users u2 ON t.executor_id = u2.id
        WHERE 1=1
    '''
    params = []
    
    if status != 'all':
        query += ' AND t.status = ?'
        params.append(status)
    
    if session['role'] != 'admin':
        query += ' AND (t.author_id = ? OR t.executor_id = ?)'
        params.extend([session['user_id'], session['user_id']])
    
    query += ' ORDER BY t.id DESC'
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    photo_path = ''
    
    if request.is_json:
        data = request.json
        photo_path = data.get('photo', '')
    else:
        data = request.form
        if 'photo_file' in request.files:
            file = request.files['photo_file']
            if file and file.filename:
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join('uploads/photos', filename)
                file.save(filepath)
                photo_path = f'/uploads/photos/{filename}'
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO tasks (title, description, author_id, executor_id, photo, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], data.get('description', ''), session['user_id'],
            int(data['executor_id']), photo_path, 'new', datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    conn = get_db()
    try:
        if request.is_json:
            data = request.json
            if 'status' in data:
                conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (data['status'], task_id))
            if 'title' in data:
                conn.execute('UPDATE tasks SET title = ? WHERE id = ?', (data['title'], task_id))
            if 'description' in data:
                conn.execute('UPDATE tasks SET description = ? WHERE id = ?', (data['description'], task_id))
            if 'executor_id' in data:
                conn.execute('UPDATE tasks SET executor_id = ? WHERE id = ?', (int(data['executor_id']), task_id))
        else:
            data = request.form
            if 'status' in data:
                conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (data['status'], task_id))
            if 'title' in data:
                conn.execute('UPDATE tasks SET title = ? WHERE id = ?', (data['title'], task_id))
            if 'description' in data:
                conn.execute('UPDATE tasks SET description = ? WHERE id = ?', (data['description'], task_id))
            if 'executor_id' in data:
                conn.execute('UPDATE tasks SET executor_id = ? WHERE id = ?', (int(data['executor_id']), task_id))
            
            if 'photo_file' in request.files:
                file = request.files['photo_file']
                if file and file.filename:
                    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                    filepath = os.path.join('uploads/photos', filename)
                    file.save(filepath)
                    conn.execute('UPDATE tasks SET photo = ? WHERE id = ?', (f'/uploads/photos/{filename}', task_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ================ REQUESTS API ================

@app.route('/api/requests', methods=['GET'])
@login_required
def get_requests():
    """Гирифтани ҳамаи заявкаҳо - ҲАМА кормандон ҳамаро мебинанд"""
    status = request.args.get('status', 'all')
    date_filter = request.args.get('date_filter', 'all')
    user_filter = request.args.get('user_filter', 'all')
    
    conn = get_db()
    query = '''
        SELECT r.*, u.full_name as author_name, u2.full_name as executor_name
        FROM requests r
        LEFT JOIN users u ON r.author_id = u.id
        LEFT JOIN users u2 ON r.executor_id = u2.id
        WHERE 1=1
    '''
    params = []
    
    # ========== ИСЛОҲ: ҲАМА кормандон ҳамаи заявкаҳоро мебинанд ==========
    # Қисмати зерин НЕСТ карда мешавад, то ҳама кормандон ҳамаро бубинанд
    # if session['role'] != 'admin':
    #     query += ' AND (r.author_id = ? OR r.executor_id = ?)'
    #     params.extend([session['user_id'], session['user_id']])
    
    # Фильтр по статусу
    if status != 'all':
        query += ' AND r.status = ?'
        params.append(status)
    
    # Фильтр по исполнителю (танҳо барои админ)
    if user_filter != 'all' and session['role'] == 'admin' and user_filter.isdigit():
        query += ' AND r.executor_id = ?'
        params.append(int(user_filter))
    
    # Фильтр по дате
    if date_filter != 'all':
        now = datetime.now()
        if date_filter == 'day':
            start_date = (now - timedelta(days=1)).isoformat()
        elif date_filter == 'week':
            start_date = (now - timedelta(weeks=1)).isoformat()
        elif date_filter == 'month':
            start_date = (now - timedelta(days=30)).isoformat()
        elif date_filter == 'year':
            start_date = (now - timedelta(days=365)).isoformat()
        else:
            start_date = None
        
        if start_date:
            query += ' AND r.created_date >= ?'
            params.append(start_date)
    
    query += ' ORDER BY r.id DESC'
    requests = conn.execute(query, params).fetchall()
    
    # Статистика барои ҳамаи заявкаҳо
    total = conn.execute('SELECT COUNT(*) as count FROM requests').fetchone()
    completed = conn.execute('SELECT COUNT(*) as count FROM requests WHERE status = "done"').fetchone()
    
    conn.close()
    return jsonify({
        'requests': [dict(req) for req in requests],
        'stats': {'total': total['count'], 'completed': completed['count']}
    })

@app.route('/api/requests', methods=['POST'])
@login_required
def add_request():
    """Илова кардани заявкаи нав"""
    data = request.json
    
    # Валидатсия
    required_fields = ['property_type', 'address', 'area', 'rooms', 'windows', 
                       'floor', 'total_floors', 'total_price', 'price_per_m2', 
                       'phone', 'client_name', 'executor_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Поле {field} обязательно'}), 400
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO requests (
                property_type, address, area, rooms, windows, floor, total_floors,
                documents, total_price, price_per_m2, phone, client_name, manager,
                smm, comment, author_id, executor_id, files, status, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['property_type'], data['address'], data['area'], data['rooms'],
            data['windows'], data['floor'], data['total_floors'], data.get('documents', ''),
            data['total_price'], data['price_per_m2'], data['phone'], data['client_name'],
            data.get('manager', ''), data.get('smm', ''), data.get('comment', ''),
            session['user_id'], data['executor_id'], json.dumps(data.get('files', [])),
            'new', datetime.now().isoformat()
        ))
        conn.commit()
        
        # Фиристодани уведомление барои исполнитель
        try:
            if data['executor_id'] != session['user_id']:
                send_request_notification(cursor.lastrowid, data['executor_id'], data['client_name'])
        except:
            pass
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error add_request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests/<int:request_id>', methods=['PUT'])
@login_required
def update_request(request_id):
    """Таҳрир кардани заявка (танҳо барои автор ё админ)"""
    data = request.json
    conn = get_db()
    
    # Санҷиши вуҷуди заявка
    request_item = conn.execute('SELECT * FROM requests WHERE id = ?', (request_id,)).fetchone()
    if not request_item:
        conn.close()
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    
    # Санҷиши ҳуқуқ: танҳо автор ё админ метавонад таҳрир кунад
    if request_item['author_id'] != session['user_id'] and session['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'error': 'Нет прав для редактирования'}), 403
    
    try:
        allowed_fields = ['status', 'property_type', 'address', 'area', 'rooms', 'windows', 
                          'floor', 'total_floors', 'documents', 'total_price', 'price_per_m2',
                          'phone', 'client_name', 'manager', 'smm', 'comment', 'executor_id']
        
        for key, value in data.items():
            if key in allowed_fields:
                conn.execute(f'UPDATE requests SET {key} = ? WHERE id = ?', (value, request_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_request(request_id):
    """Нест кардани заявка (танҳо барои автор ё админ)"""
    conn = get_db()
    
    # Санҷиши вуҷуди заявка
    request_item = conn.execute('SELECT * FROM requests WHERE id = ?', (request_id,)).fetchone()
    if not request_item:
        conn.close()
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    
    # Санҷиши ҳуқуқ: танҳо автор ё админ метавонад нест кунад
    if request_item['author_id'] != session['user_id'] and session['role'] != 'admin':
        conn.close()
        return jsonify({'success': False, 'error': 'Нет прав для удаления'}), 403
    
    conn.execute('DELETE FROM requests WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/requests/export', methods=['GET'])
@login_required
def export_requests():
    """Экспорт заявок дар Excel бо назардошти фильтрҳо"""
    status = request.args.get('status', 'all')
    date_filter = request.args.get('date_filter', 'all')
    user_filter = request.args.get('user_filter', 'all')
    
    conn = get_db()
    query = '''
        SELECT r.*, u.full_name as author_name, u2.full_name as executor_name
        FROM requests r
        LEFT JOIN users u ON r.author_id = u.id
        LEFT JOIN users u2 ON r.executor_id = u2.id
        WHERE 1=1
    '''
    params = []
    
    # ========== ИСЛОҲ: Ҳама заявкаҳо барои экспорт ==========
    # Барои админ ҳеҷ маҳдудияте нест
    # Барои кормандон низ ҳама заявкаҳо экспорт карда мешаванд
    # if session['role'] != 'admin':
    #     query += ' AND r.author_id = ?'
    #     params.append(session['user_id'])
    
    # Фильтр по статусу
    if status != 'all':
        query += ' AND r.status = ?'
        params.append(status)
    
    # Фильтр по сотруднику (танҳо барои админ)
    if user_filter != 'all' and session['role'] == 'admin' and user_filter.isdigit():
        query += ' AND r.executor_id = ?'
        params.append(int(user_filter))
    
    # Фильтр по дате
    if date_filter != 'all':
        now = datetime.now()
        if date_filter == 'day':
            start_date = (now - timedelta(days=1)).isoformat()
        elif date_filter == 'week':
            start_date = (now - timedelta(weeks=1)).isoformat()
        elif date_filter == 'month':
            start_date = (now - timedelta(days=30)).isoformat()
        elif date_filter == 'year':
            start_date = (now - timedelta(days=365)).isoformat()
        else:
            start_date = None
        
        if start_date:
            query += ' AND r.created_date >= ?'
            params.append(start_date)
    
    query += ' ORDER BY r.id DESC'
    requests = conn.execute(query, params).fetchall()
    conn.close()
    
    # Создание Excel
    data = []
    for req in requests:
        data.append({
            'ID': req['id'],
            'Клиент': req['client_name'],
            'Телефон': req['phone'],
            'Тип': req['property_type'],
            'Адрес': req['address'],
            'Площадь (м²)': req['area'],
            'Комнаты': req['rooms'],
            'Окна': req['windows'],
            'Этаж': req['floor'],
            'Этажность': req['total_floors'],
            'Цена за м² (₽)': req['price_per_m2'],
            'Общая цена (₽)': req['total_price'],
            'Статус': req['status'],
            'Менеджер': req['manager'] or '',
            'SMM специалист': req['smm'] or '',
            'Автор': req['author_name'],
            'Исполнитель': req['executor_name'],
            'Дата создания': req['created_date']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Заявки', index=False)
        
        # Настройка ширины колонок
        worksheet = writer.sheets['Заявки']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(
        output, 
        download_name=f'requests_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ================ DASHBOARD API ================
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    conn = get_db()
    
    total_requests = conn.execute('SELECT COUNT(*) as count FROM requests').fetchone()
    new_requests = conn.execute('SELECT COUNT(*) as count FROM requests WHERE status = "new"').fetchone()
    progress_requests = conn.execute('SELECT COUNT(*) as count FROM requests WHERE status = "progress"').fetchone()
    done_requests = conn.execute('SELECT COUNT(*) as count FROM requests WHERE status = "done"').fetchone()
    
    total_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks').fetchone()
    new_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "new"').fetchone()
    progress_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "progress"').fetchone()
    done_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "done"').fetchone()
    
    conn.close()
    
    return jsonify({
        'requests': {
            'total': total_requests['count'],
            'new': new_requests['count'],
            'progress': progress_requests['count'],
            'done': done_requests['count']
        },
        'tasks': {
            'total': total_tasks['count'],
            'new': new_tasks['count'],
            'progress': progress_tasks['count'],
            'done': done_tasks['count']
        }
    })

# ================ CHAT API ================
@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    conn = get_db()
    messages = conn.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 200').fetchall()
    conn.close()
    return jsonify([dict(msg) for msg in messages])

@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    message = request.form.get('message', '')
    file_path = ''
    file_name = ''
    file_type = ''
    
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            file_name = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            file_path = os.path.join('uploads/chat', file_name)
            file.save(file_path)
            file_path = f'/uploads/chat/{file_name}'
            
            ext = file_name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                file_type = 'image'
            elif ext in ['mp4', 'webm', 'mov', 'avi']:
                file_type = 'video'
            else:
                file_type = 'file'
    
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO messages (user_id, user_name, message, file_path, file_name, file_type, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], session['user_name'], message,
            file_path, file_name, file_type, datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/messages/<int:message_id>', methods=['PUT'])
@login_required
def update_message(message_id):
    data = request.json
    conn = get_db()
    try:
        conn.execute('UPDATE messages SET message = ? WHERE id = ? AND user_id = ?', 
                    (data['message'], message_id, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE id = ? AND user_id = ?', (message_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

def migrate_messages_table():
    conn = get_db()
    try:
        # Тафтиши вуҷуди сутунҳо
        cursor = conn.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'file_name' not in columns:
            conn.execute('ALTER TABLE messages ADD COLUMN file_name TEXT')
            print("✅ Column 'file_name' added to messages table")
        
        if 'file_type' not in columns:
            conn.execute('ALTER TABLE messages ADD COLUMN file_type TEXT')
            print("✅ Column 'file_type' added to messages table")
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()


# ================ POSTS API ================

# ================ KANBAN BOARDS API ================


@app.route('/api/kanban/boards', methods=['GET'])
@login_required
def get_kanban_boards():
    """Получение всех доступных досок"""
    conn = get_db()
    if session['role'] == 'admin':
        boards = conn.execute('''
            SELECT DISTINCT b.* FROM kanban_boards b
            LEFT JOIN kanban_board_members m ON b.id = m.board_id
            WHERE b.is_archived = 0 AND (b.is_public = 1 OR b.author_id = ? OR m.user_id = ?)
            ORDER BY b.id DESC
        ''', (session['user_id'], session['user_id'])).fetchall()
    else:
        boards = conn.execute('''
            SELECT DISTINCT b.* FROM kanban_boards b
            LEFT JOIN kanban_board_members m ON b.id = m.board_id
            WHERE b.is_archived = 0 AND b.is_public = 1
            ORDER BY b.id DESC
        ''', ).fetchall()
    conn.close()
    return jsonify([dict(board) for board in boards])

@app.route('/api/kanban/boards', methods=['POST'])
@login_required
def create_kanban_board():
    """Создание новой доски"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO kanban_boards (title, color, is_public, author_id, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['title'], data.get('color', '#0079bf'), data['is_public'], 
              session['user_id'], datetime.now().isoformat(), datetime.now().isoformat()))
        board_id = cursor.lastrowid
        
        # Добавление участников для приватной доски
        if data['is_public'] == 0 and data.get('members'):
            for member_id in data['members']:
                conn.execute('''
                    INSERT INTO kanban_board_members (board_id, user_id, added_date)
                    VALUES (?, ?, ?)
                ''', (board_id, member_id, datetime.now().isoformat()))
        
        conn.commit()
        return jsonify({'success': True, 'id': board_id})
    except Exception as e:
        print(f"Error create_kanban_board: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/boards/<int:board_id>', methods=['PUT'])
@login_required
def update_kanban_board(board_id):
    """Обновление доски"""
    data = request.json
    conn = get_db()
    
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('''
            UPDATE kanban_boards SET title = ?, color = ?, is_public = ?, updated_date = ?
            WHERE id = ?
        ''', (data['title'], data.get('color', '#0079bf'), data['is_public'], 
              datetime.now().isoformat(), board_id))
        
        # Обновление участников для приватной доски
        conn.execute('DELETE FROM kanban_board_members WHERE board_id = ?', (board_id,))
        if data['is_public'] == 0 and data.get('members'):
            for member_id in data['members']:
                conn.execute('''
                    INSERT INTO kanban_board_members (board_id, user_id, added_date)
                    VALUES (?, ?, ?)
                ''', (board_id, member_id, datetime.now().isoformat()))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/boards/<int:board_id>', methods=['DELETE'])
@login_required
def delete_kanban_board(board_id):
    """Удаление доски со всеми колонками и лидами"""
    conn = get_db()
    
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('DELETE FROM kanban_boards WHERE id = ?', (board_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/boards/<int:board_id>/archive', methods=['PUT'])
@login_required
def archive_kanban_board(board_id):
    """Архивирование доски"""
    conn = get_db()
    
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('UPDATE kanban_boards SET is_archived = 1, updated_date = ? WHERE id = ?', 
                    (datetime.now().isoformat(), board_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/boards/<int:board_id>/columns', methods=['GET'])
@login_required
def get_kanban_columns(board_id):
    """Получение колонок доски"""
    conn = get_db()
    columns = conn.execute('''
        SELECT * FROM kanban_columns WHERE board_id = ? AND is_archived = 0
        ORDER BY order_index ASC
    ''', (board_id,)).fetchall()
    conn.close()
    return jsonify([dict(col) for col in columns])

@app.route('/api/kanban/columns', methods=['POST'])
@login_required
def create_kanban_column():
    """Создание новой колонки"""
    data = request.json
    conn = get_db()
    
    # Проверка доступа к доске
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (data['board_id'],)).fetchone()
    if not board:
        return jsonify({'success': False, 'error': 'Доска не найдена'}), 404
    
    if board['author_id'] != session['user_id'] and session['role'] != 'admin' and board['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        max_order = conn.execute('SELECT MAX(order_index) as max_order FROM kanban_columns WHERE board_id = ?',
                                 (data['board_id'],)).fetchone()
        order_index = (max_order['max_order'] or -1) + 1
        
        cursor = conn.execute('''
            INSERT INTO kanban_columns (board_id, title, color, order_index, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['board_id'], data['title'], data.get('color', '#0079bf'), order_index, datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/columns/<int:column_id>', methods=['PUT'])
@login_required
def update_kanban_column(column_id):
    """Обновление колонки"""
    data = request.json
    conn = get_db()
    
    column = conn.execute('''
        SELECT c.*, b.author_id as board_author_id, b.is_public
        FROM kanban_columns c
        JOIN kanban_boards b ON c.board_id = b.id
        WHERE c.id = ?
    ''', (column_id,)).fetchone()
    
    if not column:
        return jsonify({'success': False, 'error': 'Колонка не найдена'}), 404
    
    if column['board_author_id'] != session['user_id'] and session['role'] != 'admin' and column['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('''
            UPDATE kanban_columns SET title = ?, color = ?, order_index = ?
            WHERE id = ?
        ''', (data['title'], data.get('color', '#0079bf'), data.get('order_index', 0), column_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/columns/<int:column_id>', methods=['DELETE'])
@login_required
def delete_kanban_column(column_id):
    """Удаление колонки и всех лидов в ней"""
    conn = get_db()
    
    column = conn.execute('''
        SELECT c.*, b.author_id as board_author_id, b.is_public
        FROM kanban_columns c
        JOIN kanban_boards b ON c.board_id = b.id
        WHERE c.id = ?
    ''', (column_id,)).fetchone()
    
    if not column:
        return jsonify({'success': False, 'error': 'Колонка не найдена'}), 404
    
    if column['board_author_id'] != session['user_id'] and session['role'] != 'admin' and column['is_public'] == 0:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('DELETE FROM kanban_columns WHERE id = ?', (column_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/leads', methods=['GET'])
@login_required
def get_kanban_leads():
    """Получение лидов для доски"""
    board_id = request.args.get('board_id')
    if not board_id:
        return jsonify([])
    
    conn = get_db()
    leads = conn.execute('''
        SELECT l.*, u.full_name as author_name
        FROM kanban_leads l
        LEFT JOIN users u ON l.author_id = u.id
        WHERE l.board_id = ?
        ORDER BY l.column_id ASC, l.order_index ASC
    ''', (board_id,)).fetchall()
    conn.close()
    return jsonify([dict(lead) for lead in leads])

@app.route('/api/kanban/leads', methods=['POST'])
@login_required
def create_kanban_lead():
    """Создание нового лида"""
    data = request.json
    
    # Определение первой колонки доски
    conn = get_db()
    first_column = conn.execute('''
        SELECT id FROM kanban_columns WHERE board_id = ? ORDER BY order_index ASC LIMIT 1
    ''', (data['board_id'],)).fetchone()
    
    column_id = data.get('column_id', first_column['id'] if first_column else None)
    if not column_id:
        return jsonify({'success': False, 'error': 'Нет доступных колонок'}), 400
    
    # Получение порядка в колонке
    max_order = conn.execute('SELECT MAX(order_index) as max_order FROM kanban_leads WHERE column_id = ?',
                            (column_id,)).fetchone()
    order_index = (max_order['max_order'] or -1) + 1
    
    cursor = conn.execute('''
        INSERT INTO kanban_leads (column_id, board_id, client_name, phone, topic, comment, source, 
                                 mortgage, box, author_id, author_name, order_index, created_date, updated_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (column_id, data['board_id'], data['client_name'], data['phone'], data.get('topic', ''),
          data.get('comment', ''), data.get('source', 'Входящий'), data.get('mortgage', 0),
          data.get('box', 0), session['user_id'], session['user_name'], order_index,
          datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': cursor.lastrowid})

@app.route('/api/kanban/leads/<int:lead_id>', methods=['PUT'])
@login_required
def update_kanban_lead(lead_id):
    """Обновление лида"""
    data = request.json
    conn = get_db()
    
    lead = conn.execute('SELECT * FROM kanban_leads WHERE id = ?', (lead_id,)).fetchone()
    if not lead:
        return jsonify({'success': False, 'error': 'Лид не найден'}), 404
    
    try:
        conn.execute('''
            UPDATE kanban_leads SET 
                client_name = ?, phone = ?, topic = ?, comment = ?, source = ?,
                mortgage = ?, box = ?, updated_date = ?
            WHERE id = ?
        ''', (data['client_name'], data['phone'], data.get('topic', ''), data.get('comment', ''),
              data.get('source', 'Входящий'), data.get('mortgage', 0), data.get('box', 0),
              datetime.now().isoformat(), lead_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/leads/<int:lead_id>', methods=['DELETE'])
@login_required
def delete_kanban_lead(lead_id):
    """Удаление лида"""
    conn = get_db()
    conn.execute('DELETE FROM kanban_leads WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/kanban/leads/move', methods=['POST'])
@login_required
def move_kanban_lead():
    """Перемещение лида между колонками"""
    data = request.json
    lead_id = data['lead_id']
    new_column_id = data['column_id']
    new_order = data.get('order_index', 0)
    
    conn = get_db()
    
    # Обновляем порядок всех лидов в новой колонке
    conn.execute('''
        UPDATE kanban_leads SET order_index = order_index + 1 
        WHERE column_id = ? AND order_index >= ?
    ''', (new_column_id, new_order))
    
    # Перемещаем лид
    conn.execute('''
        UPDATE kanban_leads SET column_id = ?, order_index = ?, updated_date = ?
        WHERE id = ?
    ''', (new_column_id, new_order, datetime.now().isoformat(), lead_id))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ================ KANBAN BOARD API ================

# Добавление функции для экспорта в нужном формате
@app.route('/api/kanban/boards/<int:board_id>/export/excel', methods=['GET'])
@login_required
def export_kanban_board_custom(board_id):
    """Экспорт доски в Excel с правильной структурой"""
    conn = get_db()
    
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'error': 'Доска не найдена'}), 404
    
    columns = conn.execute('SELECT * FROM kanban_columns WHERE board_id = ? ORDER BY order_index', (board_id,)).fetchall()
    leads = conn.execute('''
        SELECT l.*, u.full_name as author_name, c.title as column_title
        FROM kanban_leads l
        LEFT JOIN users u ON l.author_id = u.id
        LEFT JOIN kanban_columns c ON l.column_id = c.id
        WHERE l.board_id = ?
        ORDER BY l.column_id, l.order_index
    ''', (board_id,)).fetchall()
    conn.close()
    
    # Подготовка данных с правильной структурой
    data = []
    for lead in leads:
        data.append({
            'Колонка': lead['column_title'],
            'Клиент': lead['client_name'],
            'Телефон': lead['phone'],
            'Тема разговора': lead['topic'] or '',
            'Комментарий': lead['comment'] or '',
            'Источник': lead['source'],
            'Ипотека': 'Да' if lead['mortgage'] else 'Нет',
            'Коробка': 'Да' if lead['box'] else 'Нет',
            'Автор': lead['author_name'],
            'Дата создания': lead['created_date']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=board['title'][:31], index=False)
        
        worksheet = writer.sheets[board['title'][:31]]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(output, download_name=f'board_{board["title"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
                    as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/api/kanban/import/excel', methods=['POST'])
@login_required
def import_kanban_excel_custom():
    """Импорт лидов из Excel с обработкой всех колонок"""
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    
    file = request.files['file']
    board_id = request.form.get('board_id')
    
    if not board_id:
        return jsonify({'error': 'Board ID required'}), 400
    
    try:
        df = pd.read_excel(file)
        
        conn = get_db()
        
        # Получаем первую колонку доски
        first_column = conn.execute('''
            SELECT id FROM kanban_columns WHERE board_id = ? ORDER BY order_index LIMIT 1
        ''', (board_id,)).fetchone()
        
        if not first_column:
            return jsonify({'error': 'Нет колонок в доске'}), 400
        
        column_id = first_column['id']
        
        # Получаем текущий максимальный порядок
        max_order = conn.execute('SELECT COALESCE(MAX(order_index), -1) as max FROM kanban_leads WHERE column_id = ?',
                                (column_id,)).fetchone()
        order_index = max_order['max'] + 1
        
        imported_count = 0
        skipped_count = 0
        
        # Маппинг колонок (поддерживаем кириллицу и английские названия)
        column_mapping = {
            'Колонка': 'column',
            'Клиент': 'client_name',
            'Телефон': 'phone', 
            'Тема разговора': 'topic',
            'Комментарий': 'comment',
            'Источник': 'source',
            'Ипотека': 'mortgage',
            'Коробка': 'box',
            'Автор': 'author',
            'Дата создания': 'created_date'
        }
        
        # Определяем индексы колонок в файле
        headers = list(df.columns)
        col_indices = {}
        for i, header in enumerate(headers):
            header_clean = str(header).strip()
            if header_clean in column_mapping:
                col_indices[column_mapping[header_clean]] = i
            # Альтернативные названия
            elif header_clean in ['Имя', 'ФИО', 'Клиент/ФИО']:
                col_indices['client_name'] = i
            elif header_clean in ['Номер', 'Тел', 'Номер телефона']:
                col_indices['phone'] = i
            elif header_clean in ['Тема', 'Тематика']:
                col_indices['topic'] = i
            elif header_clean in ['Комментарии', 'Примечание']:
                col_indices['comment'] = i
            elif header_clean in ['Источник лида', 'Откуда']:
                col_indices['source'] = i
            elif header_clean in ['Ипотека/Кредит']:
                col_indices['mortgage'] = i
            elif header_clean in ['Коробка/Отделка']:
                col_indices['box'] = i
        
        # Обязательные поля
        required_fields = ['client_name', 'phone']
        for field in required_fields:
            if field not in col_indices:
                return jsonify({'error': f'Не найдена колонка: {field}. Доступные колонки: {headers}'}), 400
        
        for _, row in df.iterrows():
            try:
                client_name = str(row.iloc[col_indices['client_name']]) if pd.notna(row.iloc[col_indices['client_name']]) else ''
                phone = str(row.iloc[col_indices['phone']]) if pd.notna(row.iloc[col_indices['phone']]) else ''
                
                if not client_name or not phone or client_name == 'nan' or phone == 'nan':
                    skipped_count += 1
                    continue
                
                topic = str(row.iloc[col_indices['topic']]) if 'topic' in col_indices and pd.notna(row.iloc[col_indices['topic']]) else ''
                comment = str(row.iloc[col_indices['comment']]) if 'comment' in col_indices and pd.notna(row.iloc[col_indices['comment']]) else ''
                source = str(row.iloc[col_indices['source']]) if 'source' in col_indices and pd.notna(row.iloc[col_indices['source']]) else 'Входящий'
                
                # Обработка ипотеки и коробки (поддерживаем разные форматы)
                mortgage = 0
                if 'mortgage' in col_indices:
                    val = str(row.iloc[col_indices['mortgage']]).lower()
                    if val in ['да', 'yes', 'true', '1', '+', '✅']:
                        mortgage = 1
                    elif 'ипотек' in comment.lower():
                        mortgage = 1
                
                box = 0
                if 'box' in col_indices:
                    val = str(row.iloc[col_indices['box']]).lower()
                    if val in ['да', 'yes', 'true', '1', '+', '✅']:
                        box = 1
                    elif 'коробк' in comment.lower():
                        box = 1
                
                # Автоматическое определение из комментария
                if not mortgage and ('ипотек' in comment.lower() or 'кредит' in comment.lower()):
                    mortgage = 1
                if not box and ('коробк' in comment.lower() or 'отделк' in comment.lower()):
                    box = 1
                
                # Ограничим длину источника
                valid_sources = ['Входящий', 'Исходящий', 'WhatsApp', 'Telegram', 'Somon.tj', 'Instagram', 'TikTok', 'Офис застройщика', 'Наш офис', 'Холодный контакт']
                if source not in valid_sources:
                    source = 'Входящий'
                
                conn.execute('''
                    INSERT INTO kanban_leads (column_id, board_id, client_name, phone, topic, comment, source,
                                             mortgage, box, author_id, author_name, order_index, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (column_id, board_id, client_name[:100], phone[:50], topic[:200], comment[:1000], source,
                      mortgage, box, session['user_id'], session['user_name'], order_index,
                      datetime.now().isoformat(), datetime.now().isoformat()))
                order_index += 1
                imported_count += 1
                
            except Exception as row_error:
                print(f"Row import error: {row_error}")
                skipped_count += 1
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'count': imported_count, 'skipped': skipped_count})
    except Exception as e:
        print(f"Import error: {e}")
        return jsonify({'error': str(e)}), 400
    
    
# ================ KANBAN ENHANCED API ================

@app.route('/api/kanban/columns/<int:column_id>/order', methods=['PUT'])
@login_required
def update_column_order(column_id):
    """Обновление порядка колонки"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('UPDATE kanban_columns SET order_index = ? WHERE id = ?', 
                    (data['order_index'], column_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/leads/<int:lead_id>/order', methods=['PUT'])
@login_required
def update_lead_order(lead_id):
    """Обновление порядка лида"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('UPDATE kanban_leads SET order_index = ? WHERE id = ?', 
                    (data['order_index'], lead_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/columns/<int:column_id>/export/excel', methods=['GET'])
@login_required
def export_column_to_excel(column_id):
    """Экспорт колонки в Excel"""
    conn = get_db()
    
    column = conn.execute('SELECT * FROM kanban_columns WHERE id = ?', (column_id,)).fetchone()
    if not column:
        return jsonify({'error': 'Колонка не найдена'}), 404
    
    leads = conn.execute('''
        SELECT l.*, u.full_name as author_name 
        FROM kanban_leads l
        LEFT JOIN users u ON l.author_id = u.id
        WHERE l.column_id = ?
        ORDER BY l.order_index
    ''', (column_id,)).fetchall()
    conn.close()
    
    data = []
    for lead in leads:
        data.append({
            'Дата создания': lead['created_date'],
            'Имя клиента': lead['client_name'],
            'Телефон': lead['phone'],
            'Тема разговора': lead['topic'] or '',
            'Комментарий': lead['comment'] or '',
            'Источник': lead['source'],
            'Ипотека': 'Да' if lead['mortgage'] else 'Нет',
            'Коробка': 'Да' if lead['box'] else 'Нет',
            'Автор': lead['author_name']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=column['title'][:31], index=False)
        
        worksheet = writer.sheets[column['title'][:31]]
        for column_letter in worksheet.columns:
            max_length = 0
            col_letter = column_letter[0].column_letter
            for cell in column_letter:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[col_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(output, download_name=f'column_{column["title"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
                    as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/api/kanban/actions/track', methods=['POST'])
@login_required
def track_kanban_action():
    """Трекинг действий сотрудников"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO kanban_lead_interactions (lead_id, phone, topic, source, contact_type, comment, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('lead_id'), session.get('user_phone', ''), data.get('description', ''),
              '', data['action_type'], data['description'], datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/kanban/import/excel', methods=['POST'])
@login_required
def import_kanban_excel():
    """Импорт лидов из Excel"""
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    
    file = request.files['file']
    board_id = request.form.get('board_id')
    
    if not board_id:
        return jsonify({'error': 'Board ID required'}), 400
    
    try:
        df = pd.read_excel(file)
        
        # Get first column
        conn = get_db()
        first_column = conn.execute('''
            SELECT id FROM kanban_columns WHERE board_id = ? ORDER BY order_index LIMIT 1
        ''', (board_id,)).fetchone()
        
        if not first_column:
            return jsonify({'error': 'Нет колонок в доске'}), 400
        
        column_id = first_column['id']
        
        # Get current max order
        max_order = conn.execute('SELECT COALESCE(MAX(order_index), -1) as max FROM kanban_leads WHERE column_id = ?',
                                (column_id,)).fetchone()
        order_index = max_order['max'] + 1
        
        imported_count = 0
        
        for _, row in df.iterrows():
            # Определение полей
            client_name = str(row.iloc[0]) if len(row) > 0 else ''
            phone = str(row.iloc[1]) if len(row) > 1 else ''
            topic = str(row.iloc[2]) if len(row) > 2 else ''
            comment = str(row.iloc[3]) if len(row) > 3 else ''
            source = str(row.iloc[4]) if len(row) > 4 else 'Входящий'
            
            # Автоматическое определение ипотеки и коробки
            mortgage = 1 if comment and ('ипотек' in comment.lower() or 'ипотека' in comment.lower()) else 0
            box = 1 if comment and ('коробк' in comment.lower() or 'box' in comment.lower()) else 0
            
            if client_name and phone:
                conn.execute('''
                    INSERT INTO kanban_leads (column_id, board_id, client_name, phone, topic, comment, source,
                                             mortgage, box, author_id, author_name, order_index, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (column_id, board_id, client_name, phone, topic, comment, source,
                      mortgage, box, session['user_id'], session['user_name'], order_index,
                      datetime.now().isoformat(), datetime.now().isoformat()))
                order_index += 1
                imported_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'count': imported_count})
    except Exception as e:
        print(f"Import error: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/kanban/boards/<int:board_id>/export/excel', methods=['GET'])
@login_required
def export_kanban_board_full(board_id):
    """Экспорт всей доски с разделением по колонкам"""
    conn = get_db()
    
    board = conn.execute('SELECT * FROM kanban_boards WHERE id = ?', (board_id,)).fetchone()
    if not board:
        return jsonify({'error': 'Доска не найдена'}), 404
    
    columns = conn.execute('SELECT * FROM kanban_columns WHERE board_id = ? ORDER BY order_index', (board_id,)).fetchall()
    leads = conn.execute('''
        SELECT l.*, u.full_name as author_name, c.title as column_title
        FROM kanban_leads l
        LEFT JOIN users u ON l.author_id = u.id
        LEFT JOIN kanban_columns c ON l.column_id = c.id
        WHERE l.board_id = ?
        ORDER BY l.column_id, l.order_index
    ''', (board_id,)).fetchall()
    conn.close()
    
    # Apply filters if provided
    search = request.args.get('search', '')
    source = request.args.get('source', 'all')
    mortgage = request.args.get('mortgage', 'all')
    box = request.args.get('box', 'all')
    author = request.args.get('author', 'all')
    date_range = request.args.get('date_range', 'all')
    
    filtered_leads = []
    for lead in leads:
        show = True
        if search and search not in lead['client_name'].lower() and search not in lead['phone']:
            show = False
        if source != 'all' and lead['source'] != source:
            show = False
        if mortgage == 'yes' and not lead['mortgage']:
            show = False
        if mortgage == 'no' and lead['mortgage']:
            show = False
        if box == 'yes' and not lead['box']:
            show = False
        if box == 'no' and lead['box']:
            show = False
        if author != 'all' and lead['author_id'] != int(author):
            show = False
        if show:
            filtered_leads.append(lead)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Общий лист
        all_data = []
        for lead in filtered_leads:
            all_data.append({
                'Колонка': lead['column_title'],
                'Дата создания': lead['created_date'],
                'Имя клиента': lead['client_name'],
                'Телефон': lead['phone'],
                'Тема': lead['topic'] or '',
                'Комментарий': lead['comment'] or '',
                'Источник': lead['source'],
                'Ипотека': 'Да' if lead['mortgage'] else 'Нет',
                'Коробка': 'Да' if lead['box'] else 'Нет',
                'Автор': lead['author_name']
            })
        
        df_all = pd.DataFrame(all_data)
        df_all.to_excel(writer, sheet_name='Все лиды', index=False)
        
        # Отдельные листы по колонкам
        for column in columns:
            column_leads = [l for l in filtered_leads if l['column_id'] == column['id']]
            if column_leads:
                col_data = []
                for lead in column_leads:
                    col_data.append({
                        'Дата создания': lead['created_date'],
                        'Имя клиента': lead['client_name'],
                        'Телефон': lead['phone'],
                        'Тема': lead['topic'] or '',
                        'Комментарий': lead['comment'] or '',
                        'Источник': lead['source'],
                        'Ипотека': 'Да' if lead['mortgage'] else 'Нет',
                        'Коробка': 'Да' if lead['box'] else 'Нет',
                        'Автор': lead['author_name']
                    })
                df_col = pd.DataFrame(col_data)
                sheet_name = column['title'][:31]
                df_col.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Автоширина колонок для всех листов
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for column_cell in worksheet.columns:
                max_length = 0
                col_letter = column_cell[0].column_letter
                for cell in column_cell:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[col_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(output, download_name=f'board_{board["title"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', 
                    as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ================ POSTS API ================

@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    # Гирифтани параметрҳои филтр
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    content_type = request.args.get('content_type', 'all')
    author = request.args.get('author', 'all')
    project = request.args.get('project', 'all')
    date_range = request.args.get('date_range', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db()
    query = '''
        SELECT p.*, u.full_name as user_name 
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    # Параметрҳои филтр
    if search:
        query += ' AND (p.title LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category != 'all':
        query += ' AND p.category = ?'
        params.append(category)
    
    if content_type != 'all':
        query += ' AND p.content_type = ?'
        params.append(content_type)
    
    if author != 'all':
        query += ' AND p.user_id = ?'
        params.append(int(author))
    
    if project != 'all':
        query += ' AND p.project = ?'
        params.append(project)
    
    # Филтрҳои рӯз
    now = datetime.now()
    if date_range == 'today':
        today = now.strftime('%Y-%m-%d')
        query += ' AND (p.post_date = ? OR DATE(p.created_date) = ?)'
        params.extend([today, today])
    elif date_range == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        start_str = start_of_week.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'month':
        start_of_month = now.replace(day=1)
        start_str = start_of_month.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'range' and date_from and date_to:
        query += ' AND (p.post_date BETWEEN ? AND ? OR DATE(p.created_date) BETWEEN ? AND ?)'
        params.extend([date_from, date_to, date_from, date_to])
    
    query += ' ORDER BY p.created_date DESC'
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(post) for post in posts])

@app.route('/api/posts', methods=['POST'])
@login_required
def add_post():
    """Илова кардани пост"""
    category = request.form.get('category')
    content_type = request.form.get('content_type')
    project = request.form.get('project')
    title = request.form.get('title')
    description = request.form.get('description', '')
    link = request.form.get('link', '')
    post_date = request.form.get('post_date', '')
    
    # Валидатсия
    if not category or not content_type or not project or not title:
        return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400
    
    media_path = ''
    media_type = ''
    
    # Коркарди файл
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join('uploads/posts', filename)
            file.save(filepath)
            media_path = f'/uploads/posts/{filename}'
            
            ext = filename.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                media_type = 'image'
            elif ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
                media_type = 'video'
            else:
                media_type = 'file'
    
    conn = get_db()
    try:
        # Агар post_date набошат, санаи ҷорӣ гирем
        if not post_date:
            post_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor = conn.execute('''
            INSERT INTO posts (user_id, user_name, category, content_type, project, 
                              title, description, link, media_path, media_type, post_date, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], session['user_name'], category, content_type, project,
            title, description, link, media_path, media_type, post_date, datetime.now().isoformat()
        ))
        conn.commit()
        
        # Фиристодани уведомление
        try:
            send_notification_to_user(session['user_id'], "Пост создан", 
                                     f"Создан новый пост: {title}", "post", "/posts")
        except:
            pass
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error adding post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    """Таҳрир кардани пост"""
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        return jsonify({'success': False, 'error': 'Пост не найден'}), 404
    
    # Санҷиши ҳуқуқ
    if post['user_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав для редактирования'}), 403
    
    category = request.form.get('category')
    content_type = request.form.get('content_type')
    project = request.form.get('project')
    title = request.form.get('title')
    description = request.form.get('description', '')
    link = request.form.get('link', '')
    post_date = request.form.get('post_date', '')
    
    media_path = post['media_path']
    media_type = post['media_type']
    
    # Коркарди файли нав (агар бошад)
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename:
            # Нест кардани файли кӯҳна
            if media_path and os.path.exists(media_path[1:]):
                try:
                    os.remove(media_path[1:])
                except:
                    pass
            
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join('uploads/posts', filename)
            file.save(filepath)
            media_path = f'/uploads/posts/{filename}'
            
            ext = filename.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                media_type = 'image'
            elif ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
                media_type = 'video'
            else:
                media_type = 'file'
    
    try:
        conn.execute('''
            UPDATE posts SET 
                category = ?, content_type = ?, project = ?, title = ?,
                description = ?, link = ?, media_path = ?, media_type = ?, post_date = ?
            WHERE id = ?
        ''', (category, content_type, project, title, description, link, media_path, media_type, post_date, post_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """Нест кардани пост"""
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        return jsonify({'success': False, 'error': 'Пост не найден'}), 404
    
    # Санҷиши ҳуқуқ
    if post['user_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав для удаления'}), 403
    
    # Нест кардани файли медиа
    if post['media_path'] and os.path.exists(post['media_path'][1:]):
        try:
            os.remove(post['media_path'][1:])
        except:
            pass
    
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ================ EXPORT POSTS TO EXCEL ================

@app.route('/api/posts/export/excel', methods=['GET'])
@login_required
def export_posts_excel():
    """Экспортировать посты в Excel"""
    # Гирифтани параметрҳои филтр
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    content_type = request.args.get('content_type', 'all')
    author = request.args.get('author', 'all')
    project = request.args.get('project', 'all')
    date_range = request.args.get('date_range', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db()
    query = '''
        SELECT p.*, u.full_name as user_name 
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (p.title LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    if category != 'all':
        query += ' AND p.category = ?'
        params.append(category)
    if content_type != 'all':
        query += ' AND p.content_type = ?'
        params.append(content_type)
    if author != 'all':
        query += ' AND p.user_id = ?'
        params.append(int(author))
    if project != 'all':
        query += ' AND p.project = ?'
        params.append(project)
    
    now = datetime.now()
    if date_range == 'today':
        today = now.strftime('%Y-%m-%d')
        query += ' AND (p.post_date = ? OR DATE(p.created_date) = ?)'
        params.extend([today, today])
    elif date_range == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        start_str = start_of_week.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'month':
        start_of_month = now.replace(day=1)
        start_str = start_of_month.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'range' and date_from and date_to:
        query += ' AND (p.post_date BETWEEN ? AND ? OR DATE(p.created_date) BETWEEN ? AND ?)'
        params.extend([date_from, date_to, date_from, date_to])
    
    query += ' ORDER BY p.created_date DESC'
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    # Таҳияи маълумот барои Excel
    platforms = ['instagram', 'telegram', 'tiktok', 'facebook', 'youtube', 'other']
    platform_names = {'instagram': 'Instagram', 'telegram': 'Telegram', 'tiktok': 'TikTok', 
                      'facebook': 'Facebook', 'youtube': 'YouTube', 'other': 'Другое'}
    
    # Листи статистика
    stats_data = []
    stats_data.append(['Платформа', 'Reels', 'Stories', 'Публикации', 'Всего'])
    
    total_stats = {'reels': 0, 'stories': 0, 'publication': 0}
    for platform in platforms:
        reels = len([p for p in posts if p['category'] == platform and p['content_type'] == 'reels'])
        stories = len([p for p in posts if p['category'] == platform and p['content_type'] == 'stories'])
        publication = len([p for p in posts if p['category'] == platform and p['content_type'] == 'publication'])
        total_stats['reels'] += reels
        total_stats['stories'] += stories
        total_stats['publication'] += publication
        stats_data.append([platform_names.get(platform, platform), reels, stories, publication, reels + stories + publication])
    
    stats_data.append(['ИТОГО', total_stats['reels'], total_stats['stories'], total_stats['publication'], sum(total_stats.values())])
    
    # Листи постҳо
    posts_data = []
    posts_data.append(['ID', 'Дата', 'Платформа', 'Тип', 'Проект', 'Название', 'Описание', 'Ссылка', 'Автор', 'Дата создания'])
    for post in posts:
        posts_data.append([
            post['id'],
            post['post_date'] or post['created_date'][:10],
            platform_names.get(post['category'], post['category']),
            post['content_type'],
            'nav_xona' if post['project'] == 'nav_xona' else 'navsoht',
            post['title'],
            post['description'] or '',
            post['link'] or '',
            post['user_name'],
            post['created_date']
        ])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Листи статистика
        df_stats = pd.DataFrame(stats_data[1:], columns=stats_data[0])
        df_stats.to_excel(writer, sheet_name='Статистика', index=False)
        
        # Листи постҳо
        df_posts = pd.DataFrame(posts_data[1:], columns=posts_data[0])
        df_posts.to_excel(writer, sheet_name='Посты', index=False)
        
        # Танзими васеъии сутунҳо
        for sheetname in ['Статистика', 'Посты']:
            worksheet = writer.sheets[sheetname]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return send_file(output, download_name=f'posts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', as_attachment=True)

# ================ EXPORT POSTS TO PDF ================

@app.route('/api/posts/export/pdf', methods=['GET'])
@login_required
def export_posts_pdf():
    """Экспортировать посты в PDF"""
    from io import BytesIO as IO_bytes
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    # Гирифтани параметрҳои филтр
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    content_type = request.args.get('content_type', 'all')
    author = request.args.get('author', 'all')
    project = request.args.get('project', 'all')
    date_range = request.args.get('date_range', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db()
    query = '''
        SELECT p.*, u.full_name as user_name 
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (p.title LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    if category != 'all':
        query += ' AND p.category = ?'
        params.append(category)
    if content_type != 'all':
        query += ' AND p.content_type = ?'
        params.append(content_type)
    if author != 'all':
        query += ' AND p.user_id = ?'
        params.append(int(author))
    if project != 'all':
        query += ' AND p.project = ?'
        params.append(project)
    
    now = datetime.now()
    if date_range == 'today':
        today = now.strftime('%Y-%m-%d')
        query += ' AND (p.post_date = ? OR DATE(p.created_date) = ?)'
        params.extend([today, today])
    elif date_range == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        start_str = start_of_week.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'month':
        start_of_month = now.replace(day=1)
        start_str = start_of_month.strftime('%Y-%m-%d')
        query += ' AND (p.post_date >= ? OR DATE(p.created_date) >= ?)'
        params.extend([start_str, start_str])
    elif date_range == 'range' and date_from and date_to:
        query += ' AND (p.post_date BETWEEN ? AND ? OR DATE(p.created_date) BETWEEN ? AND ?)'
        params.extend([date_from, date_to, date_from, date_to])
    
    query += ' ORDER BY p.created_date DESC'
    posts = conn.execute(query, params).fetchall()
    
    # Гирифтани маълумоти корбар барои филтр
    author_name = ''
    if author != 'all':
        user = conn.execute('SELECT full_name FROM users WHERE id = ?', (int(author),)).fetchone()
        if user:
            author_name = user['full_name']
    conn.close()
    
    # Таҳияи маълумот барои статистика
    platforms = ['instagram', 'telegram', 'tiktok', 'facebook', 'youtube', 'other']
    platform_names = {'instagram': 'Instagram', 'telegram': 'Telegram', 'tiktok': 'TikTok', 
                      'facebook': 'Facebook', 'youtube': 'YouTube', 'other': 'Другое'}
    
    stats_by_platform = {p: {'reels': 0, 'stories': 0, 'publication': 0} for p in platforms}
    for post in posts:
        if post['category'] in stats_by_platform:
            stats_by_platform[post['category']][post['content_type']] += 1
    
    total_stats = {'reels': 0, 'stories': 0, 'publication': 0}
    for p in platforms:
        total_stats['reels'] += stats_by_platform[p]['reels']
        total_stats['stories'] += stats_by_platform[p]['stories']
        total_stats['publication'] += stats_by_platform[p]['publication']
    
    total_posts = sum(total_stats.values())
    
    # Создание PDF
    buffer = IO_bytes()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                           rightMargin=15, leftMargin=15, topMargin=25, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    
    # Заголовок
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                  fontSize=18, textColor=colors.HexColor('#2563eb'), 
                                  alignment=TA_CENTER, spaceAfter=15)
    story.append(Paragraph("Отчет по публикациям в социальных сетях", title_style))
    
    # Информация о фильтрах
    filter_text = f"Период: "
    if date_range == 'today':
        filter_text += f"Сегодня ({datetime.now().strftime('%d.%m.%Y')})"
    elif date_range == 'week':
        start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
        filter_text += f"Эта неделя (с {start_of_week.strftime('%d.%m.%Y')})"
    elif date_range == 'month':
        start_of_month = datetime.now().replace(day=1)
        filter_text += f"Этот месяц (с {start_of_month.strftime('%d.%m.%Y')})"
    elif date_range == 'range' and date_from and date_to:
        filter_text += f"с {date_from} по {date_to}"
    else:
        filter_text += "За все время"
    
    if author_name:
        filter_text += f" | Автор: {author_name}"
    if category != 'all':
        filter_text += f" | Платформа: {platform_names.get(category, category)}"
    if content_type != 'all':
        filter_text += f" | Тип: {content_type}"
    
    filter_style = ParagraphStyle('FilterStyle', parent=styles['Normal'], 
                                   fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=12)
    story.append(Paragraph(filter_text, filter_style))
    story.append(Spacer(1, 5))
    
    # Таблица статистики по платформам
    table_data = [['Платформа', 'Reels', 'Stories', 'Публикации', 'Всего']]
    for platform in platforms:
        row = [
            platform_names[platform],
            str(stats_by_platform[platform]['reels']),
            str(stats_by_platform[platform]['stories']),
            str(stats_by_platform[platform]['publication']),
            str(sum(stats_by_platform[platform].values()))
        ]
        table_data.append(row)
    
    table_data.append(['ИТОГО', str(total_stats['reels']), str(total_stats['stories']), 
                       str(total_stats['publication']), str(total_posts)])
    
    table = Table(table_data, colWidths=[90, 60, 60, 90, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e0e0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))
    
    # Создание диаграммы с помощью matplotlib
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Диаграмма по типам контента
    type_labels = ['Reels', 'Stories', 'Публикации']
    type_values = [total_stats['reels'], total_stats['stories'], total_stats['publication']]
    colors_list = ['#3b82f6', '#f59e0b', '#10b981']
    
    if sum(type_values) > 0:
        ax1.pie(type_values, labels=type_labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
    else:
        ax1.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax1.transAxes)
    ax1.set_title('Распределение по типам контента', fontsize=11, fontweight='bold')
    
    # Диаграмма по платформам
    platform_labels = [platform_names[p] for p in platforms]
    platform_values = [sum(stats_by_platform[p].values()) for p in platforms]
    
    if sum(platform_values) > 0:
        bars = ax2.bar(platform_labels, platform_values, color='#2563eb')
        ax2.set_title('Количество постов по платформам', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Количество')
        ax2.tick_params(axis='x', rotation=45, labelsize=8)
        for bar, val in zip(bars, platform_values):
            if val > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, 
                        str(val), ha='center', va='bottom', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    
    # Сохранение диаграммы
    chart_buffer = IO_bytes()
    plt.savefig(chart_buffer, format='png', dpi=120, bbox_inches='tight')
    chart_buffer.seek(0)
    plt.close()
    
    from reportlab.platypus import Image
    img = Image(chart_buffer, width=430, height=170)
    story.append(img)
    story.append(Spacer(1, 15))
    
    # Таблица постов
    story.append(Paragraph("Список публикаций", 
                          ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=12, spaceAfter=8)))
    
    posts_data = [['Дата', 'Платформа', 'Тип', 'Название', 'Автор']]
    for post in posts[:30]:  # Максимум 30 постҳо
        posts_data.append([
            post['post_date'] or post['created_date'][:10],
            platform_names.get(post['category'], post['category']),
            post['content_type'],
            (post['title'][:35] + '...') if len(post['title']) > 35 else post['title'],
            post['user_name']
        ])
    
    posts_table = Table(posts_data, colWidths=[70, 80, 70, 160, 80])
    posts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(posts_table)
    
    # Сборка PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(buffer, download_name=f'posts_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf', 
                    as_attachment=True, mimetype='application/pdf')

# ================ FILES & FOLDERS API ================

@app.route('/api/folders', methods=['GET'])
@login_required
def get_folders():
    parent_id = request.args.get('parent_id', 0)
    conn = get_db()
    folders = conn.execute('''
        SELECT f.*, u.full_name as author_name 
        FROM folders f
        LEFT JOIN users u ON f.author_id = u.id
        WHERE f.parent_id = ?
        ORDER BY f.name ASC
    ''', (parent_id,)).fetchall()
    conn.close()
    return jsonify([dict(folder) for folder in folders])

@app.route('/api/folders', methods=['POST'])
@login_required
def create_folder():
    data = request.json
    name = data.get('name')
    parent_id = data.get('parent_id', 0)
    
    # Добавление даты к названию папки
    date_str = datetime.now().strftime('%Y-%m-%d')
    full_name = f"{name}_{date_str}"
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO folders (name, parent_id, author_id, author_name, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, parent_id, session['user_id'], session['user_name'], datetime.now().isoformat()))
        conn.commit()
        
        # Создание физической папки
        folder_path = os.path.join('uploads', 'folders', str(cursor.lastrowid))
        os.makedirs(folder_path, exist_ok=True)
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/folders/<int:folder_id>', methods=['PUT'])
@login_required
def rename_folder(folder_id):
    data = request.json
    new_name = data.get('name')
    
    conn = get_db()
    folder = conn.execute('SELECT * FROM folders WHERE id = ?', (folder_id,)).fetchone()
    
    if not folder:
        return jsonify({'success': False, 'error': 'Папка не найдена'}), 404
    
    if folder['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        conn.execute('UPDATE folders SET name = ? WHERE id = ?', (new_name, folder_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    conn = get_db()
    folder = conn.execute('SELECT * FROM folders WHERE id = ?', (folder_id,)).fetchone()
    
    if not folder:
        return jsonify({'success': False, 'error': 'Папка не найдена'}), 404
    
    if folder['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        # Удаление файлов из БД
        conn.execute('DELETE FROM folder_files WHERE folder_id = ?', (folder_id,))
        conn.execute('DELETE FROM folders WHERE id = ?', (folder_id,))
        conn.commit()
        
        # Удаление физической папки
        import shutil
        folder_path = os.path.join('uploads', 'folders', str(folder_id))
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/folders/<int:folder_id>/files', methods=['GET'])
@login_required
def get_files(folder_id):
    conn = get_db()
    files = conn.execute('''
        SELECT * FROM folder_files 
        WHERE folder_id = ? 
        ORDER BY created_date DESC
    ''', (folder_id,)).fetchall()
    conn.close()
    return jsonify([dict(file) for file in files])

@app.route('/api/folders/<int:folder_id>/files', methods=['POST'])
@login_required
def upload_file(folder_id):
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Нет файла'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Нет файла'}), 400
    
    original_name = file.filename
    safe_filename = secure_filename(f"{datetime.now().timestamp()}_{original_name}")
    
    # Сохранение файла
    folder_path = os.path.join('uploads', 'folders', str(folder_id))
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, safe_filename)
    file.save(filepath)
    
    # Определение типа файла
    ext = original_name.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        filetype = 'image'
    elif ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
        filetype = 'video'
    elif ext == 'pdf':
        filetype = 'pdf'
    else:
        filetype = 'other'
    
    filesize = os.path.getsize(filepath)
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO folder_files (folder_id, filename, original_name, filepath, filetype, filesize, author_id, author_name, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (folder_id, safe_filename, original_name, f'/uploads/folders/{folder_id}/{safe_filename}', 
              filetype, filesize, session['user_id'], session['user_name'], datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    conn = get_db()
    file = conn.execute('SELECT * FROM folder_files WHERE id = ?', (file_id,)).fetchone()
    
    if not file:
        return jsonify({'success': False, 'error': 'Файл не найден'}), 404
    
    # Проверка прав: автор папки или админ могут удалять
    folder = conn.execute('SELECT * FROM folders WHERE id = ?', (file['folder_id'],)).fetchone()
    if folder['author_id'] != session['user_id'] and session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Нет прав'}), 403
    
    try:
        # Удаление физического файла
        filepath = os.path.join('uploads', 'folders', str(file['folder_id']), file['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        conn.execute('DELETE FROM folder_files WHERE id = ?', (file_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/download/<int:file_id>')
@login_required
def download_file(file_id):
    conn = get_db()
    file = conn.execute('SELECT * FROM folder_files WHERE id = ?', (file_id,)).fetchone()
    conn.close()
    
    if not file:
        return jsonify({'error': 'Файл не найден'}), 404
    
    filepath = os.path.join('uploads', 'folders', str(file['folder_id']), file['filename'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'Файл не найден'}), 404
    
    return send_file(filepath, as_attachment=True, download_name=file['original_name'])

@app.route('/baza')
@login_required
def baza_page():
    return render_template('baza.html')


# ================ REALTY OBJECTS WITH MAP API ================

@app.route('/karta')
@login_required
def karta_page():
    """Саҳифаи карта бо объектҳои недвижимость"""
    return render_template('karta.html')

# -------------------- OBJECTS (бо координатаҳо) --------------------
@app.route('/api/realty/objects', methods=['GET'])
@login_required
def get_realty_objects():
    """Гирифтани ҳамаи объектҳо бо координатаҳо"""
    conn = get_db()
    
    # Санҷиши вуҷуди сутунҳои lat ва lng
    cursor = conn.execute("PRAGMA table_info(realty_objects)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'lat' not in columns:
        conn.execute('ALTER TABLE realty_objects ADD COLUMN lat REAL DEFAULT 38.5598')
        conn.execute('ALTER TABLE realty_objects ADD COLUMN lng REAL DEFAULT 68.7870')
        conn.commit()
    
    objects = conn.execute('''
        SELECT o.*, u.full_name as author_name 
        FROM realty_objects o
        LEFT JOIN users u ON o.author_id = u.id
        ORDER BY o.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(obj) for obj in objects])

@app.route('/api/realty/objects', methods=['POST'])
@login_required
@admin_required
def add_realty_object():
    """Илова кардани объекти нав бо координатаҳо"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO realty_objects (name, description, address, lat, lng, construction_type, district,
                                        area, rooms, windows, floor, total_floors, price_per_m2, total_price,
                                        developer, contact_phone, has_tech_passport, has_renovation_permit,
                                        created_date, updated_date, author_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'), data.get('description', ''), data.get('address', ''),
            data.get('lat', 38.5598), data.get('lng', 68.7870),
            data.get('construction_type', 'новостройка'), data.get('district', 'н.Сино'),
            data.get('area', 0), data.get('rooms', 0), data.get('windows', 0),
            data.get('floor', 0), data.get('total_floors', 0), data.get('price_per_m2', 0),
            data.get('total_price', 0), data.get('developer', ''), data.get('contact_phone', ''),
            data.get('has_tech_passport', 'нет'), data.get('has_renovation_permit', 'нет'),
            datetime.now().isoformat(), datetime.now().isoformat(), session['user_id']
        ))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Error add_realty_object: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/objects/<int:object_id>', methods=['PUT'])
@login_required
@admin_required
def update_realty_object(object_id):
    """Таҳрир кардани объект"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE realty_objects SET 
                name = ?, description = ?, address = ?, lat = ?, lng = ?,
                construction_type = ?, district = ?, area = ?, rooms = ?, windows = ?,
                floor = ?, total_floors = ?, price_per_m2 = ?, total_price = ?,
                developer = ?, contact_phone = ?, has_tech_passport = ?, has_renovation_permit = ?,
                updated_date = ?
            WHERE id = ?
        ''', (
            data.get('name'), data.get('description', ''), data.get('address', ''),
            data.get('lat', 38.5598), data.get('lng', 68.7870),
            data.get('construction_type', 'новостройка'), data.get('district', 'н.Сино'),
            data.get('area', 0), data.get('rooms', 0), data.get('windows', 0),
            data.get('floor', 0), data.get('total_floors', 0), data.get('price_per_m2', 0),
            data.get('total_price', 0), data.get('developer', ''), data.get('contact_phone', ''),
            data.get('has_tech_passport', 'нет'), data.get('has_renovation_permit', 'нет'),
            datetime.now().isoformat(), object_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error update_realty_object: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/objects/<int:object_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_realty_object(object_id):
    """Нест кардани объект ва ҳамаи блокҳо, прайсҳо, планировкаҳо"""
    conn = get_db()
    try:
        # Нест кардани блокҳо (каскадӣ)
        conn.execute('DELETE FROM realty_blocks WHERE object_id = ?', (object_id,))
        conn.execute('DELETE FROM realty_pricing WHERE object_id = ?', (object_id,))
        conn.execute('DELETE FROM realty_layouts WHERE object_id = ?', (object_id,))
        conn.execute('DELETE FROM realty_objects WHERE id = ?', (object_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error delete_realty_object: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# -------------------- BLOCKS --------------------
@app.route('/api/realty/objects/<int:object_id>/blocks', methods=['GET'])
@login_required
def get_realty_blocks(object_id):
    """Гирифтани блокҳои объект"""
    conn = get_db()
    blocks = conn.execute('''
        SELECT * FROM realty_blocks WHERE object_id = ? ORDER BY order_index ASC
    ''', (object_id,)).fetchall()
    conn.close()
    return jsonify([dict(block) for block in blocks])

@app.route('/api/realty/blocks', methods=['POST'])
@login_required
@admin_required
def add_realty_block():
    """Илова кардани блоки нав"""
    data = request.json
    conn = get_db()
    try:
        # Санҷиши тартиби блок
        max_order = conn.execute('SELECT MAX(order_index) as max_order FROM realty_blocks WHERE object_id = ?', 
                                  (data['object_id'],)).fetchone()
        order_index = (max_order['max_order'] or 0) + 1
        
        cursor = conn.execute('''
            INSERT INTO realty_blocks (object_id, name, code, order_index, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['object_id'], data['name'], data.get('code', ''), order_index, datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/blocks/<int:block_id>', methods=['PUT'])
@login_required
@admin_required
def update_realty_block(block_id):
    """Таҳрир кардани блок"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE realty_blocks SET name = ?, code = ?, order_index = ?
            WHERE id = ?
        ''', (data['name'], data.get('code', ''), data.get('order_index', 0), block_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/blocks/<int:block_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_realty_block(block_id):
    """Нест кардани блок"""
    conn = get_db()
    try:
        # Нест кардани прайсҳои марбут ба блок
        conn.execute('DELETE FROM realty_pricing WHERE block_id = ?', (block_id,))
        conn.execute('DELETE FROM realty_blocks WHERE id = ?', (block_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# -------------------- PRICING --------------------
@app.route('/api/realty/pricing', methods=['GET'])
@login_required
def get_realty_pricing():
    """Гирифтани прайс-листҳо"""
    object_id = request.args.get('object_id')
    block_id = request.args.get('block_id')
    
    conn = get_db()
    query = 'SELECT * FROM realty_pricing WHERE 1=1'
    params = []
    
    if object_id:
        query += ' AND object_id = ?'
        params.append(int(object_id))
    if block_id:
        query += ' AND block_id = ?'
        params.append(int(block_id))
    
    query += ' ORDER BY block_id ASC, floor_number ASC'
    pricing = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(p) for p in pricing])

@app.route('/api/realty/pricing', methods=['POST'])
@login_required
@admin_required
def add_realty_pricing():
    """Илова кардани прайс (нарх барои этаж ва процент)"""
    data = request.json
    conn = get_db()
    try:
        # Санҷиши вуҷуди сабти такрорӣ
        existing = conn.execute('''
            SELECT id FROM realty_pricing 
            WHERE object_id = ? AND block_id = ? AND floor_number = ? AND percent_value = ?
        ''', (data['object_id'], data.get('block_id'), data['floor_number'], data['percent_value'])).fetchone()
        
        if existing:
            # Агар мавҷуд бошад, нав мекунем
            conn.execute('''
                UPDATE realty_pricing SET 
                    floor_range_start = ?, floor_range_end = ?,
                    price_usd = ?, price_tjs = ?, currency = ?, updated_date = ?
                WHERE id = ?
            ''', (data.get('floor_range_start'), data.get('floor_range_end'),
                  data.get('price_usd', 0), data.get('price_tjs', 0),
                  data.get('currency', 'USD'), datetime.now().isoformat(), existing['id']))
        else:
            # Сабти нав
            conn.execute('''
                INSERT INTO realty_pricing (object_id, block_id, floor_number, floor_range_start, floor_range_end,
                                            percent_value, price_usd, price_tjs, currency, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['object_id'], data.get('block_id'), data['floor_number'],
                  data.get('floor_range_start'), data.get('floor_range_end'),
                  data['percent_value'], data.get('price_usd', 0), data.get('price_tjs', 0),
                  data.get('currency', 'USD'), datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error add_realty_pricing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/pricing/<int:pricing_id>', methods=['PUT'])
@login_required
@admin_required
def update_realty_pricing(pricing_id):
    """Таҳрир кардани прайс"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE realty_pricing SET 
                floor_number = ?, floor_range_start = ?, floor_range_end = ?,
                percent_value = ?, price_usd = ?, price_tjs = ?, currency = ?, updated_date = ?
            WHERE id = ?
        ''', (data['floor_number'], data.get('floor_range_start'), data.get('floor_range_end'),
              data['percent_value'], data.get('price_usd', 0), data.get('price_tjs', 0),
              data.get('currency', 'USD'), datetime.now().isoformat(), pricing_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/pricing/<int:pricing_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_realty_pricing(pricing_id):
    """Нест кардани прайс"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM realty_pricing WHERE id = ?', (pricing_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

# -------------------- LAYOUTS (ПЛАНИРОВКИ) --------------------
@app.route('/api/realty/layouts', methods=['GET'])
@login_required
def get_realty_layouts():
    """Гирифтани планировкаҳо"""
    object_id = request.args.get('object_id')
    conn = get_db()
    if object_id:
        layouts = conn.execute('''
            SELECT * FROM realty_layouts WHERE object_id = ? ORDER BY room_type ASC, area ASC
        ''', (int(object_id),)).fetchall()
    else:
        layouts = conn.execute('SELECT * FROM realty_layouts ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(layout) for layout in layouts])

@app.route('/api/realty/layouts', methods=['POST'])
@login_required
@admin_required
def add_realty_layout():
    """Илова кардани планировкаи нав"""
    data = request.json
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO realty_layouts (object_id, room_type, windows_count, area, price_usd, price_tjs, description, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['object_id'], data['room_type'], data['windows_count'], data['area'],
              data.get('price_usd', 0), data.get('price_tjs', 0), data.get('description', ''),
              datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/layouts/<int:layout_id>', methods=['PUT'])
@login_required
@admin_required
def update_realty_layout(layout_id):
    """Таҳрир кардани планировка"""
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            UPDATE realty_layouts SET 
                room_type = ?, windows_count = ?, area = ?, 
                price_usd = ?, price_tjs = ?, description = ?
            WHERE id = ?
        ''', (data['room_type'], data['windows_count'], data['area'],
              data.get('price_usd', 0), data.get('price_tjs', 0), data.get('description', ''), layout_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/realty/layouts/<int:layout_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_realty_layout(layout_id):
    """Нест кардани планировка"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM realty_layouts WHERE id = ?', (layout_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()
        
# ================ ИЛОВА БАРОИ ЗАПУСКИ OBJEKT.PY ================
def run_objekt_backend():
    """Запуск бекенди objekt.py дар як потоки алоҳида"""
    import subprocess
    import sys
    import os
    
    # Санҷидани он ки objekt.py аллакай дар ҷараён аст
    try:
        # Кӯшиши пайвастшавӣ ба порти objekt.py
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 5002))
        sock.close()
        
        if result != 0:
            # Порт кушода нест, запуск мекунем
            print("🔄 Запуски бекенди objekt.py...")
            subprocess.Popen([sys.executable, 'objekt.py'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            print("✅ Бекенди objekt.py дар порти 5002 оғоз шуд")
        else:
            print("✅ Бекенди objekt.py аллакай кор мекунад")
    except Exception as e:
        print(f"⚠️ Хатогӣ дар запуски objekt.py: {e}")

# Запуск бекенди objekt.py (агар ҳанӯз оғоз нашуда бошад)
try:
    run_objekt_backend()
except Exception as e:
    print(f"⚠️ Объект API оғоз нашуд: {e}")     
        


# ================ STATIC FILES ================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join('uploads', filename))


if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Сервер запущен! Доступные страницы:")
    print("  - http://127.0.0.1:5000/")
    print("  - http://127.0.0.1:5000/login")
    print("  - http://127.0.0.1:5000/admin (только для админа)")
    print("  - http://127.0.0.1:5000/zadacha")
    print("  - http://127.0.0.1:5000/zayavka")
    print("  - http://127.0.0.1:5000/chat")
    print("  - http://127.0.0.1:5000/posts")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=80)