import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'storage_service.dart';

@pragma('vm:entry-point')
void onStart(ServiceInstance service) async {
  final storage = StorageService();
  await storage.init();

  Timer.periodic(const Duration(seconds: 15), (timer) async {
    if (!storage.isTracking) return;

    final topic = storage.ntfyTopic;
    if (topic.isEmpty) return;

    try {
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      final payload = {
        "id": "tracker_1",
        "name": storage.trackerName,
        "lat": position.latitude,
        "lon": position.longitude,
        "timestamp": DateTime.now().millisecondsSinceEpoch,
        "battery": 100, // mock or implement battery package
        "isCharging": false,
      };

      await http.post(
        Uri.parse('https://ntfy.sh/$topic'),
        body: jsonEncode(payload),
        headers: {
          'Title': 'Location Update',
        },
      );
    } catch (e) {
      debugPrint("Error sending location: $e");
    }
  });

  service.on('stopService').listen((event) {
    service.stopSelf();
  });
}

class AppLocationService {
  static Future<void> initializeService() async {
    final service = FlutterBackgroundService();

    await service.configure(
      androidConfiguration: AndroidConfiguration(
        onStart: onStart,
        autoStart: false,
        isForegroundMode: true,
        notificationChannelId: 'proximity_tracker_channel',
        initialNotificationTitle: 'Proximity Tracker',
        initialNotificationContent: 'Tracking location in background',
        foregroundServiceNotificationId: 888,
      ),
      iosConfiguration: IosConfiguration(
        autoStart: false,
        onForeground: onStart,
        onBackground: onIosBackground,
      ),
    );
  }

  @pragma('vm:entry-point')
  static Future<bool> onIosBackground(ServiceInstance service) async {
    return true;
  }
}
