import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'dart:math'; // For generating random ratings

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  GoogleMapController? mapController;
  Set<Marker> _markers = {};

  // Define the points across India with random values
  List<Map<String, dynamic>> locations = [
    {"city": "Bangalore", "lat": 12.9716, "lng": 77.5946, "rating": Random().nextInt(10) + 1},
    {"city": "Delhi", "lat": 28.7041, "lng": 77.1025, "rating": Random().nextInt(10) + 1},
    {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "rating": Random().nextInt(10) + 1},
    {"city": "Chennai", "lat": 13.0827, "lng": 80.2707, "rating": Random().nextInt(10) + 1},
    {"city": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "rating": Random().nextInt(10) + 1},
    {"city": "Kolkata", "lat": 22.5726, "lng": 88.3639, "rating": Random().nextInt(10) + 1},
    {"city": "Pune", "lat": 18.5204, "lng": 73.8567, "rating": Random().nextInt(10) + 1},
    {"city": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "rating": Random().nextInt(10) + 1},
    {"city": "Jaipur", "lat": 26.9124, "lng": 75.7873, "rating": Random().nextInt(10) + 1},
    {"city": "Lucknow", "lat": 26.8467, "lng": 80.9462, "rating": Random().nextInt(10) + 1},
  ];

  @override
  void initState() {
    super.initState();
    _generateMarkers(); // Generate markers for all locations
  }

  // Function to generate color based on rating
  Color _getMarkerColor(int rating) {
    if (rating <= 3) return Colors.red;
    if (rating <= 7) return Colors.yellow;
    return Colors.green;
  }

  Future<void> _generateMarkers() async {
    for (var location in locations) {
      final customMarker = await _createMarkerWithRating(location['rating']);
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
          ),
        ),
      );
    });
  }

  // Function to create a custom marker with rating inside
  Future<BitmapDescriptor> _createMarkerWithRating(int rating) async {
    final Color circleColor = _getMarkerColor(rating);

    // Create a marker widget dynamically
    final ui.PictureRecorder pictureRecorder = ui.PictureRecorder();
    final Canvas canvas = Canvas(pictureRecorder);
    final Paint paint = Paint()..color = circleColor;
    final double markerSize = 150.0;

    // Draw circle
    canvas.drawCircle(Offset(markerSize / 2, markerSize / 2), markerSize / 2, paint);

    // Draw text
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

    // Convert the canvas into an image and then into a BitmapDescriptor
    final ui.Image image = await pictureRecorder.endRecording().toImage(markerSize.toInt(), markerSize.toInt());
    final ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final Uint8List imageData = byteData!.buffer.asUint8List();

    return BitmapDescriptor.fromBytes(imageData);
  }

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    // Move camera to show all points
    mapController?.animateCamera(
      CameraUpdate.newLatLngBounds(
        LatLngBounds(
          southwest: LatLng(8.0, 68.0),
          northeast: LatLng(35.0, 97.0),
        ),
        50,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Samundar Saathi'),
      ),
      body: GoogleMap(
        onMapCreated: _onMapCreated,
        initialCameraPosition: CameraPosition(
          target: LatLng(20.0, 80.0), // Central point of India
          zoom: 4.5, // Adjust zoom level
        ),
        markers: _markers,
      ),
    );
  }
}

void main() {
  runApp(MaterialApp(
    home: HomePage(),
  ));
}
