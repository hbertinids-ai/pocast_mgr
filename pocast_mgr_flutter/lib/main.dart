import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(const MyApp());


class Episode {
  final String title;
  final String scheduledDate;
  final String type;

  Episode({required this.title, required this.scheduledDate, required this.type});

  factory Episode.fromJson(Map<String, dynamic> json) {
    return Episode(
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

class MyApp extends StatelessWidget {
  const MyApp({super.key});

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

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Podcast Episodes',
      home: Scaffold(
        appBar: AppBar(title: const Text('Podcast Episodes')),
        drawer: Drawer(
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              const DrawerHeader(
                decoration: BoxDecoration(
                  color: Color(0xFF4A90E2),
                ),
                child: Text('Menu', style: TextStyle(color: Colors.white, fontSize: 24)),
              ),
              ListTile(
                leading: const Icon(Icons.library_music),
                title: const Text('Episódios'),
                onTap: () {
                  Navigator.pop(context);
                  // This is the main page, so just close the drawer
                },
              ),
            ],
          ),
        ),
        body: FutureBuilder<List<Episode>>(
          future: fetchEpisodes(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Error: ${snapshot.error}'));
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(child: Text('No episodes found.'));
            } else {
              return Container(
                color: const Color(0xFFF0F0F0),
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                  itemCount: snapshot.data!.length,
                  separatorBuilder: (context, idx) => const SizedBox(height: 18),
                  itemBuilder: (context, idx) {
                    final ep = snapshot.data![idx];
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
                                  Text(
                                    ep.title,
                                    style: TextStyle(
                                      color: getTypeColor(ep.type),
                                      fontWeight: FontWeight.bold,
                                      fontSize: 20,
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
                ),
              );
            }
          },
        ),
      ),
    );
  }
}
