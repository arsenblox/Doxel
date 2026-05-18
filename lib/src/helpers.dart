import 'package:flutter/material.dart';

import 'package:url_launcher/url_launcher.dart';
String two(int n) => n.toString().padLeft(2, '0');

String formatDate(DateTime d) => '${two(d.day)}/${two(d.month)}/${d.year}';
String formatTime(DateTime d) => '${two(d.hour)}:${two(d.minute)}';
String formatDateTime(DateTime d) => '${formatDate(d)} ${formatTime(d)}';

String remainingText(DateTime deadline) {
  final now = DateTime.now();
  if (now.isAfter(deadline)) return 'PASSED';
  final diff = deadline.difference(now);
  if (diff.inDays >= 1) return '${diff.inDays}D ${diff.inHours % 24}H';
  if (diff.inHours >= 1) return '${diff.inHours}H ${diff.inMinutes % 60}M';
  return '${diff.inMinutes.clamp(0, 999)}M';
}

Color priorityColor(String priorityName, BuildContext context) {
  switch (priorityName.toLowerCase()) {
    case 'urgent':
    case 'darurat':
      return const Color(0xFFFF4C67);
    case 'normal':
      return const Color(0xFFFFC928);
    default:
      return const Color(0xFF00FF44);
  }
}


Future<void> openExternalLink(BuildContext context, String rawUrl) async {
  final cleaned = rawUrl.trim();
  if (cleaned.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No LMS link was added for this quest.')));
    return;
  }

  final uri = Uri.tryParse(cleaned);
  final valid = uri != null && (uri.isScheme('http') || uri.isScheme('https')) && uri.host.isNotEmpty;
  if (!valid) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invalid LMS link.')));
    return;
  }

  try {
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not open LMS link.')));
    }
  } catch (e) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not open LMS link: $e')));
  }
}
