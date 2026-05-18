from pathlib import Path
import re
import shutil

ROOT = Path.cwd()
SRC = ROOT / 'lib' / 'src'
MODELS = SRC / 'models.dart'

if not MODELS.exists():
    raise SystemExit('Could not find lib/src/models.dart. Run this script from your Flutter project root.')

backup = MODELS.with_suffix(MODELS.suffix + '.bak_v12')
if not backup.exists():
    shutil.copy2(MODELS, backup)

text = MODELS.read_text(encoding='utf-8')
original = text

# 1) Make Quest.photoPaths mutable when a new Quest is constructed.
# Old generated code used a const default list, which can later become unmodifiable.
if "this.photoPaths = const <String>[]" in text:
    text = text.replace(
        "    this.photoPaths = const <String>[],",
        "    List<String>? photoPaths,",
    )
    text = text.replace(
        "    this.lmsId = '',\n  });",
        "    this.lmsId = '',\n  }) : photoPaths = List<String>.from(photoPaths ?? const <String>[]);",
        1,
    )

# 2) Make AppSettings.reminderMinutes mutable and keep Simple UI as the default.
settings_pattern = re.compile(
    r"class AppSettings \{\s*"
    r"AppSettings\(\{\s*"
    r"this\.language = AppLanguage\.en,\s*"
    r"this\.themeMode = AppThemeMode\.dark,\s*"
    r"this\.uiStyle = UiStyle\.(?:compact|simple),\s*"
    r"this\.fontStyle = PixelFontStyle\.visitor,\s*"
    r"List<int>\? reminderMinutes,\s*"
    r"\}\) : reminderMinutes = (?:reminderMinutes \?\? defaultReminderMinutes|List<int>\.from\(reminderMinutes \?\? defaultReminderMinutes\));",
    re.DOTALL,
)
settings_replacement = """class AppSettings {
  AppSettings({
    this.language = AppLanguage.en,
    this.themeMode = AppThemeMode.dark,
    this.uiStyle = UiStyle.simple,
    this.fontStyle = PixelFontStyle.visitor,
    List<int>? reminderMinutes,
  }) : reminderMinutes = List<int>.from(reminderMinutes ?? defaultReminderMinutes);"""
text, settings_count = settings_pattern.subn(settings_replacement, text, count=1)

# If formatting was slightly different, still patch the most important lines.
text = text.replace("this.uiStyle = UiStyle.compact,", "this.uiStyle = UiStyle.simple,")
text = text.replace(
    ": reminderMinutes = reminderMinutes ?? defaultReminderMinutes;",
    ": reminderMinutes = List<int>.from(reminderMinutes ?? defaultReminderMinutes);",
)
text = text.replace("orElse: () => UiStyle.compact", "orElse: () => UiStyle.simple")

# 3) Make AppState lists mutable on fresh installs / resetAllData().
# The previous constructor used const lists, so state.quests.add(...) crashed.
if "List<Quest>? quests" not in text:
    appstate_pattern = re.compile(
        r"class AppState \{\s*"
        r"AppState\(\{\s*"
        r"this\.level = 1,\s*"
        r"this\.exp = 0,\s*"
        r"this\.streak = 0,\s*"
        r"this\.totalCompleted = 0,\s*"
        r"this\.lateCompleted = 0,\s*"
        r"this\.deadlineFailed = 0,\s*"
        r"this\.quests = const <Quest>\[\],\s*"
        r"this\.alertedReminderKeys = const <String>\[\],\s*"
        r"this\.penalizedQuestIds = const <String>\[\],\s*"
        r"this\.unlockedAchievementIds = const <String>\[\],\s*"
        r"\}\);",
        re.DOTALL,
    )
    appstate_replacement = """class AppState {
  AppState({
    this.level = 1,
    this.exp = 0,
    this.streak = 0,
    this.totalCompleted = 0,
    this.lateCompleted = 0,
    this.deadlineFailed = 0,
    List<Quest>? quests,
    List<String>? alertedReminderKeys,
    List<String>? penalizedQuestIds,
    List<String>? unlockedAchievementIds,
  })  : quests = List<Quest>.from(quests ?? const <Quest>[]),
        alertedReminderKeys = List<String>.from(alertedReminderKeys ?? const <String>[]),
        penalizedQuestIds = List<String>.from(penalizedQuestIds ?? const <String>[]),
        unlockedAchievementIds = List<String>.from(unlockedAchievementIds ?? const <String>[]);"""
    text, state_count = appstate_pattern.subn(appstate_replacement, text, count=1)
    if state_count == 0:
        raise SystemExit(
            'Could not patch AppState constructor automatically. '
            'Please send me your lib/src/models.dart and I will patch it exactly.'
        )

# 4) Make the JSON loader extra safe too, in case any old saved data returns a fixed list.
text = text.replace(
    "quests: ((json['quests'] as List?) ?? const <dynamic>[])\n            .whereType<Map>()\n            .map((e) => Quest.fromJson(Map<String, dynamic>.from(e)))\n            .toList(),",
    "quests: List<Quest>.from(((json['quests'] as List?) ?? const <dynamic>[])\n            .whereType<Map>()\n            .map((e) => Quest.fromJson(Map<String, dynamic>.from(e)))),",
)
text = text.replace(
    "alertedReminderKeys: ((json['alertedReminderKeys'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),",
    "alertedReminderKeys: List<String>.from(((json['alertedReminderKeys'] as List?) ?? const <dynamic>[]).map((e) => e.toString())),",
)
text = text.replace(
    "penalizedQuestIds: ((json['penalizedQuestIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),",
    "penalizedQuestIds: List<String>.from(((json['penalizedQuestIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString())),",
)
text = text.replace(
    "unlockedAchievementIds: ((json['unlockedAchievementIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),",
    "unlockedAchievementIds: List<String>.from(((json['unlockedAchievementIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString())),",
)

if text == original:
    print('No changes were needed. Your models.dart already looks patched.')
else:
    MODELS.write_text(text, encoding='utf-8')
    print('Patched lib/src/models.dart')
    print(f'Backup saved as: {backup}')

print('\nNow run:')
print('flutter clean')
print('flutter pub get')
print('flutter run')
print('\nImportant: do a full restart, not only hot reload.')
