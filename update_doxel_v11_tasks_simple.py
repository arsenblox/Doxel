from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "lib" / "src"
PUBSPEC = ROOT / "pubspec.yaml"

if not PUBSPEC.exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current Flutter project.")

BACKUP_SUFFIX = ".bak_v11"


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + BACKUP_SUFFIX)
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def replace_getter(text: str, getter: str, value: str) -> str:
    pattern = rf"String\s+get\s+{re.escape(getter)}\s*=>\s*.*?;"
    repl = f"String get {getter} => {value};"
    new_text, count = re.subn(pattern, repl, text)
    if count == 0:
        print(f"warning: could not find getter {getter}")
    return new_text


# 1) Models: keep Doxel name, force Simple UI as the only active style.
models_path = SRC / "models.dart"
if models_path.exists():
    text = read(models_path)
    text = re.sub(r"const\s+String\s+appDisplayName\s*=\s*['\"][^'\"]+['\"];", "const String appDisplayName = 'Doxel';", text)
    text = re.sub(r"this\.uiStyle\s*=\s*UiStyle\.(?:compact|simple)", "this.uiStyle = UiStyle.simple", text)
    # Any saved old compact setting should load as simple now.
    text = re.sub(
        r"uiStyle:\s*UiStyle\.values\.firstWhere\(\s*\(e\)\s*=>\s*e\.name\s*==\s*json\['uiStyle'\],\s*orElse:\s*\(\)\s*=>\s*UiStyle\.(?:compact|simple),\s*\),",
        "uiStyle: UiStyle.simple,",
        text,
        flags=re.S,
    )
    # Keep saving simple if the model still serializes uiStyle.
    text = re.sub(r"'uiStyle':\s*uiStyle\.name,", "'uiStyle': UiStyle.simple.name,", text)
    write(models_path, text)


# 2) i18n: user-facing Quest -> Task, CREATE QUEST -> CREATE, sort labels clean.
i18n_path = SRC / "i18n.dart"
if i18n_path.exists():
    text = read(i18n_path)
    text = replace_getter(text, "homework", "id ? 'TUGAS' : 'TASKS'")
    text = replace_getter(text, "createQuest", "id ? 'BUAT' : 'CREATE'")
    text = replace_getter(text, "noQuest", "id ? 'Belum ada tugas.' : 'No tasks yet.'")
    text = replace_getter(text, "sortPriority", "id ? 'Prioritas tertinggi' : 'Highest priority'")
    text = replace_getter(text, "sortExp", "id ? 'EXP tertinggi' : 'Highest EXP'")
    # Keep these getters around for compatibility, but they should no longer appear in Settings.
    text = replace_getter(text, "uiDesign", "id ? 'Desain UI' : 'UI Design'")
    text = replace_getter(text, "compact", "id ? 'Compact' : 'Compact'")
    text = replace_getter(text, "simple", "id ? 'Simple' : 'Simple'")
    text = text.replace("No quests yet.", "No tasks yet.")
    text = text.replace("Belum ada quest.", "Belum ada tugas.")
    write(i18n_path, text)


