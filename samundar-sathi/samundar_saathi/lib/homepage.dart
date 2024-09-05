import 'dart:math' as math;
import 'dart:math';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'dart:async';
import 'package:samundar_saathi/beachdetail.dart';
import 'package:samundar_saathi/profile.dart'; // Assuming profile.dart exists

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  GoogleMapController? mapController;
  Set<Marker> _markers = {};
  bool isLoading = true;
  int selectedIndex = -1;

  // Firestore instance
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Timer to refresh data every 25 minutes
  Timer? _timer;

  // Initial empty list for locations
  List<Map<String, dynamic>> locations = [];

  @override
  void initState() {
    super.initState();
    _fetchLocationData(); // Fetch locations initially

    // Set timer to fetch data every 25 minutes
    _timer = Timer.periodic(const Duration(minutes: 25), (timer) {
      _fetchLocationData();
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // Cancel the timer when the widget is disposed
    super.dispose();
  }

  Future<void> _fetchLocationData() async {
    try {
      final QuerySnapshot snapshot = await _firestore.collection('samundar_data').get();

      List<Map<String, dynamic>> newLocations = [];

      for (var doc in snapshot.docs) {
        final data = doc.data() as Map<String, dynamic>;

        final safetyReport = data['safety_report'] ?? {};
        final safetyScore = safetyReport['safety_score'];
        final safetyMessage = safetyReport['safety_message'] ?? 'Unknown';
        final reasons = safetyReport['reasons'] ?? [];

        final roundedScore = safetyScore != null ? safetyScore.round() : 0;

        final double lat = data['latitude']?.toDouble() ?? 0.0;
        final double lng = data['longitude']?.toDouble() ?? 0.0;

        newLocations.add({
          "city": data['name'],
          "lat": lat,
          "lng": lng,
          "rating": roundedScore,
          "safetyMessage": safetyMessage,
          "reasons": reasons,
        });
      }

      setState(() {
        locations = newLocations;
        _markers.clear();
        _generateMarkers();
        isLoading = false;
      });
    } catch (e) {
      log("Error fetching data from Firestore: $e" as num);
      setState(() {
        isLoading = false;
      });
    }
  }

  Color _getMarkerColor(int rating) {
    if (rating <= 3) return Colors.red;
    if (rating <= 7) return Colors.yellow;
    return Colors.green;
  }

  Future<void> _generateMarkers() async {
    for (var location in locations) {
      final customMarker = await createMarkerWithRingAndScore(location['rating']);
      _addMarker(
        location['city'],
        LatLng(location['lat'], location['lng']),
        customMarker,
        location['safetyMessage'],
        location['rating'],
        location['reasons'],
      );
    }
  }

  void _addMarker(String city, LatLng position, BitmapDescriptor markerIcon, String safetyMessage, int safetyScore, List<dynamic> reasons) {
    setState(() {
      _markers.add(
        Marker(
          markerId: MarkerId(city),
          position: position,
          icon: markerIcon,
          onTap: () {
            setState(() {
              selectedIndex = locations.indexWhere((location) => location['city'] == city);
            });
          },
        ),
      );
    });
  }

  Future<BitmapDescriptor> createMarkerWithRingAndScore(int rating) async {
    final Color ringColor = _getMarkerColor(rating);

    final ui.PictureRecorder pictureRecorder = ui.PictureRecorder();
    final Canvas canvas = Canvas(pictureRecorder);
    final Paint outerRingPaint = Paint()..color = ringColor;
    final Paint innerCirclePaint = Paint()..color = Colors.blue;

    final double markerSize = 150.0;
    final double ringWidth = 20.0;

    canvas.drawCircle(Offset(markerSize / 2, markerSize / 2), markerSize / 2, outerRingPaint);
    canvas.drawCircle(Offset(markerSize / 2, markerSize / 2), (markerSize / 2) - ringWidth, innerCirclePaint);

    TextPainter painter = TextPainter(
      textDirection: TextDirection.ltr,
      textAlign: TextAlign.center,
    );
    painter.text = TextSpan(
      text: rating.toString(),
      style: TextStyle(
        fontSize: 60.0,
        color: Colors.black,
        fontWeight: FontWeight.bold,
      ),
    );
    painter.layout();
    painter.paint(canvas, Offset(markerSize / 2 - painter.width / 2, markerSize / 2 - painter.height / 2));

    final ui.Image image = await pictureRecorder.endRecording().toImage(markerSize.toInt(), markerSize.toInt());
    final ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final Uint8List imageData = byteData!.buffer.asUint8List();

    return BitmapDescriptor.fromBytes(imageData);
  }

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    if (locations.isNotEmpty) {
      mapController?.animateCamera(
        CameraUpdate.newLatLngBounds(
          LatLngBounds(
            southwest: const LatLng(8.0, 68.0),
            northeast: const LatLng(35.0, 97.0),
          ),
          50,
        ),
      );
    }
  }

  Widget _buildCustomInfoBox(BuildContext context) {
    if (selectedIndex == -1) return const SizedBox();

    final selectedLocation = locations[selectedIndex];
    return Positioned(
      bottom: 20,
      left: 20,
      right: 20,
      child: Card(
        elevation: 10,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        color: Colors.white.withOpacity(0.9),
        child: Padding(
          padding: const EdgeInsets.all(15.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                selectedLocation['city'],
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              Text(
                'Safety Score: ${selectedLocation['rating']}',
                style: const TextStyle(fontSize: 18, color: Colors.black, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              Text(
                selectedLocation['safetyMessage'],
                style: const TextStyle(fontSize: 16, color: Colors.black54),
              ),
              const SizedBox(height: 10),
              Text(
                'Reasons: ${selectedLocation['reasons'].join(", ")}',
                style: const TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => BeachDetailPage(
                        beachName: selectedLocation['city'],
                        safetyMessage: selectedLocation['safetyMessage'],
                        safetyScore: selectedLocation['rating'],
                        reasons: selectedLocation['reasons'],
                      ),
                    ),
                  );
                },
                child: const Text('View More Details'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Bottom Navigation Bar with two icons
  void _onItemTapped(int index) {
    if (index == 0) {
      // Stay on Home Page
    } else if (index == 1) {
      // Navigate to Profile Page
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const ProfilePage()), // Assuming ProfilePage exists
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Samudra Saathi'),
        backgroundColor: Colors.blueAccent,
        elevation: 10,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
        ),
      ),
      body: Stack(
        children: [
          isLoading
              ? const Center(child: CircularProgressIndicator())
              : GoogleMap(
                  onMapCreated: _onMapCreated,
                  initialCameraPosition: const CameraPosition(
                    target: LatLng(20.0, 80.0),
                    zoom: 4.5,
                  ),
                  markers: _markers,
                ),
          _buildCustomInfoBox(context),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.beach_access),
            label: 'Beach',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        currentIndex: 0,
        selectedItemColor: Colors.blueAccent,
        onTap: _onItemTapped,
      ),
    );
  }
}
