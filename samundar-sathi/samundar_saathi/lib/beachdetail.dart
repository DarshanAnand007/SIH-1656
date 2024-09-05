import 'package:flutter/material.dart';
import 'package:carousel_slider/carousel_slider.dart';

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
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(beachName),
        backgroundColor: _getMarkerColor(safetyScore),
        elevation: 0,
      ),
      body: Column(
        children: [
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
          
          // Adding Popular Times Widget
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: PopularTimesWidget(),
          ),
          
          const SizedBox(height: 20),

          // Adding Weather Widget
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: WeatherWidget(),
          ),

          const SizedBox(height: 20),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                color: Colors.white.withOpacity(0.7),
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
                            fontSize: 26,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Safety Score',
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12.0),
                    child: Text(
                      safetyMessage,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class PopularTimesWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Popular Times',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(7, (index) {
            return Column(
              children: [
                Container(
                  width: 8,
                  height: 50 - index * 5.0, // Simulate busyness
                  decoration: BoxDecoration(
                    color: index == 5 ? Colors.blue : Colors.grey, // Show blue for peak time
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(height: 5),
                Text('${index + 1} PM'),
              ],
            );
          }),
        ),
      ],
    );
  }
}

class WeatherWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            spreadRadius: 1,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            children: const [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Thu'),
              Text('29°', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          Column(
            children: const [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Fri'),
              Text('28°', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          Column(
            children: const [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Sat'),
              Text('28°', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }
}
