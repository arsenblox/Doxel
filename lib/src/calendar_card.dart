
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class CalendarCard extends StatefulWidget {
  const CalendarCard({super.key, required this.controller});
  final AppController controller;

  @override
  State<CalendarCard> createState() => _CalendarCardState();
}

class _CalendarCardState extends State<CalendarCard> {
  late DateTime month;
  DateTime? selected;

  @override
  void initState() {
    super.initState();
    month = DateTime(2026, 5);
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final days = DateUtils.getDaysInMonth(month.year, month.month);
    final firstWeekday = DateTime(month.year, month.month, 1).weekday; // Monday = 1
    final active = widget.controller.activeQuests();
    final selectedTasks = selected == null
        ? <dynamic>[]
        : active.where((q) => DateUtils.isSameDay(q.deadline, selected)).toList();

    return PixelPanel(
      title: l.calendar,
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 380 || constraints.maxHeight < 420;
          final titleFont = compact ? 24.0 : 28.0;
          final weekFont = compact ? 13.0 : 15.0;
          final dayFont = compact ? 18.0 : 21.0;
          final navSize = compact ? 42.0 : 48.0;
          final dotSize = compact ? 7.0 : 8.0;

          Widget dayCell(int index) {
            final day = index - (firstWeekday - 1) + 1;
            if (day < 1 || day > days) {
              return const Expanded(child: SizedBox.shrink());
            }

            final date = DateTime(month.year, month.month, day);
            final count = active.where((q) => DateUtils.isSameDay(q.deadline, date)).length;
            final isToday = DateUtils.isSameDay(date, DateTime.now());
            final isSelected = selected != null && DateUtils.isSameDay(date, selected);

            return Expanded(
              child: Padding(
                padding: EdgeInsets.all(compact ? 2 : 3),
                child: Material(
                  color: isSelected ? c.line.withValues(alpha: 0.18) : Colors.transparent,
                  borderRadius: BorderRadius.circular(13),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(13),
                    onTap: () => setState(() => selected = date),
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(13),
                        border: isToday ? Border.all(color: c.accent, width: 2) : null,
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 3, horizontal: 2),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          SizedBox(
                            height: compact ? 22 : 26,
                            child: Center(
                              child: FittedBox(
                                fit: BoxFit.scaleDown,
                                child: Text(
                                  '$day',
                                  maxLines: 1,
                                  style: TextStyle(
                                    fontSize: dayFont,
                                    height: 1.0,
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: 0.8,
                                    color: c.text,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          SizedBox(
                            height: dotSize,
                            child: count > 0
                                ? Center(
                                    child: Container(
                                      width: dotSize,
                                      height: dotSize,
                                      decoration: const BoxDecoration(color: Color(0xFFFFC400), shape: BoxShape.circle),
                                    ),
                                  )
                                : const SizedBox.shrink(),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          }

          return Column(
            children: <Widget>[
              SizedBox(
                height: compact ? 50 : 58,
                child: Row(
                  children: <Widget>[
                    _CalendarNavButton(
                      size: navSize,
                      icon: Icons.chevron_left,
                      onTap: () => setState(() => month = DateTime(month.year, month.month - 1)),
                    ),
                    Expanded(
                      child: Center(
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            '${l.monthName(month.month)} ${month.year}',
                            maxLines: 1,
                            style: TextStyle(fontSize: titleFont, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2.0, color: c.text),
                          ),
                        ),
                      ),
                    ),
                    _CalendarNavButton(
                      size: navSize,
                      icon: Icons.chevron_right,
                      onTap: () => setState(() => month = DateTime(month.year, month.month + 1)),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: compact ? 28 : 32,
                child: Row(
                  children: <Widget>[
                    _Week('M', fontSize: weekFont),
                    _Week('T', fontSize: weekFont),
                    _Week('W', fontSize: weekFont),
                    _Week('T', fontSize: weekFont),
                    _Week('F', fontSize: weekFont),
                    _Week('S', fontSize: weekFont),
                    _Week('S', fontSize: weekFont),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              Expanded(
                child: Column(
                  children: List<Widget>.generate(6, (row) {
                    return Expanded(
                      child: Row(
                        children: List<Widget>.generate(7, (col) => dayCell(row * 7 + col)),
                      ),
                    );
                  }),
                ),
              ),
              if (selectedTasks.isNotEmpty) ...<Widget>[
                const SizedBox(height: 8),
                SizedBox(
                  height: 38,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: selectedTasks
                        .map<Widget>((q) => Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: Chip(label: Text(q.title, overflow: TextOverflow.ellipsis)),
                            ))
                        .toList(),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _CalendarNavButton extends StatelessWidget {
  const _CalendarNavButton({required this.size, required this.icon, required this.onTap});
  final double size;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return SizedBox(
      width: size,
      height: size,
      child: OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          padding: EdgeInsets.zero,
          side: BorderSide(color: c.line.withValues(alpha: 0.7), width: 2),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          foregroundColor: c.text,
        ),
        child: Icon(icon, size: size * 0.62),
      ),
    );
  }
}

class _Week extends StatelessWidget {
  const _Week(this.text, {required this.fontSize});
  final String text;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(fontWeight: FontWeight.w900, fontSize: fontSize, height: 1.0, color: c.muted),
        ),
      ),
    );
  }
}
