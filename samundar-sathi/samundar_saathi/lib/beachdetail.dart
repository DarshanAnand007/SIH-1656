import 'package:carousel_slider/carousel_slider.dart';
import 'package:flutter/material.dart'; // Add carousel dependency

class BeachDetailPage extends StatelessWidget {
  final String beachName;
  final int rating;
  final String safetyMessage;
  final Map<String, dynamic> weatherData;

  BeachDetailPage({
    required this.beachName,
    required this.rating,
    required this.safetyMessage,
    required this.weatherData,
  });
  Color _getMarkerColor(int rating) {
    if (rating <= 3) return Colors.red;
    if (rating <= 7) return Colors.yellow;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    final List<String> imageUrls = [
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxGYhhCxHXxM5d-KV10RstIRUueQgaAvCloA&s',
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlK2VgKxLjWmmyNELGYf8f3KzpEYbFiVCu4w&s',
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlK2VgKxLjWmmyNELGYf8f3KzpEYbFiVCu4w&s',
    ]; // Example image URLs

    return Scaffold(
      appBar: AppBar(title: Text(beachName)),
      body: Column(
        children: [
          Stack(
            children: [
              CarouselSlider(
                options: CarouselOptions(height: 300.0, autoPlay: true),
                items: imageUrls.map((url) {
                  return Builder(
                    builder: (BuildContext context) {
                      return Image.network(url, fit: BoxFit.cover, width: 1000);
                    },
                  );
                }).toList(),
              ),
              Positioned(
                bottom: 10,
                left: 10,
                child: Text(
                  beachName,
                  style: TextStyle(
                    fontSize: 30,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    backgroundColor: Colors.black54,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 20),
          Text(
            'Rating: $rating',
            style: TextStyle(
              fontSize: 30,
              fontWeight: FontWeight.bold,
              color: _getMarkerColor(rating),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Text(
              'Safety Message: $safetyMessage',
              style: TextStyle(fontSize: 18),
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(8.0),
              children: weatherData.entries.map((entry) {
                return ListTile(
                  title: Text('${entry.key}: ${entry.value}'),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
