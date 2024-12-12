import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:carousel_slider/carousel_slider.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

Future<void> fetchActivities() async {
  try {
    // Access Firestore instance
    final FirebaseFirestore _firestore = FirebaseFirestore.instance;

    // Fetch all documents from the 'samundar_data' collection
    QuerySnapshot snapshot = await _firestore.collection('active').get();

    // Parse the documents into a variable
    activities = snapshot.docs.map((doc) {
      return doc.data() as Map<String, dynamic>;
    }).toList();

    // Print or use the activities as needed
    log('Fetched Activities: $activities');
  } catch (e) {
    log('Error fetching activities: $e');
  }
}

List<Map<String, dynamic>> activities = [];

IconData getActivityIcon(String activity) {
  // Mapping of activity categories to icons
  final Map<String, IconData> activityIcons = {
    "Water-Based Activities":
        Icons.pool, // Example: Pool for water-based activities
    "Relaxation and Wellness": Icons.spa, // Example: Spa for relaxation
    "Family-Friendly Activities":
        Icons.child_friendly, // Example: Child-friendly activities
    "Fitness and Sports": Icons.fitness_center, // Example: Fitness center
    "Adventure and Exploration":
        Icons.explore, // Example: Explore for adventure
    "Social and Leisure Activities":
        Icons.group, // Example: Group for social activities
    "Cultural and Eco Activities": Icons.eco, // Example: Eco activities
    "Romantic Activities": Icons.favorite, // Example: Favorite for romantic
    "Extreme Sports (for Thrill Seekers)":
        Icons.flash_on, // Example: Flash for extreme sports
    "Food and Drinks":
        Icons.local_dining, // Example: Dining for food and drinks
    "Seasonal Activities":
        Icons.event, // Example: Event for seasonal activities
  };

  // Mapping activities to their categories
  final Map<String, String> activityCategories = {
    // Water-Based Activities
    "Swimming": "Water-Based Activities",
    "Snorkeling": "Water-Based Activities",
    "Surfing": "Water-Based Activities",
    "Paddleboarding": "Water-Based Activities",
    "Jet Skiing": "Water-Based Activities",
    "Parasailing": "Water-Based Activities",
    "Scuba Diving": "Water-Based Activities",
    "Boating/Kayaking": "Water-Based Activities",
    "Fishing": "Water-Based Activities",
    "Bodyboarding": "Water-Based Activities",
    "Kite Surfing": "Water-Based Activities",
    "Wave Watching": "Water-Based Activities",

    // Relaxation and Wellness
    "Sunbathing": "Relaxation and Wellness",
    "Reading": "Relaxation and Wellness",
    "Meditation": "Relaxation and Wellness",
    "Beach Yoga": "Relaxation and Wellness",
    "Picnicking": "Relaxation and Wellness",
    "Stargazing": "Relaxation and Wellness",
    "Massage": "Relaxation and Wellness",

    // Family-Friendly Activities
    "Building Sandcastles": "Family-Friendly Activities",
    "Beachcombing": "Family-Friendly Activities",
    "Playing Frisbee": "Family-Friendly Activities",
    "Beach Volleyball": "Family-Friendly Activities",
    "Flying Kites": "Family-Friendly Activities",
    "Paddle Ball": "Family-Friendly Activities",
    "Treasure Hunts": "Family-Friendly Activities",

    // Fitness and Sports
    "Running/Jogging": "Fitness and Sports",
    "Beach Football/Soccer": "Fitness and Sports",
    "Beach Cricket": "Fitness and Sports",
    "Yoga and Pilates": "Fitness and Sports",
    "Sand Workouts": "Fitness and Sports",
    "Cycling": "Fitness and Sports",

    // Adventure and Exploration
    "Hiking": "Adventure and Exploration",
    "Rock Climbing": "Adventure and Exploration",
    "Tide Pooling": "Adventure and Exploration",
    "Wildlife Watching": "Adventure and Exploration",
    "Photography": "Adventure and Exploration",

    // Social and Leisure Activities
    "Barbecuing": "Social and Leisure Activities",
    "Camping": "Social and Leisure Activities",
    "Bonfires": "Social and Leisure Activities",
    "Dancing": "Social and Leisure Activities",
    "Music Jam": "Social and Leisure Activities",
    "Beach Parties": "Social and Leisure Activities",

    // Cultural and Eco Activities
    "Art and Sand Sculptures": "Cultural and Eco Activities",
    "Eco-Cleanups": "Cultural and Eco Activities",
    "Educational Tours": "Cultural and Eco Activities",
    "Local Markets": "Cultural and Eco Activities",

    // Romantic Activities
    "Watching Sunsets/Sunrises": "Romantic Activities",
    "Dining by the Shore": "Romantic Activities",
    "Walking Along the Beach": "Romantic Activities",
    "Boat Rides for Two": "Romantic Activities",

    // Extreme Sports (for Thrill Seekers)
    "Windsurfing": "Extreme Sports (for Thrill Seekers)",
    "Paragliding": "Extreme Sports (for Thrill Seekers)",
    "Underwater Scooter Riding": "Extreme Sports (for Thrill Seekers)",
    "Water Skiing": "Extreme Sports (for Thrill Seekers)",

    // Food and Drinks
    "Beach Cafés": "Food and Drinks",
    "Seafood Sampling": "Food and Drinks",
    "Ice Cream Stands": "Food and Drinks",

    // Seasonal Activities
    "Whale Watching": "Seasonal Activities",
    "Festivals": "Seasonal Activities",
    "Sand Art Competitions": "Seasonal Activities",
  };

  // Get the category of the activity
  String? category = activityCategories[activity];

  // Return the icon corresponding to the category or a default icon
  return activityIcons[category] ?? Icons.help_outline;
}

