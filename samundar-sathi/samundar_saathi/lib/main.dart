import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import 'package:samundar_saathi/login.dart';

void main() {
  runApp(const MainApp());
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Lottie.network(
          'https://lottie.host/9da4b4f2-c9fb-4377-9666-5f69d8bf6383/K7kAoQmEzZ.json',
          width: 200,
          height: 200,
          fit: BoxFit.fill,
          onLoaded: (composition) {
            // Ensure the animation runs for 2.1 seconds
            Future.delayed(const Duration(seconds: 2, milliseconds: 100), () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => const LoginPage()),
              );
            });
          },
        ),
      ),
    );
  }
}