# 3) Controller: update notification wording, force simple settings, and clean achievement names.
controller_path = SRC / "app_controller.dart"
if controller_path.exists():
    text = read(controller_path)

    text = text.replace("was added to your quest list.", "was added to your task list.")
    text = text.replace("completed. +$gained EXP gained.", "completed. +$gained EXP gained.")
    text = text.replace("Miss a quest deadline", "Miss a task deadline")
    text = text.replace("Complete a quest", "Complete a task")
    text = text.replace("You completed your first quest.", "You completed your first task.")
    text = text.replace("You completed a quest for the first time!", "You completed your first task.")
    text = text.replace("You completed 5 quests.", "You completed 5 tasks.")
    text = text.replace("You completed 10 quests.", "You completed 10 tasks.")
    text = text.replace("You completed 25 quests.", "You completed 25 tasks.")
    text = text.replace("You completed 50 quests.", "You completed 50 tasks.")
    text = text.replace("You completed 100 quests.", "You completed 100 tasks.")
    text = text.replace("You kept a 1-quest streak.", "You kept a 1-task streak.")
    text = text.replace("urgent quest", "urgent task")
    text = text.replace("Urgent Quest Completed", "Urgent Task Completed")
    text = text.replace("Image Attached", "Image Attached")
    text = text.replace("Notes Added", "Notes Added")

    # Force settings updates to stay on Simple UI, even if older UI code passes compact.
    text = re.sub(
        r"Future<void>\s+updateSettings\(AppSettings\s+next\)\s+async\s*\{\s*settings\s*=\s*next;\s*await\s+save\(\);\s*notifyListeners\(\);\s*\}",
        """Future<void> updateSettings(AppSettings next) async {
    settings = AppSettings(
      language: next.language,
      themeMode: next.themeMode,
      uiStyle: UiStyle.simple,
      fontStyle: next.fontStyle,
      reminderMinutes: next.reminderMinutes,
    );
    await save();
    notifyListeners();
  }""",
        text,
        flags=re.S,
    )

    # Replace the achievement set if the usual block is present.
    achievement_block = """
      a('quest_1', 'Task Beginner', 'You completed your first task.', completed, 1),
      a('quest_5', 'Task Regular', 'You completed 5 tasks.', completed, 5),
      a('quest_10', 'Task Tracker', 'You completed 10 tasks.', completed, 10),
      a('quest_25', 'Task Finisher', 'You completed 25 tasks.', completed, 25),
      a('quest_50', 'Task Veteran', 'You completed 50 tasks.', completed, 50),
      a('quest_100', 'Task Master', 'You completed 100 tasks.', completed, 100),
      a('level_2', 'Level 2 Reached', 'You reached level 2.', level, 2),
      a('level_5', 'Level 5 Reached', 'You reached level 5.', level, 5),
      a('level_10', 'Level 10 Reached', 'You reached level 10.', level, 10),
      a('level_25', 'Level 25 Reached', 'You reached level 25.', level, 25),
      a('level_50', 'Level 50 Reached', 'You reached level 50.', level, 50),
      a('level_100', 'DOXEL FINAL BOSS', 'You reached level 100.', level, 100),
      a('streak_1', 'First Streak', 'You kept a 1-task streak.', streak, 1),
      a('streak_5', '5 Streak', 'You kept a 5-task streak.', streak, 5),
      a('streak_10', '10 Streak', 'You kept a 10-task streak.', streak, 10),
      a('streak_15', '15 Streak', 'You kept a 15-task streak.', streak, 15),
      a('streak_30', '30 Streak', 'You kept a 30-task streak.', streak, 30),
      a('streak_60', '60 Streak', 'You kept a 60-task streak.', streak, 60),
      a('streak_100', 'STREAK GOD!', 'You kept a 100-task streak.', streak, 100),
      a('early_24h', 'Early Completion', 'Complete a task at least 24 hours before the deadline.', early24, 1),
      a('miss_streak_1', 'Streak Lost', 'Lose your streak for the first time.', missed, 1),
      a('miss_deadline_1', 'Deadline Missed', 'Miss a task deadline for the first time.', missed, 1),
      a('proof_sender', 'Image Attached', 'Complete a task with at least one image attached.', withImages, 1),
      a('lore_writer', 'Notes Added', 'Complete a task with notes attached.', withNotes, 1),
      a('panic_solver', 'Urgent Task Completed', 'Complete an urgent task on time.', urgentOnTime, 1),"""

    block_pattern = re.compile(r"\s*a\('quest_1'.*?\n\s*a\('panic_solver'.*?\),", re.S)
    if block_pattern.search(text):
        text = block_pattern.sub("\n" + achievement_block, text)
    else:
        # Fallback targeted replacements.
        replacements = {
            "'Quest Beginner'": "'Task Beginner'",
            "'Quest Regular'": "'Task Regular'",
            "'Quest Tracker'": "'Task Tracker'",
            "'Quest Finisher'": "'Task Finisher'",
            "'Quest Veteran'": "'Task Veteran'",
            "'Quest Master'": "'Task Master'",
            "'Level 100 Reached'": "'DOXEL FINAL BOSS'",
            "'100 Streak'": "'STREAK GOD!'",
            "'Urgent Quest Completed'": "'Urgent Task Completed'",
        }
        for a, b in replacements.items():
            text = text.replace(a, b)

    write(controller_path, text)


