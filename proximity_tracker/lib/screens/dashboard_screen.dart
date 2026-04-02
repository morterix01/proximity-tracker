import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import '../services/storage_service.dart';
import '../widgets/glass_card.dart';
import '../widgets/neon_button.dart';
import 'settings_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final StorageService _storage = StorageService();
  bool isRunning = false;

  @override
  void initState() {
    super.initState();
    isRunning = _storage.isTracking;
  }

  Future<void> _toggleTracking() async {
    final service = FlutterBackgroundService();

    if (isRunning) {
      await _storage.setTracking(false);
      service.invoke("stopService");
      setState(() {
        isRunning = false;
      });
    } else {
      // Validate settings
      if (_storage.ntfyTopic.isEmpty || _storage.trackerName.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Configura Nome e Topic NTFY nelle impostazioni prima di iniziare.')),
        );
        return;
      }

      await _storage.setTracking(true);
      service.startService();
      setState(() {
        isRunning = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A14),
      body: Stack(
        children: [
          // Modern background gradient blobs
          Positioned(
            top: -100,
            left: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                color: const Color(0xFF00F2FF).withOpacity(0.15),
                shape: BoxShape.circle,
              ),
            ),
          ),
          Positioned(
            bottom: -50,
            right: -100,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                color: const Color(0xFFFF4D4D).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
            ),
          ),
          // Blur layer to create glass effect over background blobs
          Positioned.fill(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
              child: const SizedBox(),
            ),
          ),
          
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 25.0, vertical: 15.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'PROXIMITY TRACKER',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.5,
                      color: Color(0xFF00F2FF),
                    ),
                  ),
                  const SizedBox(height: 30),
                  GlassCard(
                    height: 150,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          isRunning ? "TRACCIAMENTO ATTIVO" : "TRACCIAMENTO INATTIVO",
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          "Nome: ${_storage.trackerName}",
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                          ),
                        ),
                        Text(
                          "Topic: ${_storage.ntfyTopic}",
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  NeonButton(
                    text: isRunning ? 'STOP' : 'START',
                    baseColor: isRunning
                        ? const Color(0xFFFF4D4D)
                        : const Color(0xFF00F2FF),
                    onPressed: _toggleTracking,
                  ),
                  const SizedBox(height: 15),
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: Colors.white24, width: 1.5),
                      color: Colors.white.withOpacity(0.03),
                    ),
                    child: TextButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const SettingsScreen()),
                        ).then((_) => setState(() {})); 
                      },
                      icon: const Icon(Icons.settings, color: Colors.white70),
                      label: const Text(
                        'IMPOSTAZIONI',
                        style: TextStyle(
                          color: Colors.white, 
                          fontSize: 18, 
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                        ),
                      ),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        )
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
