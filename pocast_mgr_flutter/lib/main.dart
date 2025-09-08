import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Podcast Manager',
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  static const List<Widget> _pages = <Widget>[
    PodcastEpisodesPage(),
    SimpleCalendarPage(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Podcast Manager')),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.library_music),
            label: 'Episodes',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_today),
            label: 'Calendar',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: const Color(0xFF4A90E2),
        onTap: _onItemTapped,
      ),
    );
  }
}

class Episode {
  final int id;
  final String title;
  final String scheduledDate;
  final String type;

  Episode({required this.id, required this.title, required this.scheduledDate, required this.type});

  factory Episode.fromJson(Map<String, dynamic> json) {
    return Episode(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      scheduledDate: json['scheduled_date'] ?? '',
      type: json['type'] ?? '',
    );
  }
}

Color getTypeColor(String type) {
  switch (type.toLowerCase()) {
    case 'solo':
      return const Color(0xFF4A90E2); // blue
    case 'convidado':
    case 'guest':
      return const Color(0xFFF5A623); // orange
    default:
      return const Color(0xFF555555); // gray
  }
}

Future<List<Episode>> fetchEpisodes() async {
  final response = await http.get(Uri.parse('http://127.0.0.1:5010/api/all_episodes'));
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    final episodes = data['episodes'] as List;
    return episodes.map((e) => Episode.fromJson(e)).toList();
  } else {
    throw Exception('Failed to load episodes');
  }
}

class PodcastEpisodesPage extends StatelessWidget {
  const PodcastEpisodesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Episode>>(
      future: fetchEpisodes(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: \\${snapshot.error}'));
        } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(child: Text('No episodes found.'));
        } else {
          final episodes = snapshot.data!;
          return ListView.separated(
            padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
            itemCount: episodes.length,
            separatorBuilder: (context, idx) => const SizedBox(height: 18),
            itemBuilder: (context, idx) {
              final ep = episodes[idx];
              return Card(
                elevation: 4,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                child: Padding(
                  padding: const EdgeInsets.all(18.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        ep.type.toLowerCase() == 'solo'
                            ? Icons.person
                            : Icons.group,
                        color: getTypeColor(ep.type),
                        size: 32,
                      ),
                      const SizedBox(width: 18),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            GestureDetector(
                              onTap: () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (context) => EpisodeDetailPage(episodeId: ep.id),
                                  ),
                                );
                              },
                              child: Text(
                                ep.title,
                                style: TextStyle(
                                  color: getTypeColor(ep.type),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 20,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                Icon(Icons.calendar_today, size: 16, color: Colors.grey[600]),
                                const SizedBox(width: 6),
                                Text(
                                  ep.scheduledDate.replaceAll('T', ' '),
                                  style: TextStyle(color: Colors.grey[700], fontSize: 15),
                                ),
                              ],
                            ),
                            if (ep.type.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 8.0),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: getTypeColor(ep.type).withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    ep.type,
                                    style: TextStyle(
                                      color: getTypeColor(ep.type),
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        }
      },
    );
  }
}

class EpisodeDetailPage extends StatelessWidget {
  final int episodeId;
  const EpisodeDetailPage({super.key, required this.episodeId});

  Future<Map<String, dynamic>> fetchEpisodeDetail() async {
    final response = await http.get(Uri.parse('http://127.0.0.1:5010/api/view_episode/$episodeId'));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['episode'] ?? {};
    } else {
      throw Exception('Failed to load episode detail');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Episode Detail')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: fetchEpisodeDetail(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: \\${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('Episode not found.'));
          } else {
            final ep = snapshot.data!;
            return Center(
              child: Card(
                elevation: 6,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                margin: const EdgeInsets.all(24),
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        ep['title'] ?? '',
                        style: TextStyle(
                          color: getTypeColor(ep['type'] ?? ''),
                          fontWeight: FontWeight.bold,
                          fontSize: 26,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Icon(Icons.calendar_today, size: 18, color: Colors.grey[600]),
                          const SizedBox(width: 8),
                          Text(
                            (ep['scheduled_date'] ?? '').replaceAll('T', ' '),
                            style: TextStyle(color: Colors.grey[700], fontSize: 16),
                          ),
                        ],
                      ),
                      if ((ep['type'] ?? '').isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 14.0),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: getTypeColor(ep['type'] ?? '').withOpacity(0.18),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              ep['type'] ?? '',
                              style: TextStyle(
                                color: getTypeColor(ep['type'] ?? ''),
                                fontWeight: FontWeight.w600,
                                fontSize: 15,
                              ),
                            ),
                          ),
                        ),
                      if ((ep['guest'] ?? '').isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10.0),
                          child: Text(
                            'Guest: ' + ep['guest'],
                            style: const TextStyle(fontSize: 16, color: Colors.black87),
                          ),
                        ),
                      if ((ep['theme'] ?? '').isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10.0),
                          child: Text(
                            'Theme: ' + ep['theme'],
                            style: const TextStyle(fontSize: 16, color: Colors.black87),
                          ),
                        ),
                      if ((ep['description'] ?? '').isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10.0),
                          child: Text(
                            'Description: ' + ep['description'],
                            style: const TextStyle(fontSize: 16, color: Colors.black87),
                          ),
                        ),
                      if ((ep['announcement'] ?? '').isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10.0),
                          child: Text(
                            'Announcement: ' + ep['announcement'],
                            style: const TextStyle(fontSize: 16, color: Colors.black87),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            );
          }
        },
      ),
    );
  }
}

