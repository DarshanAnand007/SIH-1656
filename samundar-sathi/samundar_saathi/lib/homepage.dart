import 'dart:convert';
import 'dart:developer';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'dart:async';

import 'package:samundar_saathi/beachdetail.dart'; // For Timer

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  GoogleMapController? mapController;
  Set<Marker> _markers = {};
  bool isLoading = true;

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
    final QuerySnapshot snapshot =
        await _firestore.collection('samundar_data').get();

    List<Map<String, dynamic>> newLocations = [];

    for (var doc in snapshot.docs) {
      final data = doc.data() as Map<String, dynamic>;

      // Accessing safety_score from safety_report
      final safetyReport = data['safety_report'];
      final safetyScore = safetyReport['safety_score'];
      final roundedScore = safetyScore != null ? safetyScore.round() : 0; // Round off the score

      // Retrieve latitude and longitude from Firestore data
      final double lat = data['latitude']?.toDouble() ?? 0.0;
      final double lng = data['longitude']?.toDouble() ?? 0.0;

      newLocations.add({
        "city": data['name'], // Beach name from the "name" field
        "lat": lat, // Actual latitude
        "lng": lng, // Actual longitude
        "rating": roundedScore, // Use the rounded score
      });
    }

    setState(() {
      locations = newLocations; // Update the locations list
      _markers.clear(); // Clear old markers
      _generateMarkers(); // Generate new markers
      isLoading = false; // Stop loading indicator
    });
  } catch (e) {
    log("Error fetching data from Firestore: $e");
    setState(() {
      isLoading = false; // Stop loading in case of error
    });
  }
}


// Helper function to generate random values in a given range
  double _generateRandomInRange(double start, double end) {
    final random = math.Random();
    return start + (random.nextDouble() * (end - start));
  }

  // Function to generate color based on rating
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
        location['rating'],
      );
    }
  }

  void _addMarker(String city, LatLng position, BitmapDescriptor markerIcon, int rating) {
  setState(() {
    _markers.add(
      Marker(
        markerId: MarkerId(city),
        position: position,
        icon: markerIcon,
        infoWindow: InfoWindow(
          title: city,
          snippet: 'Rating: $rating',
          onTap: () {
            // Navigate to the detailed page when the marker is tapped
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => BeachDetailPage(
                  beachName: city,
                  rating: rating,
                  safetyMessage: "Safe", // Example safety message, you can pass actual data
                  weatherData: { // Example weather data, replace with actual data
                    "wave_height": 0.86,
                    "wind_speed": 147,
                    "wave_direction": 255,
                  },
                ),
              ),
            );
          },
        ),
      ),
    );
  });
}


  // Function to create a custom marker with rating inside
  // Function to create a custom marker with a colored ring and a score in the center
Future<BitmapDescriptor> createMarkerWithRingAndScore(int rating) async {
  final Color ringColor = _getMarkerColor(rating); // Outer ring color based on rating

  final ui.PictureRecorder pictureRecorder = ui.PictureRecorder();
  final Canvas canvas = Canvas(pictureRecorder);
  final Paint outerRingPaint = Paint()..color = ringColor; // Color for outer ring
  final Paint innerCirclePaint = Paint()..color = Colors.white; // White inner circle

  final double markerSize = 150.0;
  final double ringWidth = 20.0; // Width of the outer ring

  // Draw outer ring (circle with color based on rating)
  canvas.drawCircle(Offset(markerSize / 2, markerSize / 2), markerSize / 2, outerRingPaint);

  // Draw inner circle (white)
  canvas.drawCircle(Offset(markerSize / 2, markerSize / 2), (markerSize / 2) - ringWidth, innerCirclePaint);

  // Draw the rating text
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
  painter.paint(
      canvas,
      Offset(markerSize / 2 - painter.width / 2,
          markerSize / 2 - painter.height / 2));

  // Convert the canvas into an image and then into a BitmapDescriptor
  final ui.Image image = await pictureRecorder
      .endRecording()
      .toImage(markerSize.toInt(), markerSize.toInt());
  final ByteData? byteData =
      await image.toByteData(format: ui.ImageByteFormat.png);
  final Uint8List imageData = byteData!.buffer.asUint8List();

  return BitmapDescriptor.fromBytes(imageData);
}


  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    // Move camera to show all points
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Samudra Saathi'),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator()) // Show loading indicator
          : GoogleMap(
              onMapCreated: _onMapCreated,
              initialCameraPosition: const CameraPosition(
                target: LatLng(20.0, 80.0), // Central point of India
                zoom: 4.5, // Adjust zoom level
              ),
              markers: _markers,
            ),
    );
  }
}
