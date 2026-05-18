
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class StatsCard extends StatelessWidget {
  const StatsCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final s = controller.state;
    final active = controller.state.quests.where((q) => !q.isCompleted).length;
    final width = MediaQuery.sizeOf(context).width;
    final height = width < 430 ? 250.0 : 285.0;
    return PixelPanel(
      title: l.stats,
      height: height,
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 18),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final donutSize = (constraints.maxWidth * 0.32).clamp(96.0, 170.0);
          return Row(
            children: <Widget>[
              SizedBox(
                width: donutSize,
                height: donutSize,
                child: DonutChart(
                  completed: s.completedOnTime,
                  late: s.lateCompleted,
                  onDue: active,
                  percent: s.completionPercent,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    FittedBox(
                      alignment: Alignment.centerLeft,
                      fit: BoxFit.scaleDown,
                      child: Text(l.scoreLabel(s.completionPercent), maxLines: 1, style: const TextStyle(fontSize: 38, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 3)),
                    ),
                    const SizedBox(height: 14),
                    _bar(context),
                    const SizedBox(height: 12),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(flex: 12, child: _legend(context, l, active)),
                        Expanded(flex: 9, child: _miniStat(context, l.streak, '${s.streak}')),
                        Expanded(flex: 12, child: _miniStat(context, l.level, '${s.level}\n${s.exp}/${s.expNeeded}')),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _bar(BuildContext context) {
    final c = appColors(context);
    final pct = controller.state.expNeeded == 0 ? 0.0 : (controller.state.exp / controller.state.expNeeded).clamp(0.0, 1.0);
    return Column(
      children: <Widget>[
        Container(height: 5, color: c.line.withValues(alpha: 0.9)),
        const SizedBox(height: 5),
        Align(
          alignment: Alignment.centerLeft,
          child: FractionallySizedBox(widthFactor: pct, child: Container(height: 5, color: c.line.withValues(alpha: 0.6))),
        ),
      ],
    );
  }

  Widget _legend(BuildContext context, L10n l, int active) {
    final c = appColors(context);
    Widget item(Color color, String text) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(children: <Widget>[
            Container(width: 12, height: 12, color: color),
            const SizedBox(width: 6),
            Expanded(child: Text(text, overflow: TextOverflow.ellipsis, maxLines: 1, style: TextStyle(color: c.text, fontSize: 11, height: 1.0, fontWeight: FontWeight.w900))),
          ]),
        );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        item(const Color(0xFF00FF39), l.completed),
        item(const Color(0xFFFF1208), l.late),
        item(const Color(0xFFFFC400), l.due),
      ],
    );
  }

  Widget _miniStat(BuildContext context, String title, String value) {
    final c = appColors(context);
    return Padding(
      padding: const EdgeInsets.only(left: 6),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          SizedBox(
            height: 18,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(title, maxLines: 1, textAlign: TextAlign.center, style: TextStyle(fontSize: 14, height: 1.0, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 1.6)),
            ),
          ),
          Container(height: 2, color: c.line.withValues(alpha: 0.85)),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(value, textAlign: TextAlign.center, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: c.text, height: 1.1)),
          ),
        ],
      ),
    );
  }
}
