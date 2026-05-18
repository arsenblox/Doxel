
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'app_theme.dart';

class PixelPanel extends StatelessWidget {
  const PixelPanel({
    super.key,
    required this.child,
    this.title,
    this.padding = const EdgeInsets.all(18),
    this.height,
    this.margin,
  });

  final Widget child;
  final String? title;
  final EdgeInsets padding;
  final double? height;
  final EdgeInsets? margin;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Container(
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.88),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: c.line.withValues(alpha: 0.55), width: 2),
        boxShadow: <BoxShadow>[
          BoxShadow(color: Colors.black.withValues(alpha: 0.18), blurRadius: 18, offset: const Offset(0, 12)),
        ],
      ),
      child: Padding(
        padding: padding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            if (title != null) ...<Widget>[
              Center(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    title!,
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    style: TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2, color: c.text),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Center(child: Container(width: 250, height: 2, color: c.line.withValues(alpha: 0.82))),
              const SizedBox(height: 14),
            ],
            Expanded(child: child),
          ],
        ),
      ),
    );
  }
}

/// Kept as a harmless empty widget so older files that still reference it will not break.
class PixelCorners extends StatelessWidget {
  const PixelCorners({super.key, required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Column(
        children: <Widget>[
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(text, maxLines: 1, style: TextStyle(fontSize: 23, height: 1.0, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 3)),
          ),
          const SizedBox(height: 8),
          Container(width: 650, height: 4, color: c.line.withValues(alpha: 0.88)),
        ],
      ),
    );
  }
}


class DonutChart extends StatelessWidget {
  const DonutChart({super.key, required this.completed, required this.late, required this.onDue, required this.percent});
  final int completed;
  final int late;
  final int onDue;
  final int percent;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return CustomPaint(
      painter: _DonutPainter(completed: completed, late: late, onDue: onDue, percent: percent),
      child: Center(
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            '$percent%',
            style: TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, color: c.text),
          ),
        ),
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  _DonutPainter({required this.completed, required this.late, required this.onDue, required this.percent});
  final int completed;
  final int late;
  final int onDue;
  final int percent;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final stroke = math.max(20.0, size.shortestSide * 0.22);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.butt;

    // START NOW state: use one neutral ring instead of green, so it does not look like progress.
    if (percent <= 15) {
      paint.color = const Color(0xFF777A8A);
      canvas.drawArc(rect.deflate(stroke / 2), -math.pi / 2, math.pi * 2, false, paint);
      return;
    }

    final total = math.max(1, completed + late + onDue);
    double start = -math.pi / 2;
    void arc(int value, Color color) {
      if (value <= 0) return;
      final sweep = (value / total) * math.pi * 2;
      paint.color = color;
      canvas.drawArc(rect.deflate(stroke / 2), start, sweep, false, paint);
      start += sweep;
    }

    arc(completed, const Color(0xFF00FF39));
    arc(late, const Color(0xFFFF1208));
    arc(onDue, const Color(0xFFFFC400));
  }

  @override
  bool shouldRepaint(covariant _DonutPainter oldDelegate) =>
      oldDelegate.completed != completed || oldDelegate.late != late || oldDelegate.onDue != onDue || oldDelegate.percent != percent;
}

class PixelButton extends StatelessWidget {
  const PixelButton({super.key, required this.label, required this.onPressed, this.filled = false, this.icon});
  final String label;
  final VoidCallback? onPressed;
  final bool filled;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: icon == null ? const SizedBox.shrink() : Icon(icon, size: 18),
      label: FittedBox(fit: BoxFit.scaleDown, child: Text(label, maxLines: 1, style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5))),
      style: OutlinedButton.styleFrom(
        foregroundColor: filled ? c.panel : c.text,
        backgroundColor: filled ? c.line : Colors.transparent,
        side: BorderSide(color: c.line, width: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
      ),
    );
  }
}
