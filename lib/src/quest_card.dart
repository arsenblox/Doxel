
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'complete_quest_sheet.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class QuestCard extends StatelessWidget {
  const QuestCard({super.key, required this.controller, required this.quest, this.compact = false});
  final AppController controller;
  final Quest quest;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final pName = l.priorityName(quest.priority);
    final exp = quest.expGainAt(DateTime.now());
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: EdgeInsets.all(compact ? 12 : 18),
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(compact ? 12 : 28),
        border: Border.all(color: c.line.withValues(alpha: 0.8), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(quest.title.toUpperCase(), overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 13 : 21, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2)),
              ),
              IconButton(
                tooltip: l.favorite,
                onPressed: () => controller.toggleFavorite(quest.id),
                icon: Icon(quest.favorite ? Icons.star : Icons.star_border, color: quest.favorite ? const Color(0xFFFFC400) : c.text),
              ),
            ],
          ),
          Container(height: 2, color: c.line.withValues(alpha: 0.85)),
          const SizedBox(height: 8),
          if (!compact && quest.description.trim().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Text(quest.description.toUpperCase(), maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 16, color: c.muted, fontWeight: FontWeight.w900, letterSpacing: 1.3)),
            ),
          Wrap(
            spacing: 14,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: <Widget>[
              Text('${l.priority}: ', style: TextStyle(color: c.muted, fontWeight: FontWeight.w900)),
              Text(pName, style: TextStyle(color: priorityColor(pName, context), fontWeight: FontWeight.w900, letterSpacing: 1.4)),
              Text('EXP $exp', style: TextStyle(color: c.text, fontWeight: FontWeight.w900)),
              Text('${l.deadline}: ${formatDateTime(quest.deadline)}', style: TextStyle(color: c.text, fontWeight: FontWeight.w900)),
              Text(remainingText(quest.deadline), style: TextStyle(color: quest.isOverdue ? const Color(0xFFFF4C67) : c.accent, fontWeight: FontWeight.w900)),
            ],
          ),
          if (!compact) const SizedBox(height: 16),
          if (!compact)
            Row(
              children: <Widget>[
                if (quest.lmsUrl.isNotEmpty)
                  Expanded(child: PixelButton(label: l.openLms, icon: Icons.open_in_new, onPressed: () => openExternalLink(context, quest.lmsUrl))),
                if (quest.lmsUrl.isNotEmpty) const SizedBox(width: 12),
                Expanded(
                  child: PixelButton(
                    label: l.complete,
                    filled: true,
                    onPressed: () => showCompleteQuestSheet(context, controller, quest),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

// This is kept only for backward compatibility with older code. The home screen no longer uses ON DUE.
class OnDueCard extends StatelessWidget {
  const OnDueCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
