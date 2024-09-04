import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:math'; // For generating random ratings

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  GoogleMapController? mapController;
  Set<Marker> _markers = {};
  bool isLoading = true;

  // Initial empty list for locations
  List<Map<String, dynamic>> locations = [];

  @override
  void initState() {
    super.initState();
    _fetchLocationData(); // Fetch locations from API
  }

  Future<void> _fetchLocationData() async {
    try {
      final response =
          await http.get(Uri.parse('http://192.168.0.106:5001/weather'));

      if (response.statusCode == 200) {
        final jsonData = json.decode(response.body);
        final latitude = jsonData['coordinates']['latitude'];
        final longitude = jsonData['coordinates']['longitude'];
        final locationName = jsonData['location'];
        final rating =
            Random().nextInt(10) + 1; // Generate random rating for now

        setState(() {
          // Add the fetched location to the list
          locations.add({
            "city": locationName,
            "lat": latitude,
            "lng": longitude,
            "rating": rating,
          });
          _generateMarkers(); // Generate markers after adding new location
          isLoading = false; // Stop loading indicator
        });
      } else {
        print('Failed to load data from API');
        setState(() {
          isLoading = false; // Stop loading even if the data fails
        });
      }
    } catch (e) {
      print("Error fetching data: $e");
      setState(() {
        isLoading = false; // Stop loading in case of error
      });
    }
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

  void _addMarker(
      String city, LatLng position, BitmapDescriptor markerIcon, int rating) {
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
    canvas.drawCircle(
        Offset(markerSize / 2, markerSize / 2), markerSize / 2, paint);

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
            southwest: LatLng(8.0, 68.0),
            northeast: LatLng(35.0, 97.0),
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
          ? Center(child: CircularProgressIndicator()) // Show loading indicator
          : GoogleMap(
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
