from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "lib" / "src"

if not (ROOT / "pubspec.yaml").exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current Flutter project.")


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v6")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def replace_regex(path: Path, pattern: str, replacement: str, flags: int = re.S) -> bool:
    text = read(path)
    new, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count:
        write(path, new)
        return True
    print("warning: pattern not found in", path.relative_to(ROOT))
    return False


# 1) Sort labels: keep favorite behavior internally, but remove "Favorite +" from the UI text.
i18n_path = SRC / "i18n.dart"
if i18n_path.exists():
    text = read(i18n_path)
    text = re.sub(
        r"String get sortPriority => .*?;",
        "String get sortPriority => id ? 'Prioritas tertinggi' : 'Highest priority';",
        text,
    )
    text = re.sub(
        r"String get sortExp => .*?;",
        "String get sortExp => id ? 'EXP tertinggi' : 'Highest EXP';",
        text,
    )
    write(i18n_path, text)
else:
    print("warning: i18n.dart not found")


# 2) Calendar: bigger text, default May 2026, no compact overflow.
calendar_path = SRC / "calendar_card.dart"
calendar_code = r'''
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
    // Default design month requested for the mockup.
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
          final compactSpace = constraints.maxWidth < 360 || constraints.maxHeight < 360;
          final titleFont = compactSpace ? 20.0 : 24.0;
          final weekFont = compactSpace ? 12.0 : 14.0;
          final dayFont = compactSpace ? 15.0 : 18.0;
          final dotSize = compactSpace ? 5.0 : 7.0;

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
                padding: const EdgeInsets.all(2),
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => setState(() => selected = date),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isSelected ? c.line.withValues(alpha: 0.18) : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: isToday ? Border.all(color: c.accent, width: 2) : null,
                    ),
                    child: Stack(
                      alignment: Alignment.center,
                      children: <Widget>[
                        FittedBox(
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
                        if (count > 0)
                          Positioned(
                            bottom: 3,
                            child: Container(
                              width: dotSize,
                              height: dotSize,
                              decoration: const BoxDecoration(color: Color(0xFFFFC400), shape: BoxShape.circle),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }

          return Column(
            children: <Widget>[
              SizedBox(
                height: compactSpace ? 38 : 46,
                child: Row(
                  children: <Widget>[
                    IconButton(
                      padding: EdgeInsets.zero,
                      onPressed: () => setState(() => month = DateTime(month.year, month.month - 1)),
                      icon: Icon(Icons.chevron_left, color: c.text),
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
                    IconButton(
                      padding: EdgeInsets.zero,
                      onPressed: () => setState(() => month = DateTime(month.year, month.month + 1)),
                      icon: Icon(Icons.chevron_right, color: c.text),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: compactSpace ? 24 : 28,
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
'''
if calendar_path.exists():
    write(calendar_path, calendar_code)
else:
    print("warning: calendar_card.dart not found")


# 3) Make the calendar panel a bit taller so the larger text has room.
home_path = SRC / "home_page.dart"
if home_path.exists():
    text = read(home_path)
    text = re.sub(
        r"SizedBox\(height:\s*compact\s*\?\s*\d+(?:\.0)?\s*:\s*\d+(?:\.0)?\s*,\s*child:\s*CalendarCard\(controller:\s*controller\)\)",
        "SizedBox(height: compact ? 390 : 455, child: CalendarCard(controller: controller))",
        text,
    )
    write(home_path, text)
else:
    print("warning: home_page.dart not found")


# 4) Donut chart: visible percentage on white mode, and gray ring when score says START NOW.
pixel_path = SRC / "pixel_widgets.dart"
if pixel_path.exists():
    donut_code = r'''
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
'''
    text = read(pixel_path)
    pattern = r"class DonutChart extends StatelessWidget \{.*?\n\}\n\nclass PixelButton extends StatelessWidget"
    new, count = re.subn(pattern, donut_code + "\nclass PixelButton extends StatelessWidget", text, count=1, flags=re.S)
    if count:
        write(pixel_path, new)
    else:
        print("warning: could not patch DonutChart in pixel_widgets.dart")
else:
    print("warning: pixel_widgets.dart not found")

print("\nDone. Now run:")
print("flutter clean")
print("flutter pub get")
print("flutter run")
