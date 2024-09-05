import 'package:carousel_slider/carousel_slider.dart';
import 'package:flutter/material.dart';

class BeachDetailPage extends StatelessWidget {
  final String beachName;
  final String safetyMessage;
  final int safetyScore;
  final List<dynamic> reasons;

  BeachDetailPage({
    required this.beachName,
    required this.safetyMessage,
    required this.safetyScore,
    required this.reasons,
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
      appBar: AppBar(
        title: Text(beachName),
        backgroundColor: _getMarkerColor(safetyScore),
        elevation: 0,
      ),
      body: Column(
        children: [
          // Full-screen Carousel
          Stack(
            children: [
              CarouselSlider(
                options: CarouselOptions(
                  height: 280.0,
                  autoPlay: true,
                  viewportFraction: 1.0,
                ),
                items: imageUrls.map((url) {
                  return Builder(
                    builder: (BuildContext context) {
                      return ClipRRect(
                        borderRadius: const BorderRadius.only(
                          bottomLeft: Radius.circular(30),
                          bottomRight: Radius.circular(30),
                        ),
                        child: Image.network(
                          url,
                          fit: BoxFit.cover,
                          width: MediaQuery.of(context).size.width,
                        ),
                      );
                    },
                  );
                }).toList(),
              ),
              // Gradient Overlay for better text readability
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.transparent,
                        Colors.black54,
                      ],
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: 20,
                left: 20,
                child: Text(
                  beachName,
                  style: const TextStyle(
                    fontSize: 28,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          // Safety Score with circular badge
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0), // Added padding around container
            child: Container(
              padding: const EdgeInsets.all(20), // More padding for spaciousness
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                color: Colors.white.withOpacity(0.7), // Higher opacity for clearer contrast
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    blurRadius: 10,
                    spreadRadius: 1,
                    offset: Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [_getMarkerColor(safetyScore), Colors.blue],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 10,
                              offset: Offset(0, 3),
                            ),
                          ],
                        ),
                        child: Text(
                          safetyScore.toString(),
                          style: const TextStyle(
                            fontSize: 26, // Slightly reduced font size
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12), // Increased spacing between badge and text
                      Text(
                        'Safety Score',
                        style: const TextStyle(
                          fontSize: 22, // Slightly reduced font size
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12), // Extra space
                  // Safety Message
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12.0),
                    child: Text(
                      safetyMessage,
                      style: const TextStyle(
                        fontSize: 16, // Slightly smaller font for text
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20), // Extra space
          // Reasons List with Card Design
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    blurRadius: 20,
                    spreadRadius: 1,
                    offset: Offset(0, -3),
                  ),
                ],
              ),
              child: ListView.builder(
                itemCount: reasons.length,
                itemBuilder: (context, index) {
                  return Card(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15),
                    ),
                    elevation: 3, // Reduced elevation for a lighter feel
                    margin: const EdgeInsets.symmetric(vertical: 12), // Increased vertical spacing between cards
                    child: ListTile(
                      leading: Icon(
                        Icons.warning_amber_rounded,
                        color: _getMarkerColor(safetyScore),
                        size: 26, // Reduced icon size for better spacing
                      ),
                      title: Text(
                        reasons[index].toString(),
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
