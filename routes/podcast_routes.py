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
            cursor.execute("SELECT scheduled_date, type, title FROM episodes WHERE scheduled_date LIKE ?", (f'{year}-{month:02d}%',))
            episodes = cursor.fetchall()
        except sqlite3.OperationalError:
            episodes = []
        episode_map = {}
        for edate, etype, etitle in episodes:
            if edate:
                d = edate.split('T')[0]
                episode_map[d] = {'type': etype, 'title': etitle}
        cal = pycalendar.Calendar(firstweekday=0)
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            week_data = []
            for d in week:
                info = 'none'
                episode_detail = ''
                if d.month == month:
                    ep = episode_map.get(d.strftime('%Y-%m-%d'))
                    if ep:
                        info = 'solo' if ep['type'] and ep['type'].lower() == 'solo' else 'guest' if ep['type'] else 'none'
                        episode_detail = ep['title']
                week_data.append({'date': d if d.month == month else None, 'info': info, 'episode': episode_detail})
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT scheduled_date, title FROM episodes ORDER BY scheduled_date ASC')
        episodes = [{'scheduled_date': sd, 'title': t} for sd, t in cursor.fetchall()]
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
