
import 'dart:io';

import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'complete_quest_sheet.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final items = controller.completedQuests();
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.history),
          if (items.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in items)
              Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: c.panel.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: c.line.withValues(alpha: 0.6), width: 2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            q.title.toUpperCase(),
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: q.wasLateCompleted()
                                ? const Color(0xFFFF4C67).withValues(alpha: 0.18)
                                : const Color(0xFF00FF39).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(99),
                          ),
                          child: Text(
                            q.wasLateCompleted() ? l.completedLate : l.completedOnTime,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              color: q.wasLateCompleted() ? const Color(0xFFFF4C67) : const Color(0xFF00FF39),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('${l.completed}: ${formatDateTime(q.completedAt ?? q.deadline)}'),
                    const SizedBox(height: 4),
                    Text('${l.expGained}: +${q.historyExp()} EXP', style: const TextStyle(fontWeight: FontWeight.w900)),
                    if (q.completionNotes.trim().isNotEmpty) ...<Widget>[
                      const SizedBox(height: 10),
                      Text(q.completionNotes),
                    ],
                    if (q.photoPaths.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 12),
                      Text(
                        l.id ? 'Tap gambar untuk preview' : 'Tap image to preview',
                        style: TextStyle(color: c.muted, fontSize: 12, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      SizedBox(
                        height: 92,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          itemBuilder: (_, i) => InkWell(
                            borderRadius: BorderRadius.circular(12),
                            onTap: () => showImagePreview(context, q.photoPaths, i),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.file(
                                File(q.photoPaths[i]),
                                width: 92,
                                height: 92,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => Container(
                                  width: 92,
                                  height: 92,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(border: Border.all(color: c.line, width: 2), borderRadius: BorderRadius.circular(12)),
                                  child: const Icon(Icons.broken_image),
                                ),
                              ),
                            ),
                          ),
                          separatorBuilder: (_, __) => const SizedBox(width: 8),
                          itemCount: q.photoPaths.length,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
        ],
      ),
    );
  }
}