class SimpleCalendarPage extends StatefulWidget {
  const SimpleCalendarPage({super.key});
  @override
  State<SimpleCalendarPage> createState() => _SimpleCalendarPageState();
}

class _SimpleCalendarPageState extends State<SimpleCalendarPage> {
  late DateTime _currentMonth;
  late Future<List<Episode>> _episodesFuture;

  @override
  void initState() {
    super.initState();
    _currentMonth = DateTime.now();
    _episodesFuture = fetchEpisodes();
  }

  void _goToMonth(DateTime month) {
    setState(() {
      _currentMonth = month;
    });
  }

  List<DateTime> _daysInMonth(DateTime month) {
    final days = <DateTime>[];
    for (int i = 0; i < DateUtils.getDaysInMonth(month.year, month.month); i++) {
      days.add(DateTime(month.year, month.month, i + 1));
    }
    return days;
  }

  Color _getDayColor(List<Episode> episodes) {
    if (episodes.isEmpty) return Colors.white;
    final hasGuest = episodes.any((ep) => ep.type.toLowerCase() == 'guest' || ep.type.toLowerCase() == 'convidado');
    if (hasGuest) return const Color(0xFFF5A623); // orange
    final allSolo = episodes.every((ep) => ep.type.toLowerCase() == 'solo');
    if (allSolo) return const Color(0xFF4A90E2); // blue
    return Colors.white;
  }

  @override
  Widget build(BuildContext context) {
    final days = _daysInMonth(_currentMonth);
    return FutureBuilder<List<Episode>>(
      future: _episodesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: \\${snapshot.error}'));
        } else if (!snapshot.hasData) {
          return const Center(child: Text('No episodes found.'));
        }
        final episodes = snapshot.data!;
        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12.0, horizontal: 8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_left),
                    onPressed: () => _goToMonth(DateTime(_currentMonth.year, _currentMonth.month - 1, 1)),
                  ),
                  Text('${_currentMonth.year} - ${_currentMonth.month.toString().padLeft(2, '0')}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(
                    icon: const Icon(Icons.arrow_right),
                    onPressed: () => _goToMonth(DateTime(_currentMonth.year, _currentMonth.month + 1, 1)),
                  ),
                ],
              ),
            ),
            GridView.count(
              crossAxisCount: 7,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: days.map((day) {
                final dayStr = day.toIso8601String().substring(0, 10);
                final dayEpisodes = episodes.where((ep) => ep.scheduledDate.startsWith(dayStr)).toList();
                return Builder(
                  builder: (cellContext) => GestureDetector(
                    onTap: () {
                      if (dayEpisodes.isNotEmpty) {
                        Navigator.of(cellContext).push(
                          MaterialPageRoute(
                            builder: (context) => EpisodeListForDayPage(date: dayStr, episodes: dayEpisodes),
                          ),
                        );
                      }
                    },
                    child: Container(
                      margin: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: _getDayColor(dayEpisodes),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey[400]!),
                      ),
                      child: Center(child: Text(day.day.toString(), style: const TextStyle(fontSize: 16))),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        );
      },
    );
  }
}

class EpisodeListForDayPage extends StatelessWidget {
  final String date;
  final List<Episode> episodes;
  const EpisodeListForDayPage({super.key, required this.date, required this.episodes});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Episodes for $date')),
      body: ListView.builder(
        itemCount: episodes.length,
        itemBuilder: (context, idx) {
          final ep = episodes[idx];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            child: ListTile(
              title: Text(ep.title),
              subtitle: Text('${ep.type} • ${ep.scheduledDate}'),
            ),
          );
        },
      ),
    );
  }
}
