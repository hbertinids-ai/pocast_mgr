from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import calendar as pycalendar
from datetime import datetime, timedelta, date
import locale

podcast_bp = Blueprint('podcast', __name__)
DB_PATH = 'database.db'

@podcast_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    results = []
    if query:
        cursor.execute("SELECT id, scheduled_date, title, type FROM episodes WHERE title LIKE ? OR guest LIKE ? OR theme LIKE ? OR description LIKE ? ORDER BY scheduled_date ASC", (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        results = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
    conn.close()
    return render_template('search_results.html', query=query, results=results)
DB_PATH = 'database.db'
@podcast_bp.route('/add_episode', methods=['GET', 'POST'])
def add_episode_global():
    from datetime import datetime
    # Get date from query string, fallback to now
    date_str = request.args.get('date')
    try:
        if date_str:
            # Accept both YYYY-MM-DD and YYYY-MM-DDTHH:MM
            if 'T' in date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            dt = datetime.now()
        scheduled_date = dt.strftime('%Y-%m-%dT%H:%M')
    except Exception:
        scheduled_date = datetime.now().strftime('%Y-%m-%dT%H:%M')

    if request.method == 'POST':
        title = request.form['title']
        scheduled_date = request.form['scheduled_date']
        type_ = request.form.get('type', '')
        guest = request.form.get('guest', '')
        theme = request.form.get('theme', '')
        description = request.form.get('description', '')
        announcement = request.form.get('announcement', '')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO episodes (scheduled_date, title, type, guest, theme, description, announcement) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (scheduled_date, title, type_, guest, theme, description, announcement))
        conn.commit()
        conn.close()
        return redirect(url_for('podcast.all_episodes'))
    return render_template('add_episode.html', scheduled_date=scheduled_date)


@podcast_bp.route('/add', methods=['POST'])
def add_podcast():
    title = request.form['title']
    host = request.form['host']
    description = request.form.get('description', '')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO podcasts (title, host, description) VALUES (?, ?, ?)', (title, host, description))
    conn.commit()
    conn.close()
    return redirect(url_for('podcast.index'))

def get_calendar_data(offset=0, jump_month=None, jump_year=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = date.today()
    months = []
    if jump_month and jump_year:
        first_day = date(int(jump_year), int(jump_month), 1)
        offset = 0
    else:
        first_day = today.replace(day=1) + timedelta(days=32*offset)
        first_day = first_day.replace(day=1)
    for m in range(2):
        month_start = (first_day + timedelta(days=32*m)).replace(day=1)
        year, month = month_start.year, month_start.month
        month_name = month_start.strftime('%B')
        try:
            cursor.execute("SELECT id, scheduled_date, type, title FROM episodes WHERE scheduled_date LIKE ?", (f'{year}-{month:02d}%',))
            episodes = cursor.fetchall()
        except sqlite3.OperationalError:
            episodes = []
        episode_map = {}
        for eid, edate, etype, etitle in episodes:
            if edate:
                d = edate.split('T')[0]
                episode_map[d] = {'id': eid, 'type': etype, 'title': etitle}
        cal = pycalendar.Calendar(firstweekday=0)
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            week_data = []
            for d in week:
                info = 'none'
                episode_detail = ''
                episode_id = None
                if d.month == month:
                    ep = episode_map.get(d.strftime('%Y-%m-%d'))
                    if ep:
                        info = 'solo' if ep['type'] and ep['type'].lower() == 'solo' else 'guest' if ep['type'] else 'none'
                        episode_detail = ep['title']
                        episode_id = ep['id']
                week_data.append({'date': d if d.month == month else None, 'info': info, 'episode': episode_detail, 'episode_id': episode_id})
            weeks.append(week_data)
        months.append({'name': month_name, 'year': year, 'num': month, 'weeks': weeks})
    conn.close()
    return months

@podcast_bp.context_processor
def inject_calendar():
    from datetime import date
    today = date.today()
    offset = 0
    nav = request.args.get('calnav')
    jump_month = request.args.get('jump_month')
    jump_year = request.args.get('jump_year')
    if nav == 'prev':
        offset = int(request.args.get('offset', 0)) - 1
    elif nav == 'next':
        offset = int(request.args.get('offset', 0)) + 1
    elif nav == 'jump' and jump_month and jump_year:
        return {'calendar_months': get_calendar_data(0, jump_month, jump_year), 'offset': 0}
    else:
        offset = int(request.args.get('offset', 0))
    calendar_months = get_calendar_data(offset)
    return dict(calendar_months=calendar_months, offset=offset, today=today)

@podcast_bp.route('/all_episodes')
def all_episodes():
    date_filter = request.args.get('date')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if date_filter:
            cursor.execute('SELECT id, scheduled_date, title, type FROM episodes WHERE scheduled_date LIKE ? ORDER BY scheduled_date ASC', (f'{date_filter}%',))
        else:
            cursor.execute('SELECT id, scheduled_date, title, type FROM episodes ORDER BY scheduled_date ASC')
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
    except sqlite3.OperationalError:
        episodes = []
    conn.close()
    return render_template('all_episodes.html', episodes=episodes)

# Show podcast details and episodes
@podcast_bp.route('/podcast/<int:id>')
def podcast_detail(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, host, description FROM podcasts WHERE id = ?', (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return render_template('podcast_detail.html', podcast=None, episodes=[])
    podcast = {'id': row[0], 'title': row[1], 'host': row[2], 'description': row[3]}
    try:
        cursor.execute('SELECT id, scheduled_date, title, type, guest, theme, description, announcement FROM episodes WHERE podcast_id = ? ORDER BY scheduled_date ASC', (id,))
        episodes = [
            {
                'id': eid,
                'scheduled_date': sd,
                'title': t,
                'type': tp,
                'guest': g,
                'theme': th,
                'description': desc,
                'announcement': ann
            }
            for eid, sd, t, tp, g, th, desc, ann in cursor.fetchall()
        ]
    except sqlite3.OperationalError:
        episodes = []
    conn.close()
    return render_template('podcast_detail.html', podcast=podcast, episodes=episodes)

@podcast_bp.route('/episode/<int:id>/edit', methods=['GET', 'POST'])
def edit_episode(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        scheduled_date = request.form['scheduled_date']
        guest = request.form.get('guest', '')
        theme = request.form.get('theme', '')
        description = request.form.get('description', '')
        announcement = request.form.get('announcement', '')
        # Auto-set type
        if guest.strip():
            type_ = 'Convidado'
        else:
            type_ = 'Solo'
        cursor.execute('''UPDATE episodes SET title=?, scheduled_date=?, type=?, guest=?, theme=?, description=?, announcement=? WHERE id=?''',
            (title, scheduled_date, type_, guest, theme, description, announcement, id))
        conn.commit()
        conn.close()
        return redirect(url_for('podcast.episode_detail', id=id))
    cursor.execute('SELECT id, podcast_id, scheduled_date, title, type, guest, theme, description, announcement FROM episodes WHERE id=?', (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return render_template('edit_episode.html', episode=None)
    episode = {
        'id': row[0],
        'podcast_id': row[1],
        'scheduled_date': row[2],
        'title': row[3],
        'type': row[4],
        'guest': row[5],
        'theme': row[6],
        'description': row[7],
        'announcement': row[8]
    }
    return render_template('edit_episode.html', episode=episode)

@podcast_bp.route('/episode/<int:id>')
def episode_detail(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, podcast_id, scheduled_date, title, type, guest, theme, description, announcement FROM episodes WHERE id=?', (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return render_template('episode_detail.html', episode=None)
    episode = {
        'id': row[0],
        'podcast_id': row[1],
        'scheduled_date': row[2],
        'title': row[3],
        'type': row[4],
        'guest': row[5],
        'theme': row[6],
        'description': row[7],
        'announcement': row[8]
    }
    return render_template('episode_detail.html', episode=episode)

@podcast_bp.route('/episode/<int:id>/delete', methods=['POST'])
def delete_episode(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT podcast_id FROM episodes WHERE id=?', (id,))
    row = cursor.fetchone()
    podcast_id = row[0] if row else 1
    cursor.execute('DELETE FROM episodes WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('podcast.podcast_detail', id=podcast_id))

@podcast_bp.route('/podcast/<int:id>/edit', methods=['GET', 'POST'])
def edit_podcast(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        host = request.form['host']
        description = request.form.get('description', '')
        cursor.execute('UPDATE podcasts SET title=?, host=?, description=? WHERE id=?', (title, host, description, id))
        conn.commit()
        conn.close()
        return redirect(url_for('podcast.podcast_detail', id=id))
    cursor.execute('SELECT id, title, host, description FROM podcasts WHERE id=?', (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return render_template('edit_podcast.html', podcast=None)
    podcast = {'id': row[0], 'title': row[1], 'host': row[2], 'description': row[3]}
    return render_template('edit_podcast.html', podcast=podcast)

@podcast_bp.route('/podcast/<int:id>/delete', methods=['POST'])
def delete_podcast(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM podcasts WHERE id=?', (id,))
    cursor.execute('DELETE FROM episodes WHERE podcast_id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('podcast.index'))

@podcast_bp.route('/podcast/<int:podcast_id>/add_episode', methods=['GET', 'POST'])
def add_episode(podcast_id):
    if request.method == 'POST':
        title = request.form['title']
        scheduled_date = request.form['scheduled_date']
        type_ = request.form.get('type', '')
        guest = request.form.get('guest', '')
        theme = request.form.get('theme', '')
        description = request.form.get('description', '')
        announcement = request.form.get('announcement', '')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO episodes (podcast_id, scheduled_date, title, type, guest, theme, description, announcement) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (podcast_id, scheduled_date, title, type_, guest, theme, description, announcement))
        conn.commit()
        conn.close()
        return redirect(url_for('podcast.podcast_detail', id=podcast_id))
    return render_template('add_episode.html', podcast_id=podcast_id)

@podcast_bp.route('/calendar_view', methods=['GET', 'POST'])
def calendar_view():
    # import locale
    # locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8') if hasattr(locale, 'LC_TIME') else None
    mode = request.args.get('mode', 'month')
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = date.today().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    episodes = []
    calendar_data = {}
    prev_date = next_date = selected_date
    if mode == 'day':
        dt = datetime.strptime(selected_date, '%Y-%m-%d')
        day_name = dt.strftime('%A')
        day_num = dt.day
        month_name = dt.strftime('%B')
        calendar_data = {'day_name': day_name, 'day_num': day_num, 'month_name': month_name, 'date': selected_date}
        cursor.execute('SELECT id, scheduled_date, title, type FROM episodes WHERE scheduled_date LIKE ?', (f'{selected_date}%',))
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
        prev_date = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (dt + timedelta(days=1)).strftime('%Y-%m-%d')
    elif mode == 'week':
        dt = datetime.strptime(selected_date, '%Y-%m-%d')
        start = dt - timedelta(days=dt.weekday())
        week_num = dt.isocalendar()[1]
        month_name = dt.strftime('%B')
        week_days = [(start + timedelta(days=i)) for i in range(7)]
        calendar_data = {'week_num': week_num, 'month_name': month_name, 'week_days': week_days}
        end = start + timedelta(days=6)
        cursor.execute('SELECT id, scheduled_date, title, type FROM episodes WHERE scheduled_date BETWEEN ? AND ?', (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
        prev_date = (start - timedelta(days=7)).strftime('%Y-%m-%d')
        next_date = (start + timedelta(days=7)).strftime('%Y-%m-%d')
    elif mode == 'year':
        year = int(selected_date[:4])
        months = [date(year, m, 1) for m in range(1,13)]
        calendar_data = {'year': year, 'months': months}
        cursor.execute('SELECT id, scheduled_date, title, type FROM episodes WHERE scheduled_date LIKE ?', (f'{year}%',))
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
        prev_date = f'{year-1}-01-01'
        next_date = f'{year+1}-01-01'
    else:  # month
        year, month = int(selected_date[:4]), int(selected_date[5:7])
        month_name = date(year, month, 1).strftime('%B')
        cal = pycalendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(year, month)
        calendar_data = {'month_name': month_name, 'year': year, 'weeks': weeks}
        cursor.execute('SELECT id, scheduled_date, title, type FROM episodes WHERE scheduled_date LIKE ?', (f'{year}-{str(month).zfill(2)}%',))
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t, 'type': tp} for eid, sd, t, tp in cursor.fetchall()]
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        prev_date = f'{prev_year}-{str(prev_month).zfill(2)}-01'
        next_date = f'{next_year}-{str(next_month).zfill(2)}-01'
    conn.close()
    return render_template('calendar_view.html', mode=mode, selected_date=selected_date, episodes=episodes, calendar_data=calendar_data, prev_date=prev_date, next_date=next_date)

@podcast_bp.route('/update_episode_date', methods=['POST'])
def update_episode_date():
    eid = request.form['episode_id']
    new_date = request.form['new_date']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE episodes SET scheduled_date=? WHERE id=?', (new_date, eid))
    conn.commit()
    conn.close()
    return 'OK'
