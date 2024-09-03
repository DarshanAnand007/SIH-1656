import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  GoogleMapController? mapController;

  // Define the bounds to include India and surrounding regions
  final LatLngBounds regionBounds = LatLngBounds(
    southwest: LatLng(5.0, 60.0), // Southwestern point (includes some of Africa)
    northeast: LatLng(40.0, 100.0), // Northeastern point (includes part of China)
  );

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
    // Move camera to the region bounds
    mapController?.animateCamera(CameraUpdate.newLatLngBounds(regionBounds, 0));
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
          target: LatLng(20.0, 80.0), // Rough central point of the larger region
          zoom: 5.5, // Adjust zoom level here
        ),
      ),
    );
  }
}

void main() {
  runApp(MaterialApp(
    home: HomePage(),
  ));
}