class BeachDetailPage extends StatefulWidget {
  final String beachName;
  final String safetyMessage;
  final int safetyScore;
  final List<dynamic> reasons;

  const BeachDetailPage({
    super.key,
    required this.beachName,
    required this.safetyMessage,
    required this.safetyScore,
    required this.reasons,
  });

  @override
  State<BeachDetailPage> createState() => _BeachDetailPageState();
}

class _BeachDetailPageState extends State<BeachDetailPage> {
  Color _getMarkerColor(int rating) {
    if (rating <= 3) return Colors.red;
    if (rating <= 7) return Colors.yellow;
    return Colors.green;
  }

  @override
  void initState() {
    super.initState();
    fetchActivities(); // Ensure this method is properly implemented to fetch data from Firebase
  }

  Future<List<Map<String, dynamic>>> fetchActivitiesForTime(String time) async {
    try {
      // First, fetch the activities from Firestore
      await fetchActivities();

      // Debug print to check the contents of activities
      log('Debugging - activities: $activities');

      // Check if activities is empty
      if (activities.isEmpty) {
        log('No activities found in Firestore');
        return [];
      }

      // Check the structure of the first document
      if (activities.first is! Map) {
        log('Unexpected data structure in activities');
        return [];
      }

      // Ensure the recommendations key exists and is a list
      var recommendations = activities.first['recommendations'];
      if (recommendations == null || recommendations is! List) {
        log('No recommendations found or invalid format');
        return [];
      }

      // Iterate through the recommendations to find matching time slots
      for (var timeSlot in recommendations) {
        // Check if the time is within the time slot
        if (_isTimeInSlot(time, timeSlot['time_slot'])) {
          // Find the specific hourly activities
          for (var hourlyActivity in timeSlot['hourly_activities']) {
            // If the time matches exactly or is within the slot
            if (hourlyActivity['time'] == time) {
              // Convert possible activities to the required format
              List<Map<String, dynamic>> formattedActivities =
                  (hourlyActivity['possible_activities'] as List)
                      .map((activity) {
                return {
                  "activity": activity,
                  "category": _getCategoryForActivity(activity)
                };
              }).toList();

              return formattedActivities;
            }
          }
        }
      }

      // If no activities found, return an empty list
      return [];
    } catch (e) {
      log('Error in fetchActivitiesForTime: $e');
      return [];
    }
  }

// Helper methods remain the same as in previous response

// Helper method to check if a time is within a time slot
  bool _isTimeInSlot(String time, String timeSlot) {
    var slotParts = timeSlot.split('-');
    return time.compareTo(slotParts[0]) >= 0 &&
        time.compareTo(slotParts[1]) < 0;
  }

// Helper method to categorize activities
  String _getCategoryForActivity(String activity) {
    // You can expand this with more specific categorizations
    if ([
      'Swimming',
      'Snorkeling',
      'Surfing',
      'Paddleboarding',
      'Jet Skiing',
      'Scuba Diving'
    ].contains(activity)) {
      return 'Water-Based Activities';
    } else if (['Yoga', 'Meditation', 'Beach Yoga', 'Yoga and Pilates']
        .contains(activity)) {
      return 'Relaxation and Wellness';
    } else if ([
      'Running/Jogging',
      'Beach Volleyball',
      'Beach Football/Soccer',
      'Cycling'
    ].contains(activity)) {
      return 'Sports and Exercise';
    } else if (['Stargazing', 'Photography', 'Art and Sand Sculptures']
        .contains(activity)) {
      return 'Leisure and Creative Activities';
    } else {
      return 'Other Activities';
    }
  }