# 4) Settings page: remove UI Design/Compact setting completely.
settings_path = SRC / "settings_page.dart"
if settings_path.exists():
    settings_code = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final s = controller.settings;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(l.settings), backgroundColor: Colors.transparent),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 40),
        children: <Widget>[
          SectionTitle(l.settings),
          _tile(
            context,
            title: l.language,
            child: SegmentedButton<AppLanguage>(
              segments: const <ButtonSegment<AppLanguage>>[
                ButtonSegment(value: AppLanguage.en, label: Text('EN')),
                ButtonSegment(value: AppLanguage.id, label: Text('ID')),
              ],
              selected: <AppLanguage>{s.language},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(
                language: v.first,
                themeMode: s.themeMode,
                uiStyle: UiStyle.simple,
                fontStyle: s.fontStyle,
                reminderMinutes: s.reminderMinutes,
              )),
            ),
          ),
          _tile(
            context,
            title: l.theme,
            child: SegmentedButton<AppThemeMode>(
              segments: const <ButtonSegment<AppThemeMode>>[
                ButtonSegment(value: AppThemeMode.dark, label: Text('BLACK')),
                ButtonSegment(value: AppThemeMode.light, label: Text('WHITE')),
              ],
              selected: <AppThemeMode>{s.themeMode},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(
                language: s.language,
                themeMode: v.first,
                uiStyle: UiStyle.simple,
                fontStyle: s.fontStyle,
                reminderMinutes: s.reminderMinutes,
              )),
            ),
          ),
          _tile(
            context,
            title: l.font,
            child: SegmentedButton<PixelFontStyle>(
              segments: const <ButtonSegment<PixelFontStyle>>[
                ButtonSegment(value: PixelFontStyle.visitor, label: Text('Visitor TT2')),
                ButtonSegment(value: PixelFontStyle.classic, label: Text('Classic')),
              ],
              selected: <PixelFontStyle>{s.fontStyle},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(
                language: s.language,
                themeMode: s.themeMode,
                uiStyle: UiStyle.simple,
                fontStyle: v.first,
                reminderMinutes: s.reminderMinutes,
              )),
            ),
          ),
          _tile(
            context,
            title: l.reminders,
            child: Column(
              children: AppSettings.defaultReminderMinutes.map((m) {
                final enabled = s.reminderMinutes.contains(m);
                return CheckboxListTile(
                  value: enabled,
                  title: Text(l.reminderLabel(m)),
                  onChanged: (v) {
                    final next = List<int>.from(s.reminderMinutes);
                    if (v == true && !next.contains(m)) next.add(m);
                    if (v == false) next.remove(m);
                    next.sort((a, b) => b.compareTo(a));
                    controller.updateSettings(AppSettings(
                      language: s.language,
                      themeMode: s.themeMode,
                      uiStyle: UiStyle.simple,
                      fontStyle: s.fontStyle,
                      reminderMinutes: next,
                    ));
                  },
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () async {
              final ok = await showDialog<bool>(
                context: context,
                builder: (_) => AlertDialog(
                  title: Text(l.resetData),
                  content: const Text('This will delete all tasks, history, exp, level, and streak.'),
                  actions: <Widget>[
                    TextButton(onPressed: () => Navigator.pop(context, false), child: Text(l.cancel)),
                    FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(l.resetData)),
                  ],
                ),
              );
              if (ok == true) controller.resetAllData();
            },
            icon: const Icon(Icons.delete_forever),
            label: Text(l.resetData),
          ),
        ],
      ),
    );
  }

  Widget _tile(BuildContext context, {required String title, required Widget child}) {
    final c = appColors(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: c.line.withValues(alpha: 0.45), width: 2),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: <Widget>[
        Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 2)),
        const SizedBox(height: 12),
        child,
      ]),
    );
  }
}
'''
    write(settings_path, settings_code)


# 5) Common visible text fallback patches across UI files.
for path in SRC.glob("*.dart"):
    if path.name in {"models.dart", "i18n.dart", "app_controller.dart", "settings_page.dart"}:
        continue
    text = read(path)
    old = text
    replacements = {
        "CREATE QUEST": "CREATE",
        "Create Quest": "Create",
        "create quest": "create task",
        "No quests yet.": "No tasks yet.",
        "quest list": "task list",
        "Quest Beginner": "Task Beginner",
        "Quest Regular": "Task Regular",
        "Quest Tracker": "Task Tracker",
        "Quest Finisher": "Task Finisher",
        "Quest Veteran": "Task Veteran",
        "Quest Master": "Task Master",
        "Urgent Quest Completed": "Urgent Task Completed",
        "Complete a quest": "Complete a task",
        "completed quest": "completed task",
        "Completed quest": "Completed task",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    if text != old:
        write(path, text)

print("\nDone: Doxel stays as the app name, Settings is Simple-only, Quest wording is now Task wording, and Level 100 uses DOXEL FINAL BOSS.")
print("Run:")
print("flutter clean")
print("flutter pub get")
print("flutter run")
