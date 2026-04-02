import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'services/location_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final storage = StorageService();
  await storage.init();

  await AppLocationService.initializeService();

  runApp(const ProximityTrackerApp());
}



class ProximityTrackerApp extends StatelessWidget {
  const ProximityTrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Proximity Tracker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A14),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}
