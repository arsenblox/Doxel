
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class AchievementsPage extends StatelessWidget {
  const AchievementsPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final items = controller.achievements(l.id);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.achievements),
          for (final a in items)
            Container(
              margin: const EdgeInsets.only(bottom: 14),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: c.panel.withValues(alpha: 0.86),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: a.unlocked ? const Color(0xFFFFC400) : c.line.withValues(alpha: 0.55), width: 2),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Icon(a.unlocked ? Icons.emoji_events : Icons.lock_outline, color: a.unlocked ? const Color(0xFFFFC400) : c.muted),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          a.title,
                          overflow: TextOverflow.ellipsis,
                          maxLines: 2,
                          style: const TextStyle(fontSize: 18, height: 1.05, fontWeight: FontWeight.w900, letterSpacing: 1.3),
                        ),
                      ),
                      if (a.unlocked)
                        Text(l.achievementUnlocked, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFFFFC400))),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(a.description, style: TextStyle(color: c.muted, fontWeight: FontWeight.w800, height: 1.2)),
                  const SizedBox(height: 14),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(99),
                    child: LinearProgressIndicator(
                      minHeight: 10,
                      value: a.value,
                      backgroundColor: c.line.withValues(alpha: 0.12),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: Text('${a.percent}% (${a.safeCurrent}/${a.goal})', style: const TextStyle(fontWeight: FontWeight.w900)),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
