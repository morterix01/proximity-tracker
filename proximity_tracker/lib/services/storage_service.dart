import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  String get trackerName => _prefs.getString('trackerName') ?? 'Unknown Person';
  Future<void> setTrackerName(String name) async {
    await _prefs.setString('trackerName', name);
  }

  String get ntfyTopic => _prefs.getString('ntfyTopic') ?? '';
  Future<void> setNtfyTopic(String topic) async {
    await _prefs.setString('ntfyTopic', topic);
  }

  bool get isTracking => _prefs.getBool('isTracking') ?? false;
  Future<void> setTracking(bool tracking) async {
    await _prefs.setBool('isTracking', tracking);
  }
}
