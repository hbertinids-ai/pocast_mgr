from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import calendar as pycalendar
from datetime import datetime, timedelta, date

podcast_bp = Blueprint('podcast', __name__)
DB_PATH = 'database.db'

@podcast_bp.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS podcasts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, host TEXT NOT NULL, description TEXT)')
    cursor.execute('SELECT id, title, host, description FROM podcasts')
    podcasts = [{'id': id, 'title': title, 'host': host, 'description': description} for id, title, host, description in cursor.fetchall()]
    conn.close()
    return render_template('index.html', podcasts=podcasts)

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
        months.append({'name': month_name, 'year': year, 'weeks': weeks})
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
            cursor.execute('SELECT id, scheduled_date, title FROM episodes WHERE scheduled_date LIKE ? ORDER BY scheduled_date ASC', (f'{date_filter}%',))
        else:
            cursor.execute('SELECT id, scheduled_date, title FROM episodes ORDER BY scheduled_date ASC')
        episodes = [{'id': eid, 'scheduled_date': sd, 'title': t} for eid, sd, t in cursor.fetchall()]
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
        type_ = request.form.get('type', '')
        guest = request.form.get('guest', '')
        theme = request.form.get('theme', '')
        description = request.form.get('description', '')
        announcement = request.form.get('announcement', '')
        cursor.execute('''UPDATE episodes SET title=?, scheduled_date=?, type=?, guest=?, theme=?, description=?, announcement=? WHERE id=?''',
            (title, scheduled_date, type_, guest, theme, description, announcement, id))
        conn.commit()
        conn.close()
        return redirect(url_for('podcast.podcast_detail', id=request.form.get('podcast_id', 1)))
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
