import 'package:flutter/material.dart';

class NeonButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final Color baseColor;

  const NeonButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.baseColor = const Color.fromRGBO(0, 242, 255, 1.0),
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: baseColor,
        foregroundColor: const Color(0xFF0D0D14), // Dark text to contrast
        shadowColor: baseColor.withValues(alpha: 0.5),
        elevation: 8,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
        ),
        padding: const EdgeInsets.symmetric(vertical: 20),
        minimumSize: const Size(double.infinity, 70),
      ).copyWith(
        overlayColor: WidgetStateProperty.resolveWith<Color?>(
          (Set<WidgetState> states) {
            if (states.contains(WidgetState.pressed)) {
              return baseColor.withValues(alpha: 0.8);
            }
            return null;
          },
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}