  String selectedTime = "10:00"; // Default time
  void updateActivities(String time) async {
    final fetchedActivities = await fetchActivitiesForTime(time);
    setState(() {
      selectedTime = time;
      activities = fetchedActivities;
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<String> imageUrls = [
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxGYhhCxHXxM5d-KV10RstIRUueQgaAvCloA&s',
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlK2VgKxLjWmmyNELGYf8f3KzpEYbFiVCu4w&s',
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.beachName),
        backgroundColor: _getMarkerColor(widget.safetyScore),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Stack(
              children: [
                CarouselSlider(
                  options: CarouselOptions(
                    height: 200.0,
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
                    widget.beachName,
                    style: const TextStyle(
                      fontSize: 28,
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Positioned(
                  top: 20,
                  right: 20,
                  child: Column(
                    children: [
                      const Text(
                        'Safety Score',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              _getMarkerColor(widget.safetyScore),
                              Colors.blue
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 10,
                              offset: const Offset(0, 3),
                            ),
                          ],
                        ),
                        child: Text(
                          widget.safetyScore.toString(),
                          style: const TextStyle(
                            fontSize: 26,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Updated Popular Times Widget
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: DynamicTimesWidget(
                selectedTime: selectedTime,
                onTimeSelected: updateActivities,
              ),
            ),

            const SizedBox(height: 20),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0),
              child: Align(
                child: Text(
                  'Activities',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            // Display Activities
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: activities.isEmpty
                  ? const Center(child: Text('No activities found'))
                  : ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: activities.length,
                      itemBuilder: (context, index) {
                        final activity = activities[index];

                        // Null-aware checks and default values
                        final activityName =
                            activity['activity'] ?? 'Unknown Activity';
                        final activityCategory =
                            activity['category'] ?? 'Uncategorized';

                        // Null-aware icon selection
                        final icon = getActivityIcon(activityName);

                        return ListTile(
                          leading: Icon(icon, color: Colors.blue),
                          title: Text(activityName),
                          subtitle: Text(activityCategory),
                        );
                      },
                    ),
            ),

            const SizedBox(height: 20),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0),
              child: WeatherWidget(),
            ),
          ],
        ),
      ),
    );
  }
}

class DynamicTimesWidget extends StatelessWidget {
  final String selectedTime;
  final Function(String) onTimeSelected;

  const DynamicTimesWidget({
    super.key,
    required this.selectedTime,
    required this.onTimeSelected,
  });

  @override
  Widget build(BuildContext context) {
    final times =
        List.generate(24, (index) => "${index.toString().padLeft(2, '0')}:00");

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Select a Time',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          height: 60,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: times.length,
            itemBuilder: (context, index) {
              final time = times[index];
              final isSelected = time == selectedTime;
              return GestureDetector(
                onTap: () => onTimeSelected(time),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 5),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 15, vertical: 10),
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.blue : Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: isSelected
                        ? [
                            BoxShadow(
                              color: Colors.blue.withOpacity(0.5),
                              blurRadius: 10,
                              spreadRadius: 2,
                            ),
                          ]
                        : null,
                  ),
                  child: Center(
                    child: Text(
                      time,
                      style: TextStyle(
                        color: isSelected ? Colors.white : Colors.black,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class WeatherWidget extends StatelessWidget {
  const WeatherWidget({super.key});

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
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            children: [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Thu'),
              Text('29°',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          Column(
            children: [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Fri'),
              Text('28°',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          Column(
            children: [
              Icon(Icons.wb_cloudy),
              SizedBox(height: 5),
              Text('Sat'),
              Text('28°',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }
}
